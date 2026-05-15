web: python manage.py migrate && python manage.py crear_admin && python manage.py collectstatic --noinput && gunicorn inspectoria.wsgi --bind 0.0.0.0:$PORT
