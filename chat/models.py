from django.conf import settings
from django.db import models


class AIChatRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_chat_records')
    user_message = models.TextField()
    assistant_message = models.TextField(blank=True)
    model = models.CharField(max_length=120, blank=True)
    is_wizard = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI-запит'
        verbose_name_plural = 'AI-запити'

    def __str__(self) -> str:
        msg = (self.user_message or '').strip().replace('\n', ' ')
        if len(msg) > 60:
            msg = msg[:57] + '...'
        return f'{self.user_id}: {msg}'
