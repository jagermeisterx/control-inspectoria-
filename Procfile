release: python manage.py migrate --noinput && python manage.py crear_admin
web: gunicorn inspectoria.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 60 --access-logfile -
