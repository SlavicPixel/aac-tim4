release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn aac_tim4.wsgi --log-file -