# Manual de uso — Inspector General

Rol principal de la inspectoría. Además de registrar (como el Inspector), gestiona alumnos, elimina registros, genera informes y supervisa las acciones disciplinarias.

## Acceso
1. Ingresa con tu usuario y contraseña.
2. Llegas al **Dashboard** con el resumen del mes: retiros, atrasos, uniformes, celulares, visitas, acciones disciplinarias, totales de hoy, top de atrasos por alumno y por curso.
3. Menú lateral completo: Operación (Retiros, Atrasos, Uniformes, Celulares, Visitas, Acciones Disc.), Reportes (Informes, Reporte General, Alumnos).

## Registro diario
Los flujos de registro son iguales que para el rol Inspector: [atrasos/pases](inspector.md#registrar-un-atraso-o-pase), [retiros](inspector.md#registrar-un-retiro-anticipado), [uniformes](inspector.md#registrar-una-falta-de-uniforme), [celulares](inspector.md#requisar-un-celular) y [visitas](inspector.md#registrar-visita-de-apoderado).

## Gestionar alumnos
Ve a **Alumnos** en el menú.

### Agregar un alumno
1. Completa nombre, apellido, curso, RUT y datos del apoderado en la tarjeta "Agregar Alumno".
2. Pulsa **Agregar**.

### Editar un alumno
1. En la tabla pulsa el ícono de lápiz de la fila.
2. Se abre una ventana con todos los datos; modifícalos y pulsa **Guardar cambios**.

### Marcar / desmarcar "Campo"
1. Pulsa el botón circular de la columna **Campo**.
2. Un alumno marcado como Campo registra sus atrasos con motivo `CAMPO` y se excluye de la Frecuencia de Faltas.

### Importar alumnos desde Excel
1. Pulsa **Importar Excel**.
2. El archivo `.xlsx` debe tener estas columnas (la primera fila se ignora):

| Columna | Contenido | Obligatorio |
|---|---|---|
| A | Nombre (MAYÚSCULAS) | Sí |
| B | Apellido (MAYÚSCULAS) | Sí |
| C | Curso (ej.: 1° BÁSICO) | Recomendado |
| D | RUT | No |
| E | Nombre apoderado | No |
| F | Teléfono apoderado | No |

3. Si un alumno ya existe (mismo nombre + apellido + año), se actualizan sus datos en vez de duplicarse.

## Eliminar registros
- En Retiros, Atrasos, Uniformes, Celulares, Visitas y Acciones aparece el ícono de papelera.
- Pide confirmación antes de eliminar. **La acción no se puede deshacer.**

## Informes
Ve a **Reportes** (menú Informes):

1. **Reporte por Alumno**: filtra por curso, escribe el nombre y abre su historial completo (retiros, atrasos, uniformes, celulares, acciones disciplinarias) con exportación PDF/Excel y filtro por rango de fechas.
2. **Informe por Curso**: botón PDF por cada curso; genera el informe institucional con portada, resumen (incluye faltas de uniforme), detalle de atrasos, retiros, uniformes y celulares.
3. **Informe Todos los Cursos**: un solo PDF con todos los cursos del mes o rango seleccionados arriba.
4. **Reporte desde Excel**: sube la planilla de atrasos (descarga la plantilla oficial primero) y obtén el PDF sin guardar nada en la base de datos.

## Reporte General
1. Ve a **Reporte General**.
2. Elige alcance (todo el colegio o un curso) y período (mes/año o rango de fechas).
3. La tabla muestra retiros, atrasos, uniformes, celulares y total por curso o por alumno.
4. Exporta a PDF o Excel con los botones superiores.

## Acciones disciplinarias
1. Ve a **Acciones Disc.**
2. Busca al alumno con el autocompletado, selecciona el **tipo de acción** (*Llamada a apoderado*, *Entrevista* o *Suspensión*) y escribe las observaciones.
3. Pulsa **Registrar**. La acción queda en el listado, en el informe del alumno (HTML/PDF/Excel) y en el contador de acciones de los dashboards. Solo este rol (y Director) puede registrar y eliminar acciones.

## Consejos generales
- La pantalla de carga aparece al guardar o navegar; espera a que termine.
- Exportaciones: el botón muestra "Generando…" hasta que llega el archivo.
- Para imprimir cualquier manual usa la sección **Ayuda** y Ctrl+P.
