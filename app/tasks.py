from celery import shared_task

from app.models import LostItem
from django.utils.timezone import now
import os

@shared_task
def delete_expired_items():
    expired_items = LostItem.objects.filter(expire_at__lt=now())
    count = expired_items.count()

    # 削除データを保存
    save_deleted_items_to_file(expired_items)

    # データベースから削除
    expired_items.delete()
    return f"Deleted {count} expired items."

def save_deleted_items_to_file(expired_items):
    """削除されたデータをテキストとして保存"""
    file_path = os.path.join('deleted_items_log.txt')  # ファイル名を設定
    print(f"File path for deleted items log: {file_path}")
    with open(file_path, 'a') as file:
        for item in expired_items:
            file.write(f"ID: {item.id}, Product: {item.product}, DateTime: {item.date_time}, Comment: {item.comment}\n")