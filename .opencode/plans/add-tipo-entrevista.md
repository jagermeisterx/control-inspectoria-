# Plan: nuevo tipo de acción "Entrevista" en Acciones Disciplinarias

## Contexto verificado
Los tipos de acción **no** son una tabla de BD: son una lista hardcodeada `AccionDisciplinaria.TIPOS` en `core/models.py:236`. El campo `tipo` es `CharField(max_length=20, choices=TIPOS, default="LLAMADA")` sobre la columna `core_acciondisciplinaria.tipo` (`varchar(20)`, sin CHECK constraint ni enum nativo).

El selector de la UI es un `<select>` Bootstrap (`core/forms.py:163`, renderizado en `templates/core/acciones_disciplinarias.html:26`). El badge de la tabla se colorea con `badge-{{ r.tipo|lower }}` → la clase CSS se deriva del valor guardado.

**Decisiones confirmadas:** orden por gravedad `LLAMADA → ENTREVISTA → SUSPENSION`; badge verde (`--success`); actualizar toda la documentación de ayuda.

## Cambios

### 1. `core/models.py:236-239` — agregar el tipo
```python
TIPOS = [
    ("LLAMADA", "Llamada a apoderado"),
    ("ENTREVISTA", "Entrevista"),
    ("SUSPENSION", "Suspensión"),
]
```
`ENTREVISTA` = 9 chars, cabe en `max_length=20`. **El default sigue siendo `LLAMADA`** (no se toca `models.py:241`).

### 2. `core/migrations/0010_acciondisciplinaria_tipo_entrevista.py` — nueva migración
`AlterField` sobre `acciondisciplinaria.tipo` con la lista **completa y en el orden nuevo**, `depends = [("core", "0009_unaccent")]`.

Es cambio solo de metadatos: mismo `max_length`, sin tipo nativo → Django no emite DDL, **no toca datos existentes**. No hace falta migración de datos.

### 3. `static/css/style.css` (después de línea 550) — estilo del badge
```css
.badge-entrevista { background: var(--success); color: #fff; }
```
Sin esto el badge sale sin fondo en el listado y en `reporte_alumno.html`.

### 4. Textos que enumeran hoy solo los 2 tipos (6 lugares)
- `templates/core/ayuda_director.html:27` y `templates/core/ayuda_inspector_general.html:77` → "Selecciona el tipo: llamada a apoderado, entrevista o suspensión"
- `docs/manual/director.md:25` → *Llamada a apoderado*, *Entrevista* o *Suspensión*
- `docs/manual/inspector_general.md:63` → ídem
- `docs/manual/inspector.md:17` → "llamada a apoderado / entrevista / suspensión"
- `core/views.py:919` → comentario `# ── Acciones disciplinarias (llamada a apoderado / entrevista / suspensión) ──`

## Fuera de alcance (se adaptan solos)
`core/forms.py`, `acciones_disciplinarias.html`, `core/admin.py` (37-41), `core/pdf_generator.py:637`, `core/views.py:1093` (Excel) y `reporte_alumno.html:140` ya iteran desde `choices` / `get_tipo_display()`. No requieren cambios.

## Verificación
1. `python manage.py makemigrations --check --dry-run` → sin cambios pendientes (confirma que la migración cubre el modelo).
2. `python manage.py migrate` + `python manage.py check`.
3. Script end-to-end: registrar 3 acciones (una de cada tipo) vía `_list_create` → el desplegable ofrece los 3 en orden, y el listado devuelve `badge-entrevista` con fondo verde.
4. Verificar los 4 consumidores con una fila `ENTREVISTA`: HTML del informe del alumno, PDF, Excel y el contador de los dashboards.
5. Confirmar que las filas `LLAMADA` / `SUSPENSION` existentes siguen intactas y con su badge original.