@echo off
title Probar agente e impresora POS-58
cd /d "%~dp0"
echo.
echo 1) Consultando el agente local...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $e = Invoke-RestMethod 'http://127.0.0.1:9110/estado' -TimeoutSec 3; Write-Host ('   Agente OK (v' + $e.version + '). Impresora: ' + $e.impresora) -ForegroundColor Green; Write-Host ('   Detectadas: ' + ($e.impresoras -join ', ')); Write-Host ''; Write-Host '2) Enviando ticket de prueba...'; $r = Invoke-RestMethod 'http://127.0.0.1:9110/probar' -Headers @{ 'X-Agente' = 'inspectoria' } -TimeoutSec 20; if ($r.ok) { Write-Host '   Ticket de prueba enviado.' -ForegroundColor Green } else { Write-Host ('   Error: ' + $r.error) -ForegroundColor Red } } catch { Write-Host '   El agente no esta corriendo. Ejecuta INICIAR.bat primero.' -ForegroundColor Red }"
echo.
pause
