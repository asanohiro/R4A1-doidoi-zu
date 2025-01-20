from celery import Celery
from AWS import settings
from AWS.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

app = Celery('AWS',
             broker=CELERY_BROKER_URL,
             backend=CELERY_RESULT_BACKEND,
             include=['AWS.tasks'])

app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()