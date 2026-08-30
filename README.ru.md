# Happ profile exporter

[English](README.md) | [简体中文](README.zh-CN.md)

Утилита экспортирует все локально сохранённые профили Happ из `subs.db` в JSON. В результат попадают настройки Xray `outbounds` для всех найденных протоколов: VLESS, VMess, Trojan, Shadowsocks и Hysteria.

## Запуск

1. Установите Python 3.10+.
2. Один раз установите зависимость:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Дважды щёлкните `export-happ.cmd` или выполните:

   ```powershell
   python happ_exporter.py --output "D:\backup\happ-profiles-export.json"
   ```

При запуске через `export-happ.cmd` файл `happ-profiles-export.json` создаётся рядом со скриптом. Чтобы сохранить его в другом месте, укажите существующий путь в параметре `--output`.

## Готовый файл для XKeen

Чтобы создать `04_outbounds.json`, готовый для каталога конфигураций Xray в XKeen:

```powershell
python happ_exporter.py --format xkeen --output "D:\backup\04_outbounds.json"
```

Этот режим переносит все прокси-outbound'ы, заменяет повторяющиеся теги Happ на уникальные (`happ-vless-001`, `happ-hysteria-002` и т. п.) и добавляет по одному служебному outbound `direct` и `block`. В правилах маршрутизации указывайте тег нужного подключения из созданного файла.

## Свой файл базы

```powershell
python happ_exporter.py --database "C:\Users\<имя>\AppData\Local\Happ\subs.db" --output "D:\backup\happ.json"
```

Скрипт открывает базу только для чтения. Экспорт содержит пароли, UUID и прочие данные подключений, поэтому храните JSON как секретный файл.
