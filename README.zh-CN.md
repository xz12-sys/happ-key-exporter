# Happ 配置导出工具

[Русский](README.ru.md) | [English](README.md)

此工具会将本机 Happ 的 `subs.db` 中保存的所有配置导出为 JSON。导出内容包含检测到的所有协议的 Xray `outbounds`，包括 VLESS、VMess、Trojan、Shadowsocks 和 Hysteria。

## 运行方法

1. 安装 Python 3.10 或更高版本。
2. 首次运行前安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. 双击 `export-happ.cmd`，或执行：

   ```powershell
   python happ_exporter.py --output "D:\backup\happ-profiles-export.json"
   ```

通过 `export-happ.cmd` 启动时，`happ-profiles-export.json` 会生成在脚本所在目录。使用 `--output` 可以指定其他保存位置。

## 导出为 XKeen 格式

生成可直接用于 XKeen Xray 配置目录的 `04_outbounds.json`：

```powershell
python happ_exporter.py --format xkeen --output "D:\backup\04_outbounds.json"
```

该模式会复制所有代理 outbound，将重复的 Happ 标签替换为唯一标签（例如 `happ-vless-001`），并额外添加一个共用的 `direct` 和 `block` outbound。请在路由规则中使用生成的对应标签。

## 指定数据库文件

```powershell
python happ_exporter.py --database "C:\Users\<username>\AppData\Local\Happ\subs.db" --output "D:\backup\happ.json"
```

工具仅以只读方式打开数据库。导出的 JSON 包含密码、UUID 和其他连接密钥，请将其视为机密文件妥善保管。
