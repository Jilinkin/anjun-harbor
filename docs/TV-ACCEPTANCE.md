# 电视端验收 · V0.9

## 免部署：静态多仓

导入 https://raw.githubusercontent.com/Jilinkin/anjun-harbor/main/smoke.json 。应显示开放动画、开放科幻两仓。若客户端不支持多仓，分别导入 smoke/animation.json 与 smoke/scifi.json 的 raw 地址。静态文件不会按查询参数过滤，因此不测试真实搜索；搜索已关闭。部分客户端不支持此种静态 CMS 响应。

## 局域网：真实 CMS 查询

在 Mac mini 下载仓库源码并解压，进入目录。Python 3.9+：

```sh
python3 scripts/smoke_server.py
```

默认仅 Mac 本机可访问。电视与 Mac 在同一局域网时，在 macOS 系统设置 > 网络查看 Mac 的局域网 IPv4 地址，再以该实际地址启动。例如（示例 IP，必须替换）：

```sh
python3 scripts/smoke_server.py --host 192.168.1.100 --port 8899
```

电视导入终端打印的地址。不要做路由器公网端口映射。服务仅提供两个授权测试影片的元数据，不转发视频；退出时 Ctrl+C。

## 记录

| 验收项 | 预期 | 实机结果 |
|---|---|---|
| 多仓导入 | 显示两仓 | 待测 |
| 切换仓库 | 影片对应变化 | 待测 |
| 分类与详情 | 正确展示 | 待测 |
| 搜索（仅 LAN） | Bunny 有结果；无关词无结果 | 待测 |
| 播放 | 播放 CC BY 3.0 短片 | 待测 |
| 暂停、进度跳转 | 正常 | 待测 |
| 正式订阅 | 不受测试影响 | 待测 |

记录客户端名称、版本、网络、失败步骤及截图。外部媒体地址未做真实播放验证；Google 样片在国内网络可能不可达。正式订阅和 test.json 候选通道均未改变。仅完成协议样例与自动化测试不代表 V1.0 可用。
