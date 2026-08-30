# Happ profile exporter

[Русский](README.ru.md) | [简体中文](README.zh-CN.md)

This utility exports all Happ profiles stored locally in `subs.db` to JSON. The output includes Xray `outbounds` for every detected protocol, including VLESS, VMess, Trojan, Shadowsocks, and Hysteria.

## Run

1. Install Python 3.10 or later.
2. Install the dependency once:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Double-click `export-happ.cmd`, or run:

   ```powershell
   python happ_exporter.py --output "D:\backup\happ-profiles-export.json"
   ```

When started through `export-happ.cmd`, `happ-profiles-export.json` is created beside the script. Use `--output` to save it elsewhere.

## Export for XKeen

Create an `04_outbounds.json` ready for XKeen's Xray configuration directory:

```powershell
python happ_exporter.py --format xkeen --output "D:\backup\04_outbounds.json"
```

This mode copies all proxy outbounds, replaces duplicate Happ tags with unique ones such as `happ-vless-001`, and adds one shared `direct` and `block` outbound. Use the required generated tag in your routing rules.

## Custom database path

```powershell
python happ_exporter.py --database "C:\Users\<username>\AppData\Local\Happ\subs.db" --output "D:\backup\happ.json"
```

The database is opened read-only. The export includes passwords, UUIDs, and other connection secrets: treat the JSON file as confidential.
