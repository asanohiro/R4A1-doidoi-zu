from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Block
from .views import notify_user_on_new_message


@receiver(post_save, sender=Message)
def notify_user_on_new_message(sender, instance, created, **kwargs):
    if created:  # 新しいメッセージが作成された場合のみ通知
        chatroom = instance.chatroom
        sender_user = instance.sender

        # チャットの相手を取得
        if chatroom.user1 == sender_user:
            recipient_user = chatroom.user2
        else:
            recipient_user = chatroom.user1

        # ブロックされているか確認
        is_blocked = Block.objects.filter(blocker=recipient_user, blocked=sender_user).exists()

        if not is_blocked:  # ブロックされていない場合のみ通知
            if recipient_user.email:  # メールアドレスが登録されている場合のみ通知
                send_mail(
                    subject=f"{sender_user.nickname}からメッセージが届きました",
                    message=f"{sender_user.nickname}から新しいメッセージが届きました。\n内容: {instance.text}",
                    from_email="no-reply@example.com",
                    recipient_list=[recipient_user.email],
                    fail_silently=False,
                )
