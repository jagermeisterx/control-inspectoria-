' Arranca el agente sin mostrar la ventana de PowerShell.
' Se usa desde INSTALAR_ARRANQUE.bat al iniciar sesion en Windows.
Dim sh, fso, carpeta
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = carpeta
sh.Run "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & carpeta & "\agente_impresion.ps1""", 0, False
