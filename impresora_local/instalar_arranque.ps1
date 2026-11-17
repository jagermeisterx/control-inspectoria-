# Crea un acceso directo al agente en la carpeta de Inicio de Windows.
$carpeta = Split-Path -Parent $MyInvocation.MyCommand.Path
$inicio = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$destino = Join-Path $inicio "Agente Impresion POS.lnk"

$ws = New-Object -ComObject WScript.Shell
$acceso = $ws.CreateShortcut($destino)
$acceso.TargetPath = "wscript.exe"
$acceso.Arguments = '//B "' + (Join-Path $carpeta "iniciar_oculto.vbs") + '"'
$acceso.WorkingDirectory = $carpeta
$acceso.Description = "Agente local de impresion POS-58 (Inspectoria)"
$acceso.Save()

Write-Host ""
Write-Host "Listo. El agente se iniciara solo al entrar a Windows." -ForegroundColor Green
Write-Host "Acceso creado en:"
Write-Host "  $destino"
