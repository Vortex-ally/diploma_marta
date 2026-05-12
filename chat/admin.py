from django.contrib import admin

from .models import AIChatRecord


@admin.register(AIChatRecord)
class AIChatRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'model', 'is_wizard', 'short_user_message')
    list_filter = ('is_wizard', 'model', 'created_at')
    search_fields = ('user__username', 'user__email', 'user_message', 'assistant_message')
    ordering = ('-created_at',)

    def short_user_message(self, obj: AIChatRecord) -> str:
        s = (obj.user_message or '').strip().replace('\n', ' ')
        return (s[:80] + '...') if len(s) > 80 else s

    short_user_message.short_description = 'Запит'
