@echo off
title Instalar agente POS-58 al iniciar Windows
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "instalar_arranque.ps1"
echo.
pause
