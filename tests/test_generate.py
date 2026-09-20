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
        self.assertNotIn("nft -f", content)

    def test_pbr_loader_captures_complete_nft_commands(self) -> None:
        networks = "\n".join(
            [f"10.{index}.0.0/24" for index in range(256)]
            + [f"11.{index}.0.0/24" for index in range(44)]
        )
        ipv4, ipv6 = parse_networks(f"{networks}\n2001:db8::/48\n")
        content = render(ipv4, ipv6, "fixture.txt", "wan4837")
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            script = root / "pbr.user.geoip-cn"
            capture = root / "pbr.nft"
            harness = root / "load.sh"
            script.write_text(content, encoding="utf-8")
            harness.write_text(
                "NFT_CAPTURE=$1\n"
                "nft() { printf '%s\\n' \"$*\" >> \"$NFT_CAPTURE\"; }\n"
                "uci() { printf '1\\n'; }\n"
                f". {script}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["sh", str(harness), str(capture)],
                capture_output=True,
                text=True,
                check=False,
            )
            captured = capture.read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("-f -", captured)
        self.assertIn(
            "add element inet fw4 pbr_wan4837_4_dst_ip_user", captured
        )
        self.assertIn(
            "add element inet fw4 pbr_wan4837_6_dst_ip_user", captured
        )
        self.assertEqual(captured.count("pbr_wan4837_4_dst_ip_user"), 2)


if __name__ == "__main__":
    unittest.main()
