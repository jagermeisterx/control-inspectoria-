# Plan: Fix roles no asignados + verificación por rol

## Causa raíz confirmada
- En producción los grupos (`profesor`, etc.) **no existen** → al guardar un usuario con rol, `Group.objects.filter(name__in=[...])` devuelve vacío y asigna **nada sin error** (`core/forms.py::_asignar_roles`).
- Los grupos deberían crearlos `start.sh` (`crear_grupos`), pero probablemente el servicio de Render usa el Start Command del dashboard (era del Procfile) y nunca lo ejecuta.
- El superusuario/admin funciona porque ignora los grupos (`roles.py::es_admin`). Por eso solo admin ve todo y el resto "no ve nada" + manual en blanco (mensaje de sin-manual).

## Cambios

### 1. `core/forms.py` — asignación robusta (create + editar)
`_asignar_roles`: reemplazar filter/set por `Group.objects.get_or_create(name=rol)` + `user.groups.add(grupo)` por cada rol elegido. Así funciona aunque los grupos no existan aún.

### 2. Migración de datos `0004_seed_role_groups`
`RunPython` que crea los 4 grupos con `get_or_create` usando `apps.get_model("auth", "Group")`. Garantiza su existencia en cada deploy (buildCommand corre `migrate`) independientemente de start.sh. Reverse = noop (no destructivo).

### 3. Mensaje claro para usuario sin rol (`templates/core/ayuda.html`)
Cuando `secciones` esté vacío: alerta amarilla "Tu cuenta no tiene un rol asignado. Pide al administrador que te asigne uno desde Usuarios." en vez de parecer página en blanco.

## Verificación (script end-to-end)
1. **Escenario producción exacto**: borrar TODOS los grupos → crear usuario "profesor" vía `UsuarioCrearForm` (mismo camino que la app) → debe quedar CON grupo; login OK; `/celulares/` 200; manual muestra contenido de profesor.
2. **Editar rol**: cambiar ese usuario a director desde el formulario → grupo actualizado.
3. **Matriz por rol** (inspector, inspector_general, profesor, director):
   - Vistas permitidas → 200 (con POST real de registro en una clave por rol).
   - Vistas prohibidas → 302 denegado.
   - Sidebar muestra sus secciones y oculta las demás.
   - Manual correcto y único para su rol.
4. **Usuario sin rol**: `/ayuda/` muestra el mensaje nuevo.
5. Admin/superusuario: ya verificado en sesiones previas (re-check rápido de `/usuarios/`).
6. `manage.py check` + `makemigrations --check`.

## Acción tuya después del deploy
1. Push/merge → Render despliega → la migración 0004 crea los grupos solos.
2. Editar cada usuario afectado en **Usuarios** y volver a guardar con sus roles marcados (ahora sí quedarán). Alternativa CLI: `python manage.py crear_usuario --username X --grupo profesor --password ...`.
3. Opcional: verificar en Render que el Start Command sea `bash start.sh`.
