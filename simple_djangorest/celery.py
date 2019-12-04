import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simple_djangorest.settings')

app = Celery('simple_djangorest')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
