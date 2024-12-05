from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Djangoのsettingsモジュールをロード
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AWS.settings')

app = Celery('AWS')

# Django settingsのCELERY設定をロード
app.config_from_object('django.conf:settings', namespace='CELERY')

# アプリのタスクを自動的に探索
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')