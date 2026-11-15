"""Admin control panel for the console (Jazzmin theme)."""
from django.contrib import admin
from django.db.models import Count, Sum

from .models import Conversation, Message, MessageFeedback, Style, UserPreference


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
    raw_id_fields = ("owner", "current_leaf", "style")

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


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "key", "position", "created_at")
    list_filter = (("owner", admin.EmptyFieldListFilter),)
    search_fields = ("name", "prompt", "owner__email")
    raw_id_fields = ("owner",)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "default_model", "default_style", "theme", "language", "send_with_enter", "updated_at")
    list_filter = ("theme", "language", "default_model")
    search_fields = ("user__email",)
    raw_id_fields = ("user", "default_style")


@admin.register(MessageFeedback)
class MessageFeedbackAdmin(admin.ModelAdmin):
    """What users rated — the quickest signal for prompt and model quality."""
    list_display = ("__str__", "user", "rating", "short_comment", "model", "created_at")
    list_filter = ("rating", "message__model", "created_at")
    search_fields = ("comment", "message__content", "user__email")
    raw_id_fields = ("message", "user")
    list_select_related = ("message", "user")

    @admin.display(description="comment")
    def short_comment(self, obj):
        return (obj.comment[:80] + "…") if len(obj.comment) > 80 else obj.comment

    @admin.display(description="model", ordering="message__model")
    def model(self, obj):
        return obj.message.model
