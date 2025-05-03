web: python manage.py collectstatic --noinput && gunicorn backend.wsgi --log-file -
release: python manage.py migrate 