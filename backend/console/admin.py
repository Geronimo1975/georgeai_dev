"""Admin control panel for the console (Jazzmin theme)."""
from django.contrib import admin
from django.db.models import Count, Sum

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("role", "short_content", "model", "stop_reason", "input_tokens", "output_tokens", "created_at")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    @admin.display(description="content")
    def short_content(self, obj):
        return (obj.content[:160] + "…") if len(obj.content) > 160 else obj.content


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", "model", "n_messages", "tokens", "is_starred", "updated_at")
    list_filter = ("model", "is_starred", "updated_at")
    search_fields = ("title", "owner__email", "messages__content")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [MessageInline]
    date_hierarchy = "updated_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner").annotate(
            _n=Count("messages", distinct=True),
            _tok=Sum("messages__output_tokens"),
        )

    @admin.display(description="messages", ordering="_n")
    def n_messages(self, obj):
        return obj._n

    @admin.display(description="output tokens", ordering="_tok")
    def tokens(self, obj):
        return obj._tok or 0


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "conversation", "role", "model", "stop_reason", "output_tokens", "created_at")
    list_filter = ("role", "model", "stop_reason")
    search_fields = ("content", "conversation__title", "conversation__owner__email")
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("conversation", "parent")
