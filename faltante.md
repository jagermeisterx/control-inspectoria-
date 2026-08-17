# Faltantes para implementar avisos de WhatsApp (Cloud API de Meta)

## A. Credenciales de Meta — sandbox de WhatsApp Cloud API
1. **`WHATSAPP_TOKEN`** — Token de acceso. ¿Es temporal (24 h) o permanente (System User)? Pega el token completo.
2. **`WHATSAPP_PHONE_NUMBER_ID`** — ID del número de prueba (se ve en API Setup del sandbox).
3. **`WHATSAPP_BUSINESS_ACCOUNT_ID`** — ID de la cuenta WABA (opcional, para debug).
4. **`WHATSAPP_VERIFY_TOKEN`** — Tú lo inventas (ej: `colegioDemo2026`). Se usa para validar el webhook. Dime cuál usar.
5. **Allowlist** — Teléfonos de prueba autorizados (formato `+56...`, con WhatsApp instalado) para la demo. Lista 1–3 números.

## B. Templates de WhatsApp
6. ¿Creaste los templates en el sandbox? Los que propongo: `aviso_atraso`, `aviso_uniforme`, `aviso_celular`, `aviso_retiro`, `mensaje_general`. Si usaste otros nombres/cuerpos, pégame **nombre exacto + texto** de cada uno.
7. **Idioma** del template: ¿`es` (español genérico) u otro? (se define al crearlos en Meta).
8. ¿El sandbox te deja enviar templates propios o solo `hello_world`? (Si solo el de ejemplo, indico qué usamos).

## C. Entorno de la demo
9. **URL pública** de la app (ej: `https://inspectoria.onrender.com`) — la necesita el webhook. Si la demo será local (localhost), ¿usas túnel tipo ngrok o desactivamos el webhook?
10. ¿Token temporal o permanente? (Recomiendo **permanente** para que no expire el día de la reunión.)
11. Teléfono(s) de **apoderado de prueba** que deben estar en allowlist para demostrar que "le llega" el mensaje.

## D. Decisiones de configuración (responder sí/no)
12. ¿Auto-envío activo en los 4 módulos (`atrasos`, `uniformes`, `celulares`, `retiros`) o solo los 3 prioritarios por ahora?
13. ¿Ejecuto normalización de teléfonos ya guardados en la BD (comando) o solo aplica a nuevos registros?
14. ¿Agrego página **Historial de envíos** al menú lateral? ¿Visible para todos o solo superusuarios?
15. ¿Confirmas auto-marcar `Aviso apoderado` (Celular) y `¿Se llamó?` (Uniforme) cuando el WhatsApp se envía con éxito?
16. **Nombre del emisor** que verá el apoderado (ej: "Colegio X – Inspectoría"). Debe coincidir con el display name del sandbox.
