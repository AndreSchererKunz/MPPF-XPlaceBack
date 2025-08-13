from django.db import models
from django.conf import settings
from core.models import Post

class Notification(models.Model):
    TYPE_CHOICES = [
        ('FOLLOW', 'Follow'),
        ('LIKE', 'Like'),
        ('COMMENT', 'Comment'),
        ('REPOST', 'Repost'),
        ('BOOKMARK', 'Bookmark'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender} -> {self.recipient} ({self.type})"
