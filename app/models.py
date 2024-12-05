# app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from AWS import settings

def default_expire_at():
    return now() + timedelta(days=30)

class LostItem(models.Model):
    image = models.ImageField(upload_to='lost_items/', blank=True, null=True)  # 画像をS3にアップロード
    image_url = models.URLField(blank=True, null=True)  # S3の画像URLを保存
    product = models.CharField(max_length=50, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    date_time = models.DateTimeField(auto_now_add=True)
    prefecture = models.CharField(max_length=100, blank=True)
    comment = models.CharField(max_length=256, blank=True, null=True)
    nickname = models.CharField(max_length=50)
    expire_at = models.DateTimeField(default=default_expire_at)


    #　s3のurl保存と有効期限設定
    def save(self, *args, **kwargs):
        if self.image:
            # S3にアップロードされた画像のURLを自動的に保存
            self.image_url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.image.name}'
        super().save(*args, **kwargs)

        if not self.expire_at:
            self.expire_at = now() + timedelta(days=30)
        super().save(*args, **kwargs)

    #　有効期限が過ぎてるか
    def is_expired(self):
        # データが有効期限を過ぎているかどうかを判定
        return now() > self.expire_at

    # s3のurl
    def save(self, *args, **kwargs):
        if self.image:
            # S3にアップロードされた画像のURLを自動的に保存
            self.image_url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.image.name}'
        super().save(*args, **kwargs)

class User(models.Model):
  nickname = models.CharField(max_length=50)
  email = models.EmailField(unique=True)
  password = models.CharField(max_length=128)  # Djangoの暗号化パスワードに対応

  def __str__(self):
    return self.nickname


class ChatRoom(models.Model):
  # 特定の2人のユーザーを指定するためのフィールド
  user1 = models.ForeignKey(User, related_name='chatroom_user1', on_delete=models.CASCADE)
  user2 = models.ForeignKey(User, related_name='chatroom_user2', on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Chat between {self.user1.username} and {self.user2.username}"


class Message(models.Model):
  chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
  sender = models.ForeignKey(User, on_delete=models.CASCADE)
  text = models.TextField()
  timestamp = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Message from {self.sender.username} in {self.chatroom}"