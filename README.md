# 🏫 Inspectoría Digital

Sistema web para gestión de inspectoría escolar. Registra retiros, atrasos, control de uniformes, celulares requisados y visitas de apoderados. Genera reportes por alumno y por curso en PDF y Excel.

## Instalación local

### 1. Requisitos
- Python 3.11+
- Git

### 2. Clonar y configurar
```bash
git clone <tu-repo>
cd inspectoria

# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores
```

### 3. Inicializar base de datos
```bash
python manage.py migrate
python manage.py crear_admin
# Esto crea el superusuario inicial (ver credenciales en core/management/commands/crear_admin.py).
# **Cámbiala en el primer login** desde /admin/password_change/.
```

### 4. Ejecutar
```bash
python manage.py runserver
```
Abrir http://localhost:8000

## Deploy en Render + Supabase

### Arquitectura
- **App**: Render (plan Free, región Ohio)
- **BD**: Supabase Postgres (Transaction pooler, puerto 6543)
- **Estáticos**: WhiteNoise (incluido en el contenedor)

### Requisitos previos
1. Proyecto en [supabase.com](https://supabase.com) creado.
2. Cuenta en [render.com](https://render.com) con el repo de GitHub conectado.

### Configurar DATABASE_URL en Supabase
1. En el dashboard de Supabase: **Settings → Database → Connection string → Transaction pooler**.
2. Copia la URL (puerto 6543) y agrégale al final:
   ```
   ?pgbouncer=true&connection_limit=1
   ```
3. Quedará así:
   ```
   postgresql://postgres.PROYECTO:[PASSWORD]@aws-0-us-east-2.pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1
   ```

### Crear el Web Service en Render
1. **Dashboard Render** → **New** → **Web Service** → conectar el repo.
2. Configurar:
   - **Name**: `inspectoria`
   - **Region**: `Ohio (US East)`
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn inspectoria.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
   - **Plan**: `Free`
3. En **Environment**, agregar:
   - `DJANGO_SETTINGS_MODULE` = `inspectoria.settings`
   - `PYTHON_VERSION` = `3.12.11`
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `.onrender.com`
   - `CSRF_TRUSTED_ORIGINS` = `https://*.onrender.com`
   - `SECRET_KEY` = (Generate)
   - `DATABASE_URL` = (pegar la URL de Supabase)
4. Click **Create Web Service**.

### Verificación
- Abre `https://inspectoria.onrender.com/` → debería redirigir a `/accounts/login/`.
- Login con las credenciales definidas en `core/management/commands/crear_admin.py` (creado por el `release` command).
- **Cambia la contraseña de inmediato** en `/admin/password_change/`.

### Notas importantes
- **Cold start**: el plan Free duerme la app tras 15 min sin tráfico. El primer request tarda ~30 s.
- **Sin disco persistente**: no guardar archivos subidos en `media/`. Los Excel/PDF se procesan en memoria.
- **Migraciones**: corren automáticamente antes de cada release (`release:` en Procfile).

## Importar alumnos

Preparar un archivo .xlsx con columnas en este orden:
| nombre | apellido | curso | rut (opc.) | apoderado (opc.) | teléfono (opc.) |

Cursos válidos: PRE-KINDER, KINDER, 1° BÁSICO ... 8° BÁSICO, I° MEDIO ... IV° MEDIO

Ir a **Alumnos → Importar Excel** y subir el archivo.

## Usuarios

El sistema maneja roles mediante **grupos de Django**. El superusuario (Admin) tiene acceso total. Para crear los grupos y usuarios, ejecutar los comandos de gestión:

### 1. Crear los grupos de roles
```bash
python manage.py crear_grupos
```
Crea: `inspector_general`, `inspector`, `profesor`, `director`.

### 2. Crear usuarios con su rol
```bash
python manage.py crear_usuario --username inspector1 --grupo inspector --password CAMBIAME --nombre "Nombre" --apellido "Apellido"
python manage.py crear_usuario --username director --grupo director --password CAMBIAME
```

También se pueden asignar roles desde `/admin` (sección Usuarios → grupo).

### Matriz de permisos

| Capacidad | Admin | Insp. General | Insp. Normal | Profesor | Director |
|---|---|---|---|---|---|
| Dashboard normal | ✅ | ✅ | ➡ Atrasos | ➡ Informes | ➡ Su dashboard |
| Dashboard Director (comparación mensual) | ✅ | – | – | – | ✅ |
| Anotar retiros / atrasos / uniformes | ✅ | ✅ | ✅ | – | – |
| Anotar celulares (con "N° veces" por alumno) | ✅ | ✅ | ✅ | ✅ | – |
| Anotar visitas | ✅ | ✅ | ✅ | – | – |
| Borrar registros | ✅ | ✅ | – | – | – |
| Alumnos (agregar / importar) | ✅ | ✅ | – | – | – |
| Cargar histórico | ✅ | – | – | – | – |
| Informes (alumno/curso, PDF, Excel) | ✅ | ✅ | – | ✅ | ✅ |
| Reporte General (colegio/curso) | ✅ | ✅ | – | – | ✅ |
| Panel Django Admin | ✅ | – | – | – | – |

## Módulos

- **Dashboard**: estadísticas del mes, rankings, últimos registros
- **Retiros**: registro de salidas anticipadas
- **Atrasos**: llegadas tarde, recreo, almuerzo
- **Uniformes**: control de faltas de uniforme
- **Celulares**: celulares requisados
- **Visitas**: registro de apoderados que visitan el colegio
- **Reportes**: por alumno y por curso, descargables en PDF y Excel
- **Reporte General**: resumen del colegio o de un curso en un mes, con exportación PDF/Excel
- **Dashboard Director**: métricas del mes con comparación vs mes anterior y tendencia de 6 meses
