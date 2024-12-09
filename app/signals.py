from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from .views import notify_user_on_new_message

@receiver(post_save, sender=Message)
def notify_user_on_new_message(sender, instance, **kwargs):
  chatroom = instance.chatroom
  sender_user = instance.sender

  # チャットの相手を取得
  if chatroom.user1 == sender_user:
    recipient_user = chatroom.user2
  else:
    recipient_user = chatroom.user1

  # メールを送信
  send_mail(
    subject="新しいメッセージが届きました",
    message=f"{sender_user.nickname}からメッセージが届きました。",
    from_email="no-reply@example.com",
    recipient_list=[recipient_user.email],
    fail_silently=False,
  )

