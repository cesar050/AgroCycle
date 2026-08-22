from celery import Celery
import os

def make_celery():
    celery = Celery(
        'agrocycle',
        broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')
    )
    return celery

celery_app = make_celery()
