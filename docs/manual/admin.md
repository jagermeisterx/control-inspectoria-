# Manual de uso — Administrador

Rol de administración total. Gestiona usuarios, mantiene los datos maestros (alumnos, carga histórica) y tiene todos los permisos del Inspector General.

## Acceso
1. Ingresa con tu usuario y contraseña.
2. Llegas al **Dashboard** y verás además la sección **Configuración** en el menú lateral, con acceso a **Usuarios** y al admin de Django.
3. En la sección **Ayuda** puedes consultar el manual de cualquier rol en pestañas.

## Gestionar usuarios
Ve a **Configuración → Usuarios**.

### Crear un usuario
1. Pulsa **Nuevo usuario**.
2. Completa nombre de usuario (en minúsculas), nombre, apellido y correo.
3. Define la contraseña (dos veces). Debe tener al menos 8 caracteres y no puede ser demasiado común ni solo números.
4. Marca los **roles** que tendrá: Inspector General, Inspector, Profesor o Director. Puedes combinar varios.
5. Deja activado "Activo" para permitir el ingreso y pulsa **Guardar**.

> Solo marca "Administrador total" para crear otro superusuario.

### Editar un usuario
1. Pulsa el lápiz de la fila correspondiente.
2. Modifica datos, roles o el estado Activo (desactivar impide el inicio de sesión sin borrar su historial).
3. Guarda.

> **Protección:** no puedes desactivarte ni quitarte el perfil de administrador a ti mismo.

### Restablecer una contraseña
1. Pulsa el ícono de llave de la fila.
2. Escribe y confirma la nueva contraseña (se aplican las mismas validaciones).
3. El usuario podrá entrar inmediatamente con la nueva contraseña; la anterior queda invalidada.

## Importar alumnos desde Excel
Sección **Alumnos → Importar Excel**:

| Columna | Contenido | Obligatorio |
|---|---|---|
| A | Nombre (MAYÚSCULAS) | Sí |
| B | Apellido (MAYÚSCULAS) | Sí |
| C | Curso (ej.: 1° BÁSICO) | Recomendado |
| D | RUT | No |
| E | Nombre apoderado | No |
| F | Teléfono apoderado | No |

- Si el alumno ya existe (nombre + apellido + año) se actualizan sus datos.

## Cargar registro histórico
Sección **Alumnos → Cargar Registro Histórico** (solo administrador):

1. Descarga la **planilla base (.xlsx)**: trae hojas Retiros, Atrasos, Uniformes, Celulares y Visitas ya configuradas con menús desplegables.
2. Respeta el orden de columnas, fechas `AAAA-MM-DD`, horas `HH:MM`, nombres en MAYÚSCULAS y valores SI/NO.
3. Sube el archivo: se crean automáticamente los alumnos que no existan (con nombre + apellido + curso de la fila).
4. Al terminar verás el resumen por hoja; si hubo filas con problemas, descarga el Excel de errores, corrige y vuelve a subir solo esas filas.

## Permisos adicionales
Como administrador también puedes usar todo lo documentado para el [Inspector General](inspector_general.md): registros diarios, gestión y edición de alumnos, eliminación de registros e informes.

## Consejos generales
- La pantalla de carga aparece al guardar o navegar; espera a que termine.
- Exportaciones: el botón muestra "Generando…" hasta recibir el archivo.
- Imprime cualquier manual desde **Ayuda** con Ctrl+P.
