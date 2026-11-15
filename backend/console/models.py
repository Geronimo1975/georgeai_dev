"""GeorgeAI Console — conversations and messages (prompts 02.01 / 02.02).

Messages form a tree through ``parent``: editing a user turn or regenerating a
reply adds a sibling instead of overwriting (prompt 02.07). ``current_leaf``
marks the end of the branch the user is looking at; the active path is that
leaf walked back to the root, and only that path is sent to the model.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def style_usable_by(style, user_id):
    """A preset, or a style owned by ``user_id`` — never another user's prompt."""
    return style is not None and style.owner_id in (None, user_id)


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    title = models.CharField(max_length=200, blank=True, default="")
    model = models.CharField(max_length=64, blank=True, default="")
    is_starred = models.BooleanField(default=False)
    current_leaf = models.ForeignKey(
        "Message", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    style = models.ForeignKey(
        "Style", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]

    def __str__(self):
        return self.title or "Untitled"

    def clean(self):
        # Admin edits go through here: a staff member must not attach one
        # user's custom style (their stored instructions) to someone else's chat.
        if self.style_id and self.owner_id and not style_usable_by(self.style, self.owner_id):
            raise ValidationError({"style": "Pick a preset or a style owned by this conversation's owner."})


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField(blank=True, default="")
    model = models.CharField(max_length=64, blank=True, default="")
    stop_reason = models.CharField(max_length=32, blank=True, default="")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"


class Style(models.Model):
    """A response style (prompt 02.11): a system-prompt fragment applied to the
    next turn. Presets have no owner and are read-only; users add their own."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="styles"
    )
    key = models.SlugField(max_length=40, blank=True, default="")  # presets only: normal / concise / …
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=160, blank=True, default="")
    prompt = models.TextField(blank=True, default="", max_length=4000)
    position = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["key"], condition=models.Q(owner__isnull=True), name="style_preset_key_unique"),
        ]

    @property
    def is_preset(self):
        return self.owner_id is None

    def __str__(self):
        return self.name


class UserPreference(models.Model):
    """Per-user console settings (prompt 02.10)."""

    class Theme(models.TextChoices):
        SYSTEM = "system", "Match system"
        DARK = "dark", "Dark"
        LIGHT = "light", "Light"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="console_prefs")
    default_model = models.CharField(max_length=64, blank=True, default="")
    default_style = models.ForeignKey(Style, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    theme = models.CharField(max_length=8, choices=Theme.choices, default=Theme.DARK)
    language = models.CharField(max_length=8, blank=True, default="")  # "" = follow the browser
    personal_instructions = models.TextField(blank=True, default="", max_length=4000)
    send_with_enter = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences of {self.user}"

    def clean(self):
        if self.default_style_id and self.user_id and not style_usable_by(self.default_style, self.user_id):
            raise ValidationError({"default_style": "Pick a preset or a style owned by this user."})


class MessageFeedback(models.Model):
    """👍/👎 on an assistant reply (prompt 04.08), one per user and message."""

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="feedback")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    rating = models.SmallIntegerField(choices=[(1, "Good"), (-1, "Bad")])
    comment = models.TextField(blank=True, default="", max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["message", "user"], name="feedback_one_per_user")]

    def __str__(self):
        return f"{'👍' if self.rating > 0 else '👎'} {self.message_id}"


class LoginCode(models.Model):
    """A one-time sign-in code sent by email (passwordless console login).

    Only an HMAC of the code is stored. A code is valid for ``TTL`` and allows
    ``MAX_ATTEMPTS`` guesses; requesting a new one invalidates older ones.
    """

    TTL_SECONDS = 600
    MAX_ATTEMPTS = 5

    email = models.EmailField()
    code_hash = models.CharField(max_length=64)
    ip = models.GenericIPAddressField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [  # the per-email and per-IP rate-limit counts
            models.Index(fields=["email", "created_at"], name="logincode_email_created"),
            models.Index(fields=["ip", "created_at"], name="logincode_ip_created"),
        ]

    def __str__(self):
        return f"code for {self.email}"
