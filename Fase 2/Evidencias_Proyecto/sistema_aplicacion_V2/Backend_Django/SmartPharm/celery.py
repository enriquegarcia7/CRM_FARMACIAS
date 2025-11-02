import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartPharm.settings')

app = Celery('smartpharm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'run-offer-etl-every-3-days': {
        'task': 'core.tasks.run_offer_etl_task',
        'schedule': crontab(hour=2, minute=0, day_of_week='*/3'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
