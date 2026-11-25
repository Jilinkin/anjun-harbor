# Harbor 家庭局域网影视库（V1.0 RC1）

可选功能，不需要 GitHub 托管媒体。只使用你有权访问、播放的本地文件。Mac mini 可将群晖共享文件夹挂载为本地路径。请选择专用影视目录，不要选择整个 NAS 或用户主目录。

支持 MP4、M4V、MKV、WEBM、MOV 文件。一级目录作为仓库，文件名作为影视名，不自动刮削。启动时建立索引，新增文件需重启扫描。不转码，电视端必须支持文件编码。跳转使用单段 HTTP Range。

下载仓库源码，进入目录，Python 3.9+。本机测试：

    python3 scripts/local_library.py --media-root "/Volumes/Media"

电视测试：以 Mac 实际的局域网 IP 代替示例 192.168.1.100：

    python3 scripts/local_library.py --media-root "/Volumes/Media" --host 192.168.1.100 --allow-lan

将终端打印的完整订阅 URL 导入电视。每次启动生成新的随机访问路径；请勿上传该地址到 GitHub。仅在可信家庭网络使用，HTTP 无加密，不具备用户级认证；不要公网映射。关闭终端或 Ctrl+C 停止。服务不写入原文件、不执行脚本、不向外发送媒体清单。未在真实 Mac/NAS/TV 上测试。不要在其他用户可写的不可信目录上运行。

验收：导入多仓、显示文件名、搜索关键词、播放 MP4、进度跳转、关闭服务后无法访问。实际结果待填写。若客户端拒绝局域网 HTTP 或随机路径，记录客户端及版本。
