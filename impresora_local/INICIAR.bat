@echo off
title Agente de impresion POS-58 - Inspectoria
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "agente_impresion.ps1"
echo.
echo El agente se detuvo. Revisa agente.log si hay errores.
pause
