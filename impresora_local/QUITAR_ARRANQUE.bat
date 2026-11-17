@echo off
title Quitar agente POS-58 del inicio de Windows
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "quitar_arranque.ps1"
echo.
pause
