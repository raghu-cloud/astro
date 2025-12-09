# My_AI_Guruji/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'My_AI_Guruji.settings')

app = Celery("My_AI_Guruji", broker="redis://redis:6379/0")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
