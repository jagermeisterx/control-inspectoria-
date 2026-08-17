#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating groups..."
python manage.py crear_grupos

echo "Creating admin..."
python manage.py crear_admin

echo "Starting server..."
exec gunicorn inspectoria.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile -
