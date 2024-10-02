# app/models.py
from django.db import models

# class LostItem(models.Model):
#     image = models.ImageField(upload_to='images/')
#     comment = models.TextField(blank=True, null=True)
#     location = models.CharField(max_length=255, blank=True, null=True)
#     date_time = models.DateTimeField(auto_now_add=True)


class LostItem(models.Model):
    image = models.ImageField(upload_to='lost_items/')  # 画像フィールド
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)  # 緯度・経度
    date_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='unclaimed')
    prefecture = models.CharField(max_length=100, blank=True)  # 新しい都道府県フィールド


