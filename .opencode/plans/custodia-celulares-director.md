# Plan: Custodia de celulares en poder del Director

## Objetivo
El Director (y el admin) necesitan ver los celulares que los profesores requisan, saber cuántos.times se le quitó el teléfono a cada alumno, y marcar cada uno como **Entregado** al devolverlo.

## Decisiones ya tomadas
| Decisión | Valor |
|---|---|
| Ubicación | Página nueva `/celulares/dia/` enlazada desde el dashboard del director |
| Estados | 2: `EN_DIRECCION` → `ENTREGADO` |
| `retiro` | **Sacar del formulario de alta**; se marca `PENDIENTE` solo y lo resuelve el Director al entregar |
| Datos existentes | Marcar `ENTREGADO` (son históricos) |
| Director | Puede también **registrar** celulares nuevos |
| "N° veces" | Conteo **acumulado histórico** por alumno (mismo criterio que el `conteo_celulares` que ya usa `celulares.html:75`) |

**Admin:** en este proyecto `admin` = `is_superuser` (`core/roles.py:15-18`) y `tiene_rol` ya devuelve `True` para superusuarios (`roles.py:22-23`). Con `@rol_requerido(DIRECTOR)` + el filtro `tiene_rol`, el admin ve la página y puede confirmar **sin código adicional**. Se documenta explícitamente.

---

## Cambios

### 1. `core/models.py:154-183` — estado de custodia
```python
ESTADOS = [
    ("EN_DIRECCION", "En poder de la dirección"),
    ("ENTREGADO", "Entregado"),
]
```
- `estado = CharField("Estado", max_length=15, choices=ESTADOS, default="EN_DIRECCION")`
- `fecha_entrega = DateTimeField("Fecha de entrega", null=True, blank=True)`
- `entregado_por = FK(AUTH_USER_MODEL, null=True, blank=True, on_delete=SET_NULL, related_name="celulares_entregados")`
- **Cambiar** `retiro.default` de `"AL FINAL DEL DÍA"` → `"PENDIENTE"` (`models.py:169`)
- `Meta.indexes`: `Index(fields=["estado", "fecha"])` para la consulta diaria (consistente con el precedente de `0002_index_alumno_busqueda`)

### 2. `core/migrations/0011_celular_estado_entrega.py` (nueva)
`AddField` × 3 + `AlterField(retiro)` + `AddIndex`, y un `RunPython` que pone `estado="ENTREGADO"` en **todas** las filas existentes (`fecha_entrega` se queda `NULL` porque se desconoce). `dependencies = [("core", "0010_acciondisciplinaria_tipo_entrevista")]`.

> ⚠️ `0010` (Entrevista) sigue **sin commitear**. Hay que commitear ambos juntos o la cadena de migraciones queda rota.

### 3. `core/forms.py:114-129` — quitar `retiro` del alta
Sacar `"retiro"` de `CelularForm.Meta.fields` y su widget. El modelo pone `PENDIENTE` solo. Nuevo `CelularEntregaForm` (`ModelForm`, solo `retiro`) para la acción de entrega, restringido a las 2 opciones resueltas (`AL FINAL DEL DÍA`, `RETIRA APODERADO`).

### 4. `core/views.py` — vistas nuevas + permisos
- **Nueva `celulares_del_dia`**, `@rol_requerido(DIRECTOR)`. GET con `?fecha=YYYY-MM-DD` (default hoy): tabla del día + `conteo_celulares` (histórico, reutilizando el mismo `Count` que `views.py:225-227`) + contadores `pendientes`/`entregados`. Sin paginación (un día son pocas filas).
- **Nueva `entregar_celular(pk)`**, `@rol_requerido(DIRECTOR)`, solo POST → setea `estado="ENTREGADO"`, `fecha_entrega=timezone.now()`, `entregado_por=request.user`, `retiro` del form. Redirige a `celulares_del_dia` preservando la fecha.
- **`views.py:223`**: agregar `DIRECTOR` a `@rol_requerido(...)` de `celulares` para que pueda registrar y ver el historial.
- **`views.py:1373-1379`** (importador histórico): setear `estado="ENTREGADO"` explícito en el `bulk_create`, para que la carga histórica no aparezca como pendiente. **El contrato de 7 columnas del Excel no cambia** (`views.py:1458-1468`), así que la plantilla y el allowlist quedan intactos.
- **`views.py:1085-1087`**: agregar columnas `Estado` y `Fecha entrega` a la hoja "Celulares" de `exportar_excel_alumno`.
- **`dashboard_director` (`views.py:900-915`)**: agregar al contexto `celulares_hoy` con los 3 conteos del día.

