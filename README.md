# GeoIP CN rules for OpenWrt PBR

每天自动把 [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) 的中国大陆
IPv4/IPv6 CIDR 列表转换成 OpenWrt [`pbr`](https://docs.openwrt.melmac.net/pbr/)
自定义用户脚本。

## 使用

默认产物按本仓库作者的 OpenWrt 配置，把中国大陆目标地址路由到 `wan9929`。下载脚本：

```sh
mkdir -p /etc/pbr.d
wget -O /etc/pbr.d/pbr.user.geoip-cn \
  https://raw.githubusercontent.com/cubatic45/pbr-geoip-cn/main/src/pbr.user.geoip-cn
chmod 755 /etc/pbr.d/pbr.user.geoip-cn
/etc/init.d/pbr restart
```

`pbr` 1.1.8 会自动处理 `/etc/pbr.d/` 内的文件。旧版本可以在 LuCI 的“自定义用户文件”中
添加该文件，或写入 `/etc/config/pbr`：

```text
config include
        option path '/etc/pbr.d/pbr.user.geoip-cn'
        option enabled '1'
```

若你的目标接口不是 `wan9929`，必须修改产物开头的 `TARGET_INTERFACE`，而且接口名必须与
`/etc/config/network` 和 PBR 状态中显示的逻辑接口名完全一致。例如路由到 `wan4837`：

```sh
sed -i "s/TARGET_INTERFACE='wan9929'/TARGET_INTERFACE='wan4837'/" \
  /etc/pbr.d/pbr.user.geoip-cn
/etc/init.d/pbr restart
```

也可以直接生成对应接口的版本：

```sh
python3 scripts/generate.py --target-interface wg0
```

接口名是 OpenWrt 逻辑接口名，并且必须是 `pbr` 已支持的接口。IPv6 规则仅在
`pbr.config.ipv6_enabled=1` 时加载。

生成的脚本通过 PBR 提供的 `nft()` 函数将分块后的规则写入原子 nft 文件，兼容 PBR
1.2.2 的 fw4 nft file mode。不要把脚本中的调用改成 `nft -f`，否则 PBR 加载自定义文件时
会在 `/var/run/pbr.nft` 中写入无效参数。

## 自动更新

GitHub Actions 每天 07:17（北京时间）运行，也支持在 Actions 页面手动触发。工作流只有在
上游 CIDR 发生变化时才提交。生成器会完成 CIDR 语法校验、去重、相邻网段合并，并在上游
数据量异常减少时拒绝覆盖已有产物。

本地复现：

```sh
python3 scripts/generate.py
python3 -m unittest discover -s tests -v
sh -n src/pbr.user.geoip-cn
```

## 数据来源与致谢

- PBR 用户脚本结构参考 [fernvenue/pbr-rules-collection](https://github.com/fernvenue/pbr-rules-collection)。
- CIDR 数据来自 [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) 的 `release/text/cn.txt`。

生成的 IP 归属仅与上游数据同样准确，请在使用前自行评估路由影响。

## License

[MIT](LICENSE)
