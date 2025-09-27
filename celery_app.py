# celery_app.py
from celery import Celery

celery = Celery(__name__)

def init_celery(app):
    """Bind Celery to the Flask app factory settings + app context."""
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        timezone="UTC",
    )

    # Ensure tasks run with Flask app context (DB, configs, etc.)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
