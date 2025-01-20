# from __future__ import absolute_import, unicode_literals
# import os
# from celery import Celery
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AWS.settings')
#
# app = Celery('AWS')
#
# app.config_from_object('django.conf:settings', namespace='CELERY')
#
# app.autodiscover_tasks()
#
# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
from celery import Celery

app = Celery('AWS',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0',
             include=['app.tasks'])

app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()