# Agente local de impresion ESC/POS - Inspectoria General
#
# Escucha SOLO en 127.0.0.1 y manda los tickets que entrega la web
# directo al cabezal de la POS-58 con el tipo de datos RAW de Windows.
# No usa el driver para "renderizar" la pagina: no hay escala, margenes del
# sistema ni avance de una hoja completa. Eso elimina el blanco inicial/final
# y el descuadre del dialogo del navegador.
#
# Uso:  INICIAR.bat   (o este archivo con PowerShell)
# Configuracion: config.json

$ErrorActionPreference = "Stop"

$script:Base = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:LogPath = Join-Path $script:Base "agente.log"
$script:Cfg = @{
    puerto    = 9110
    impresora = ""
    origenes  = @(
        "https://*.onrender.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    )
}

function Escribir-Log {
    param([string]$Mensaje)
    $linea = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Mensaje
    Write-Host $linea
    try { Add-Content -Path $script:LogPath -Value $linea -Encoding UTF8 } catch { }
}

function Cargar-Config {
    $ruta = Join-Path $script:Base "config.json"
    if (-not (Test-Path $ruta)) {
        Escribir-Log "No existe config.json; se usan valores por defecto."
        return
    }
    try {
        $leido = Get-Content -Path $ruta -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $leido.puerto) { $script:Cfg.puerto = [int]$leido.puerto }
        if ($null -ne $leido.impresora) { $script:Cfg.impresora = [string]$leido.impresora }
        if ($null -ne $leido.origenes) { $script:Cfg.origenes = @($leido.origenes) }
    } catch {
        Escribir-Log "config.json invalido: $($_.Exception.Message)"
    }
}

