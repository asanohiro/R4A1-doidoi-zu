from celery import Celery
from datetime import datetime
from app.models import LostItem

app = Celery('tasks')

@app.task
def delete_expired_items():
    now = datetime.now()
    expired_items = LostItem.objects.filter(expire_at__lt=now)

    deleted_count = expired_items.count()
    if deleted_count > 0:
        # ログを残す（例: ファイルやデータベース）
        with open("deleted_lost_items_log.txt", "a") as file:
            for item in expired_items:
                file.write(f"Deleted: {item.id}, Product: {item.product}, Time: {now}\n")

        # データを削除
        expired_items.delete()

    return f"Deleted {deleted_count} expired items."