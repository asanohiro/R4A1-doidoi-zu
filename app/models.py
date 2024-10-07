# app/models.py
from django.db import models

from django.db import models

from AWS import settings


class LostItem(models.Model):
    image = models.ImageField(upload_to='lost_items/', blank=True, null=True)  # 画像をS3にアップロード
    image_url = models.URLField(blank=True, null=True)  # S3の画像URLを保存
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    date_time = models.DateTimeField(auto_now_add=True)
    prefecture = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        if self.image:
            # S3にアップロードされた画像のURLを自動的に保存
            self.image_url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.image.name}'
        super().save(*args, **kwargs)
