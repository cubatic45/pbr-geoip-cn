import ipaddress
import pathlib
import subprocess
import tempfile
import unittest

from scripts.generate import parse_networks, render


class GenerateTests(unittest.TestCase):
    def test_parse_deduplicates_sorts_and_collapses(self) -> None:
        ipv4, ipv6 = parse_networks(
            "2001:db8::/48\n10.0.1.0/24\n10.0.0.0/24\n10.0.0.0/24\n"
        )
        self.assertEqual(ipv4, [ipaddress.ip_network("10.0.0.0/23")])
        self.assertEqual(ipv6, [ipaddress.ip_network("2001:db8::/48")])

    def test_invalid_cidr_reports_line(self) -> None:
        with self.assertRaisesRegex(ValueError, "line 2"):
            parse_networks("10.0.0.0/8\nnot-a-network\n")

    def test_rendered_shell_has_valid_syntax(self) -> None:
        ipv4, ipv6 = parse_networks("1.0.1.0/24\n240e::/20\n")
        content = render(ipv4, ipv6, "fixture.txt", "wan")
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "pbr.user.geoip-cn"
            output.write_text(content, encoding="utf-8")
            result = subprocess.run(
                ["sh", "-n", str(output)], capture_output=True, text=True, check=False
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pbr_${TARGET_INTERFACE}_4_dst_ip_user", content)
        self.assertIn("pbr_${TARGET_INTERFACE}_6_dst_ip_user", content)


if __name__ == "__main__":
    unittest.main()
