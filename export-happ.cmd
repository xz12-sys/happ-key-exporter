@echo off
setlocal
cd /d "%~dp0"
python happ_exporter.py
if errorlevel 1 pause