### 5. `core/urls.py`
```python
path("celulares/dia/", views.celulares_del_dia, name="celulares_del_dia"),
path("celulares/<int:pk>/entregar/", views.entregar_celular, name="entregar_celular"),
```
Ambas antes de `eliminar/<str:modelo>/<int:pk>/` (`urls.py:21`) para que no las capture ese patrón.

### 6. `templates/core/celulares_dia.html` (nueva)
Tabla: `Alumno | Curso | N° veces | Lugar | Estado | Entregado por / cuándo | Acción`.
- La columna **N° veces** reutiliza `{{ conteo_celulares|get_item:r.alumno_id|default:0 }}`.
- En las filas `EN_DIRECCION`, la celda Acción trae un `<form>` inline con un `<select name="retiro">` (2 opciones) + botón **Entregar** + `confirm()`.
- Selector de fecha arriba (default hoy) + contador `X pendientes / Y entregados`.
- Sin form de alta (el Director registra en `/celulares/`).

### 7. Templates existentes
- **`celulares.html`**: quitar `<label>Retiro</label> + {{ form.retiro }}` (líneas 32-35) y sumar columna `Estado` con badge; el `colspan="8"` del `<tr>` vacío pasa a 9.
- **`dashboard_director.html`**: nueva `card-custom` "Celulares en dirección" con los 3 conteos + botón a `celulares_del_dia`.
- **`base.html:71-75`**: sumar `director` al link "Celulares" y agregar el item "Celulares del día".
- **`core/pdf_generator.py:479` y `:624`**: sumar columna `Estado` a las tablas de celulares.

### 8. `static/css/style.css` (tras línea 551)
```css
.badge-en_direccion { background: var(--warning); color: #fff; }
.badge-entregado    { background: var(--success); color: #fff; }
```

### 9. `core/admin.py:26-29`
Sumar `estado` y `fecha_entrega` a `list_display`, y `estado` a `list_filter`.

### 10. Documentación
- **`docs/manual/director.md`** + **`templates/core/ayuda_director.html`**: sección nueva del flujo diario y quién puede confirmar (Director y admin).
- **`docs/manual/profesor.md:14`** + **`ayuda_profesor.html:18`**: quitar la mención de "modalidad de retiro" del alta (ahora es automático "Pendiente") y aclarar que el Director confirma la entrega.

---

## Verificación
1. `makemigrations --check` sin pendientes + `check` 0 issues.
2. `sqlmigrate core 0011` — revisar que el `RunPython` marca las filas previas y que el índice se crea.
3. **Matriz de permisos** (superusuario / director / inspector_general / inspector / profesor): quién entra a `/celulares/dia/` y a `/celulares/`.
4. **Confirmación de entrega** como Director y como superusuario: cambia a `ENTREGADO`, guarda `fecha_entrega` + `entregado_por` + `retiro` resuelto, y el badge queda verde.
5. `retiro` al registrar: sin `PENDIENTE` automático, verificado en BD.
6. **`N° veces`**: alumno con 3 requisas históricas muestra 3 en la fila de hoy.
7. **Carga histórica**: importar un Excel con la hoja `Celulares` → las filas quedan `ENTREGADO`, no pending, sin tocar las 7 columnas.
8. Excel/PDF del alumno con una fila `EN_DIRECCION`: columna Estado presente.
9. `celulares.html` sin errores tras quitar el campo (colspan, count de columnas).

## Fuera de alcance (se puede agregar después)
- Botón "revertir" una entrega confirmada por error.
- Historial de quién registró vs quién recibió.
- Notificación automática al profesor cuando el Director entrega el teléfono.