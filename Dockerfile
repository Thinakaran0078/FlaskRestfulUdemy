FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser \
    && chown appuser:appuser /app

COPY --chown=appuser:appuser app.py db.py blocklist.py schemas.py ./
COPY --chown=appuser:appuser celery_app.py celery_worker.py tasks.py tasks_bp.py ./
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser resources/ ./resources/

USER appuser

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "--capture-output", "app:create_app()"]