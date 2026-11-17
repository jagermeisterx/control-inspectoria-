@echo off
title Detener agente POS-58
echo Deteniendo el agente de impresion...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":9110" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%p >nul 2>&1
)
echo Listo.
timeout /t 2 >nul
