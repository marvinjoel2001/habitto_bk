web: daphne -b 0.0.0.0 -p $PORT bk_habitto.asgi:application
worker: celery -A bk_habitto worker --loglevel=info
beat: celery -A bk_habitto beat --loglevel=info
release: python manage.py migrate
