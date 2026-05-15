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
# Esto crea usuario: admin / contraseña: admin1234
```

### 4. Ejecutar
```bash
python manage.py runserver
```
Abrir http://localhost:8000

## Deploy en Railway

1. Crear cuenta en [railway.app](https://railway.app)
2. Nuevo proyecto → Deploy from GitHub repo
3. Agregar servicio PostgreSQL
4. En Variables, agregar:
   - `SECRET_KEY` → una clave aleatoria larga
   - `DEBUG` → False
   - `DATABASE_URL` → (se autocompleta con PostgreSQL)
   - `ALLOWED_HOSTS` → .railway.app
5. Railway detecta el Procfile automáticamente

## Deploy en Render

1. Crear cuenta en [render.com](https://render.com)
2. New Web Service → conectar repo GitHub
3. Build Command: `pip install -r requirements.txt`
4. Start Command: (copiar contenido del Procfile)
5. Agregar PostgreSQL como servicio
6. Configurar las mismas variables de entorno

## Importar alumnos

Preparar un archivo .xlsx con columnas en este orden:
| nombre | apellido | curso | rut (opc.) | apoderado (opc.) | teléfono (opc.) |

Cursos válidos: PRE-KINDER, KINDER, 1° BÁSICO ... 8° BÁSICO, I° MEDIO ... IV° MEDIO

Ir a **Alumnos → Importar Excel** y subir el archivo.

## Usuarios

- **Admin**: acceso completo + panel de administración Django
- **Inspector**: registra datos y ve reportes (crear desde /admin)

Para crear inspectores: entrar a /admin → Usuarios → Agregar usuario.

## Módulos

- **Dashboard**: estadísticas del mes, rankings, últimos registros
- **Retiros**: registro de salidas anticipadas
- **Atrasos**: llegadas tarde, recreo, almuerzo
- **Uniformes**: control de faltas de uniforme
- **Celulares**: celulares requisados
- **Visitas**: registro de apoderados que visitan el colegio
- **Reportes**: por alumno y por curso, descargables en PDF y Excel
