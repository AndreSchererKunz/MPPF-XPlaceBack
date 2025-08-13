from .models import Notification

def create_notification(recipient, sender, type, message, post=None):
    if recipient != sender:
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            type=type,
            message=message,
            post=post
        )
