"""Model catalog + provider abstraction (prompts 01.08 / 03.01 / 03.02 / 09.02).

``get_provider()`` returns the Anthropic provider when ``ANTHROPIC_API_KEY`` is
set and the SDK is installed, otherwise a deterministic fake that streams a
canned reply — so the console works offline and in tests at zero API cost.
Force one with ``LLM_PROVIDER=fake|anthropic``.
"""
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings

MODELS = [
    {"id": "claude-sonnet-5-5", "name": "Sonnet 5.5", "description": "Smart, efficient model for everyday use", "default": True},
    {"id": "claude-opus-5-5", "name": "Opus 5.5", "description": "Most capable for complex work"},
    {"id": "claude-haiku-5-5", "name": "Haiku 5.5", "description": "Fastest for quick answers"},
]
MODEL_IDS = {m["id"] for m in MODELS}
DEFAULT_MODEL = next(m["id"] for m in MODELS if m.get("default"))
TITLE_MODEL = "claude-haiku-5-5"
MAX_TOKENS = 8192

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "base.md").read_text(encoding="utf-8")


@dataclass
class StreamResult:
    """Filled in by the provider as the stream runs; read after it ends."""
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""
    extra: dict = field(default_factory=dict)


class FakeProvider:
    name = "fake"

    def stream(self, model, system, messages, result):
        last = messages[-1]["content"] if messages else ""
        reply = (
            f"**Demo mode** — this reply comes from the offline fake provider instead of "
            f"`{model}` (no `ANTHROPIC_API_KEY`, or `LLM_PROVIDER=fake`).\n\n"
            f"You wrote:\n\n> {last[:400]}\n\n"
            "Everything else is real: the message was saved, streamed token by token, "
            "and is visible in the Django admin.\n\n"
            "```python\n# backend/.env\nANTHROPIC_API_KEY=sk-ant-...\n```\n\n"
            "Add a key with API credit and restart without `LLM_PROVIDER=fake` to talk to Claude."
        )
        result.input_tokens = sum(len(m["content"]) // 4 for m in messages)
        for word in reply.split(" "):
            time.sleep(0.015)
            result.output_tokens += 1
            yield word + " "
        result.stop_reason = "end_turn"

    def title(self, first_user_message):
        text = " ".join(first_user_message.split())
        return (text[:48] + "…") if len(text) > 48 else text or "New chat"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key, max_retries=2)

    def stream(self, model, system, messages, result):
        with self.client.messages.stream(
            model=model,
            max_tokens=MAX_TOKENS,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
            final = stream.get_final_message()
        result.input_tokens = final.usage.input_tokens
        result.output_tokens = final.usage.output_tokens
        result.stop_reason = final.stop_reason or ""

    def title(self, first_user_message):
        try:
            msg = self.client.messages.create(
                model=TITLE_MODEL,
                max_tokens=30,
                system="Write a 3-6 word title for a chat that starts with the user's message. "
                "Use the message's language. Reply with the title only, no quotes or punctuation at the end.",
                messages=[{"role": "user", "content": first_user_message[:2000]}],
            )
            title = "".join(b.text for b in msg.content if b.type == "text").strip().strip('"')
            return title[:120] or FakeProvider().title(first_user_message)
        except Exception:  # title is cosmetic — never fail the turn over it
            return FakeProvider().title(first_user_message)


def get_provider():
    choice = os.environ.get("LLM_PROVIDER", getattr(settings, "LLM_PROVIDER", "auto"))
    key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if choice == "fake":
        return FakeProvider()
    if key and choice in ("auto", "anthropic"):
        try:
            return AnthropicProvider(key)
        except ImportError:
            if choice == "anthropic":
                raise
    return FakeProvider()
