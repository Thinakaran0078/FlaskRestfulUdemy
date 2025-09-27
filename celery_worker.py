# celery_worker.py
from app import create_app
from celery_app import init_celery, celery

# Build the same Flask app used by web, then bind Celery to it
flask_app = create_app()
init_celery(flask_app)  # important for app context in tasks

# The worker will be started via: celery -A celery_worker.celery worker -l info
