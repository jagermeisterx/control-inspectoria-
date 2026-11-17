# Impresión directa POS-58 (agente local)

Este pequeño programa se ejecuta en el PC que tiene la impresora y recibe los
tickets desde la web. Los manda **directo al cabezal en ESC/POS**, sin pasar
por el diálogo de impresión del navegador. Eso elimina:

- el espacio en blanco enorme al inicio y al final,
- el ticket impreso más chico o descuadrado (el navegador lo escalaba),
- las páginas de largo fijo usadas por el driver.

No hay que instalar Python, Node ni nada extra: usa solo Windows PowerShell,
que ya viene con Windows 10/11.

## Instalación (una sola vez)

1. Copia esta carpeta **`impresora_local`** completa a un lugar fijo del PC,
   por ejemplo `C:\Inspectoria\impresora_local`.
   (No la dejes dentro de un ZIP ni en Descargas.)
2. Verifica que la POS-58 esté instalada y que imprima la página de prueba de
   Windows.
3. Abre **`INICIAR.bat`** con doble clic. Debe decir:
   `Agente listo en http://127.0.0.1:9110/` y mostrar el nombre de la impresora.
4. Con el agente corriendo, abre **`PROBAR.bat`** y confirma que sale un ticket
   de prueba por la POS. Si sale bien, ya está operativo.
5. Para que arranque solo al encender el PC, ejecuta **`INSTALAR_ARRANQUE.bat`**
   una vez. Desde ese momento no hay que abrir nada a mano.

> La ventana de `INICIAR.bat` debe quedar abierta mientras se imprime si no
> instalaste el arranque automático. También puedes cerrarla: al abrir la web,
> si el agente no está activo, se usará el diálogo del navegador como respaldo.

## Si el nombre de la impresora no se detecta

Abre PowerShell y ejecuta:

```powershell
Get-Printer | Select-Object Name, Default
```

Copia el nombre exacto en `config.json`, por ejemplo:

```json
{
  "puerto": 9110,
  "impresora": "POS-58 Printer",
  "origenes": ["https://*.onrender.com", "http://localhost:8000"]
}
```

Luego cierra y vuelve a abrir `INICIAR.bat`. Si `"impresora": ""` queda vacío,
el agente busca uno que contenga `POS`, `58`, `thermal`, `receipt` o `ticket`;
si no encuentra, usa la predeterminada de Windows.

## Cómo saber si está funcionando

- `PROBAR.bat` imprime un ticket de prueba y muestra la impresora usada.
- En el navegador, el aviso de la pestaña del pase dice
  `Imprimiendo en POS-58…` y la pestaña se cierra sola.
- Si el agente no responde, la pestaña avisa
  `Agente local no detectado` y abre el diálogo normal del navegador.
- Los eventos quedan en `agente.log` (misma carpeta).

## Problemas frecuentes

| Síntoma | Qué revisar |
| --- | --- |
| `El agente no esta corriendo` | Abre `INICIAR.bat` y revisa `agente.log`. |
| `No se pudo iniciar el puerto 9110` | Otra copia del agente está abierta (usa `DETENER.bat`) o cambia `puerto` en `config.json`. |
| `Windows no pudo escribir…` | El nombre de la impresora en `config.json` no coincide. |
| El ticket sale corrido a la derecha o con margen izquierdo grande | Ejecuta `PROBAR.bat`: imprime una regla de 32 columnas con bordes `\|`. Si la regla sale completa pero el ticket no, actualiza la app en el servidor (el ticket ya ancla cada línea al borde izquierdo). Si la regla también sale corrida o sin el borde derecho, revisa el modo 58/80 mm del firmware y la guía física del papel. |
| El ticket sale cortado a los lados | La impresora no es de 58 mm o el logo/ticket está configurado para otro ancho. Avisa para ajustarlo. |
| La web nunca detecta el agente | Confirma que abres la web desde el mismo PC y que el dominio está en `origenes` de `config.json`. |

## Seguridad

El agente escucha únicamente en `127.0.0.1` (no es accesible desde la red) y
solo acepta pedidos de los dominios listados en `origenes`. No imprime nada
que venga de otro sitio web.

## Archivos

- `agente_impresion.ps1`: el agente (HTTP local + impresión RAW).
- `config.json`: puerto, impresora y dominios permitidos.
- `INICIAR.bat` / `DETENER.bat`: iniciar y detener.
- `PROBAR.bat`: estado + ticket de prueba.
- `INSTALAR_ARRANQUE.bat` / `QUITAR_ARRANQUE.bat`: inicio automático.
- `agente.log`: registro de actividad (se crea solo).