# --- Impresion RAW con la API de Windows (sin dependencias) -----------------
function Cargar-WinSpool {
    if ("RawPrinter" -as [type]) { return }
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class RawPrinter
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public class DOCINFOA
    {
        [MarshalAs(UnmanagedType.LPWStr)] public string pDocName;
        [MarshalAs(UnmanagedType.LPWStr)] public string pOutputFile;
        [MarshalAs(UnmanagedType.LPWStr)] public string pDataType;
    }

    [DllImport("winspool.Drv", EntryPoint = "OpenPrinterW", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool OpenPrinter(string src, out IntPtr hPrinter, IntPtr pd);

    [DllImport("winspool.Drv", EntryPoint = "ClosePrinter", SetLastError = true)]
    public static extern bool ClosePrinter(IntPtr hPrinter);

    [DllImport("winspool.Drv", EntryPoint = "StartDocPrinterW", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern int StartDocPrinter(IntPtr hPrinter, int level,
        [In, MarshalAs(UnmanagedType.LPStruct)] DOCINFOA di);

    [DllImport("winspool.Drv", EntryPoint = "EndDocPrinter", SetLastError = true)]
    public static extern bool EndDocPrinter(IntPtr hPrinter);

    [DllImport("winspool.Drv", EntryPoint = "StartPagePrinter", SetLastError = true)]
    public static extern bool StartPagePrinter(IntPtr hPrinter);

    [DllImport("winspool.Drv", EntryPoint = "EndPagePrinter", SetLastError = true)]
    public static extern bool EndPagePrinter(IntPtr hPrinter);

    [DllImport("winspool.Drv", EntryPoint = "WritePrinter", SetLastError = true)]
    public static extern bool WritePrinter(IntPtr hPrinter, IntPtr pBytes, int dwCount, out int dwWritten);

    // Devuelve 0 si todo salio bien; si no, el codigo Win32 del error.
    public static int SendBytes(string printer, byte[] bytes)
    {
        IntPtr hPrinter;
        if (!OpenPrinter(printer, out hPrinter, IntPtr.Zero)) return Marshal.GetLastWin32Error();

        int err = 0;
        DOCINFOA di = new DOCINFOA();
        di.pDocName = "Inspectoria - pase";
        di.pDataType = "RAW";

        if (StartDocPrinter(hPrinter, 1, di) == 0)
        {
            err = Marshal.GetLastWin32Error();
            ClosePrinter(hPrinter);
            return err;
        }

        if (!StartPagePrinter(hPrinter))
        {
            err = Marshal.GetLastWin32Error();
        }
        else
        {
            IntPtr puntero = Marshal.AllocCoTaskMem(bytes.Length);
            try
            {
                Marshal.Copy(bytes, 0, puntero, bytes.Length);
                int escrito;
                if (!WritePrinter(hPrinter, puntero, bytes.Length, out escrito))
                {
                    err = Marshal.GetLastWin32Error();
                }
                else if (escrito != bytes.Length)
                {
                    err = -1;
                }
            }
            finally
            {
                Marshal.FreeCoTaskMem(puntero);
            }
            EndPagePrinter(hPrinter);
        }

        EndDocPrinter(hPrinter);
        ClosePrinter(hPrinter);
        return err;
    }
}
"@
}

function Obtener-Impresoras {
    try {
        return @(Get-Printer | Select-Object -ExpandProperty Name)
    } catch {
        try {
            Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue
            return @([System.Drawing.Printing.PrinterSettings]::InstalledPrinters | ForEach-Object { $_ })
        } catch {
            return @()
        }
    }
}

function Obtener-Predeterminada {
    try {
        $def = Get-CimInstance Win32_Printer -Filter "Default = TRUE" -ErrorAction Stop |
            Select-Object -First 1
        if ($def) { return [string]$def.Name }
    } catch { }
    return ""
}

function Elegir-Impresora {
    if ($script:Cfg.impresora) { return [string]$script:Cfg.impresora }

    $virtuales = "Microsoft Print to PDF|Microsoft XPS|OneNote|Fax"
    $todas = @(Obtener-Impresoras | Where-Object { $_ -notmatch $virtuales })

    # Nombre tipico: "POS-58", "POS58 Printer", "58mm Series", "Thermal"...
    foreach ($nombre in $todas) {
        if ($nombre -match "POS|58|thermal|termic|receipt|ticket") { return $nombre }
    }
    $def = Obtener-Predeterminada
    if ($def -and $def -notmatch $virtuales) { return $def }
    return ($todas | Select-Object -First 1)
}

function Enviar-Raw {
    param([string]$Impresora, [byte[]]$Datos)
    if (-not $Impresora) { throw "No hay impresora configurada ni predeterminada." }
    Cargar-WinSpool
    $codigo = [RawPrinter]::SendBytes($Impresora, $Datos)
    if ($codigo -ne 0) {
        throw "Windows no pudo escribir en '$Impresora' (Win32 $codigo). Revisa el nombre en config.json."
    }
}

# --- HTTP minimo sobre TCP (funciona sin permisos de administrador) ---------
function Origen-Permitido {
    param([string]$Origen)
    if ([string]::IsNullOrWhiteSpace($Origen)) { return $true }  # curl / prueba local
    foreach ($patron in $script:Cfg.origenes) {
        if ($patron -eq "*") { return $true }
        if ($Origen -like $patron) { return $true }
    }
    return $false
}

function Enviar-Respuesta {
    param(
        [System.IO.Stream]$Stream,
        [int]$Codigo,
        [string]$Origen,
        [byte[]]$Cuerpo = @(),
        [string]$Tipo = "application/json; charset=utf-8"
    )
    $motivos = @{
        "200" = "OK"; "204" = "No Content"; "400" = "Bad Request"; "403" = "Forbidden"
        "404" = "Not Found"; "405" = "Method Not Allowed"; "500" = "Internal Server Error"
    }
    if ([string]::IsNullOrWhiteSpace($Origen)) { $Origen = "*" }
    $estado = $motivos["$Codigo"]
    if (-not $estado) { $estado = "OK" }

    $cabeceras = @(
        "HTTP/1.1 $Codigo $estado"
        "Content-Type: $Tipo"
        "Content-Length: $($Cuerpo.Length)"
        "Connection: close"
        "Cache-Control: no-store"
        "Access-Control-Allow-Origin: $Origen"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS"
        "Access-Control-Allow-Headers: Content-Type, X-Agente"
        "Access-Control-Allow-Private-Network: true"
        "Access-Control-Max-Age: 600"
        "Vary: Origin"
    )
    $bytes = [System.Text.Encoding]::ASCII.GetBytes(($cabeceras -join "`r`n") + "`r`n`r`n")
    try {
        $Stream.Write($bytes, 0, $bytes.Length)
        if ($Cuerpo.Length -gt 0) { $Stream.Write($Cuerpo, 0, $Cuerpo.Length) }
        $Stream.Flush()
    } catch { }
}

function Responder-Json {
    param($Peticion, $Objeto, [int]$Codigo = 200)
    $json = $Objeto | ConvertTo-Json -Compress -Depth 5
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    Enviar-Respuesta $Peticion.Stream $Codigo $Peticion.Origen $bytes
}

function Leer-Peticion {
    param($Cliente)
    $stream = $Cliente.GetStream()
    $stream.ReadTimeout = 5000
    $buffer = New-Object byte[] 16384
    $memoria = New-Object System.IO.MemoryStream
    $texto = ""

    while ($true) {
        $leidos = $stream.Read($buffer, 0, $buffer.Length)
        if ($leidos -le 0) { break }
        $memoria.Write($buffer, 0, $leidos)
        $texto = [System.Text.Encoding]::ASCII.GetString($memoria.ToArray())
        if ($texto.Contains("`r`n`r`n")) { break }
        if ($memoria.Length -gt 65536) { break }
    }

    $pos = $texto.IndexOf("`r`n`r`n")
    if ($pos -lt 0) { throw "Peticion HTTP invalida." }

    $cabecera = $texto.Substring(0, $pos)
    $cuerpo = $texto.Substring($pos + 4)
    $lineas = $cabecera -split "`r`n"
    $partes = $lineas[0] -split " "
    $metodo = $partes[0].ToUpperInvariant()
    $url = "http://127.0.0.1" + $partes[1]
    $ruta = ([uri]$url).AbsolutePath

    $encabezados = @{}
    for ($i = 1; $i -lt $lineas.Count; $i++) {
        $j = $lineas[$i].IndexOf(":")
        if ($j -gt 0) {
            $clave = $lineas[$i].Substring(0, $j).Trim().ToLowerInvariant()
            $encabezados[$clave] = $lineas[$i].Substring($j + 1).Trim()
        }
    }

    $largo = 0
    if ($encabezados.ContainsKey("content-length")) {
        $largo = [int]$encabezados["content-length"]
    }
    while ($cuerpo.Length -lt $largo) {
        $leidos = $stream.Read($buffer, 0, $buffer.Length)
        if ($leidos -le 0) { break }
        $cuerpo += [System.Text.Encoding]::ASCII.GetString($buffer, 0, $leidos)
    }
    if ($largo -gt 0 -and $cuerpo.Length -gt $largo) {
        $cuerpo = $cuerpo.Substring(0, $largo)
    }

    $origen = ""
    if ($encabezados.ContainsKey("origin")) { $origen = [string]$encabezados["origin"] }
    $agente = ""
    if ($encabezados.ContainsKey("x-agente")) { $agente = [string]$encabezados["x-agente"] }

    return [pscustomobject]@{
        Stream = $stream
        Metodo = $metodo
        Ruta   = $ruta
        Origen = $origen
        Agente = $agente
        Cuerpo = $cuerpo
    }
}

function Centrar-Pos58 {
    param([string]$Texto)
    if ($Texto.Length -ge 32) { return $Texto }
    $izquierda = [int][math]::Floor((32 - $Texto.Length) / 2)
    return $Texto.PadLeft($Texto.Length + $izquierda).PadRight(32)
}

function Ticket-Prueba {
    # Se arman bytes, no texto: al codificar en CP850 un [char]128 se
    # convierte en "?" y el ancho de área saldría mal (319 en vez de 384).
    $ESC = [byte]27
    $GS = [byte]29
    $cod = [System.Text.Encoding]::GetEncoding(850)
    $salida = [System.Collections.Generic.List[byte]]::new()

    function Agregar-Bytes([byte[]]$datos) {
        $salida.AddRange($datos)
    }

    function Agregar-Linea([string]$texto) {
        $salida.AddRange([byte[]]@($ESC, 36, 0, 0))   # ESC $ 0 0
        $salida.AddRange([byte[]]$cod.GetBytes($texto + "`n"))
    }

    Agregar-Bytes ([byte[]]@($ESC, 64))                # ESC @ reset
    Agregar-Bytes ([byte[]]@($GS, 76, 0, 0))           # GS L margen 0
    Agregar-Bytes ([byte[]]@($GS, 87, 128, 1))         # GS W 384 dots
    Agregar-Bytes ([byte[]]@($ESC, 77, 0))             # Fuente A
    Agregar-Bytes ([byte[]]@($ESC, 32, 0))             # espaciado 0
    Agregar-Bytes ([byte[]]@($ESC, 116, 2))            # CP850
    Agregar-Bytes ([byte[]]@(10))

    $regla = "|" + ("-" * 30) + "|"
    Agregar-Bytes ([byte[]]@($ESC, 69, 1))             # negrita
    Agregar-Linea (Centrar-Pos58 "INSPECTORIA GENERAL")
    Agregar-Bytes ([byte[]]@($ESC, 69, 0))
    Agregar-Linea $regla
    Agregar-Linea (Centrar-Pos58 "PRUEBA POS-58")
    Agregar-Linea $regla
    Agregar-Linea "IZQUIERDA"
    Agregar-Linea (Centrar-Pos58 "CENTRADO")
    Agregar-Linea ("DERECHA").PadLeft(32)
    Agregar-Linea $regla
    Agregar-Linea "Si los bordes | de la regla"
    Agregar-Linea "salen completos, el ancho esta"
    Agregar-Linea "bien. Si falta el borde derecho"
    Agregar-Linea "o sobra margen izquierdo, es"
    Agregar-Linea "el modo 58/80 mm del firmware"
    Agregar-Linea "o la guia fisica del papel."
    Agregar-Linea ""
    Agregar-Linea ""
    Agregar-Linea ""
    Agregar-Bytes ([byte[]]@($ESC, 100, 4))            # avance
    Agregar-Bytes ([byte[]]@($GS, 86, 0))              # corte
    return [byte[]]$salida.ToArray()
}

function Procesar-Peticion {
    param($Peticion)

    if (-not (Origen-Permitido $Peticion.Origen)) {
        Escribir-Log "Origen rechazado: $($Peticion.Origen)"
        Responder-Json $Peticion @{ ok = $false; error = "Origen no autorizado" } 403
        return
    }

    if ($Peticion.Metodo -eq "OPTIONS") {
        Enviar-Respuesta $Peticion.Stream 204 $Peticion.Origen @()
        return
    }

    $impresora = Elegir-Impresora

    # Cabecera propia: evita que un <img> o formulario de otro sitio imprima.
    if (($Peticion.Ruta -eq "/probar" -or $Peticion.Ruta -eq "/imprimir") -and
        $Peticion.Agente -ne "inspectoria") {
        Escribir-Log "Peticion sin cabecera X-Agente: $($Peticion.Ruta)"
        Responder-Json $Peticion @{ ok = $false; error = "Falta la cabecera X-Agente" } 403
        return
    }

    switch ($Peticion.Ruta) {
        "/estado" {
            Responder-Json $Peticion @{
                ok             = $true
                version        = "1.2"
                puerto         = $script:Cfg.puerto
                impresora     = $impresora
                predeterminada = (Obtener-Predeterminada)
                impresoras     = @(Obtener-Impresoras)
            }
            return
        }

        "/probar" {
            try {
                Enviar-Raw $impresora (Ticket-Prueba)
                Escribir-Log "Ticket de prueba enviado a '$impresora'."
                Responder-Json $Peticion @{ ok = $true; impresora = $impresora }
            } catch {
                Escribir-Log "ERROR prueba: $($_.Exception.Message)"
                Responder-Json $Peticion @{ ok = $false; error = $_.Exception.Message; impresora = $impresora }
            }
            return
        }

        "/imprimir" {
            if ($Peticion.Metodo -ne "POST") {
                Responder-Json $Peticion @{ ok = $false; error = "Usa POST" } 405
                return
            }
            try {
                $cuerpo = $null
                if (-not [string]::IsNullOrWhiteSpace($Peticion.Cuerpo)) {
                    $cuerpo = $Peticion.Cuerpo | ConvertFrom-Json
                }
                if ($null -eq $cuerpo -or [string]::IsNullOrWhiteSpace($cuerpo.datos_base64)) {
                    throw "Falta datos_base64 en el cuerpo."
                }
                $datos = [Convert]::FromBase64String([string]$cuerpo.datos_base64)
                if ($datos.Length -eq 0) { throw "El ticket llego vacio." }
                if ($datos.Length -gt 2MB) { throw "El ticket supera 2 MB." }

                if ($cuerpo.impresora) { $impresora = [string]$cuerpo.impresora }
                Enviar-Raw $impresora $datos
                Escribir-Log "Ticket enviado a '$impresora' ($($datos.Length) bytes)."
                Responder-Json $Peticion @{ ok = $true; impresora = $impresora; bytes = $datos.Length }
            } catch {
                Escribir-Log "ERROR impresion: $($_.Exception.Message)"
                Responder-Json $Peticion @{ ok = $false; error = $_.Exception.Message; impresora = $impresora }
            }
            return
        }

        default {
            Responder-Json $Peticion @{ ok = $false; error = "Ruta desconocida: $($Peticion.Ruta)" } 404
        }
    }
}

# --- Arranque ---------------------------------------------------------------
Cargar-Config

# Solo loopback IPv4: no queda accesible desde la red del colegio.
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, [int]$script:Cfg.puerto)
try {
    $listener.Start()
} catch {
    Escribir-Log "No se pudo abrir el puerto $($script:Cfg.puerto): $($_.Exception.Message)"
    Escribir-Log "Cierra otra copia del agente (DETENER.bat) o cambia 'puerto' en config.json."
    exit 1
}

$impresoraInicial = Elegir-Impresora
Escribir-Log "Agente listo en http://127.0.0.1:$($script:Cfg.puerto)/"
Escribir-Log "Impresora: $(if ($impresoraInicial) { $impresoraInicial } else { '(no detectada)' })"

try {
    while ($true) {
        $cliente = $listener.AcceptTcpClient()
        try {
            $peticion = Leer-Peticion $cliente
            Procesar-Peticion $peticion
        } catch {
            Escribir-Log "Error atendiendo peticion: $($_.Exception.Message)"
        } finally {
            try { $cliente.Close() } catch { }
        }
    }
} finally {
    try { $listener.Stop() } catch { }
    Escribir-Log "Agente detenido."
}
