# tasks.py
import time
from celery_app import celery

@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def add(self, a: int, b: int) -> int:
    time.sleep(2)  # simulate some work
    return a + b
