# Quita el agente del inicio automatico de Windows.
$inicio = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$destino = Join-Path $inicio "Agente Impresion POS.lnk"
if (Test-Path $destino) {
    Remove-Item $destino -Force
    Write-Host "Acceso de inicio eliminado." -ForegroundColor Green
} else {
    Write-Host "No habia acceso de inicio instalado."
}
