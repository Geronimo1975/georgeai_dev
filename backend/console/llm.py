"""Model catalog + provider abstraction (prompts 01.08 / 03.01 / 03.02 / 09.02).

Each model belongs to a vendor. ``get_provider(model)`` returns that vendor's
live provider when its key is configured, otherwise a deterministic fake that
streams a canned reply — so the console works offline and in tests at zero API
cost. ``LLM_PROVIDER=fake`` forces the fake for every model.

Vendors:
  anthropic — ``ANTHROPIC_API_KEY``, official SDK.
  deepseek  — ``DEEPSEEK_API_KEY``; any OpenAI-compatible chat-completions
              endpoint at ``DEEPSEEK_BASE_URL`` (default: DeepSeek's own API,
              servers in China). Point it at an EU host serving the open
              DeepSeek weights to keep data in the EU — no code change.
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings

log = logging.getLogger(__name__)

MODELS = [
    {"id": "claude-sonnet-5-5", "vendor": "anthropic", "name": "Sonnet 5.5", "description": "Smart, efficient model for everyday use", "default": True},
    {"id": "claude-opus-5-5", "vendor": "anthropic", "name": "Opus 5.5", "description": "Most capable for complex work"},
    {"id": "claude-haiku-5-5", "vendor": "anthropic", "name": "Haiku 5.5", "description": "Fastest for quick answers"},
    {"id": "deepseek-chat", "vendor": "deepseek", "name": "DeepSeek Chat", "description": "Fast general-purpose open model"},
    {"id": "deepseek-reasoner", "vendor": "deepseek", "name": "DeepSeek Reasoner", "description": "Thinks step by step before answering"},
]
VENDORS = {"anthropic": "Claude", "deepseek": "DeepSeek"}
MODEL_IDS = {m["id"] for m in MODELS}
VENDOR_OF = {m["id"]: m["vendor"] for m in MODELS}
DEFAULT_MODEL = next(m["id"] for m in MODELS if m.get("default"))
TITLE_MODEL = "claude-haiku-5-5"
DEEPSEEK_TITLE_MODEL = "deepseek-chat"
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
            f"`{model}` (no API key for that model's vendor, or `LLM_PROVIDER=fake`).\n\n"
            f"You wrote:\n\n> {last[:400]}\n\n"
            "Everything else is real: the message was saved, streamed token by token, "
            "and is visible in the Django admin.\n\n"
            "```python\n# backend/.env\nANTHROPIC_API_KEY=sk-ant-...\nDEEPSEEK_API_KEY=sk-...\n```\n\n"
            "Add a key with API credit and restart without `LLM_PROVIDER=fake` to get real replies."
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
        except Exception as exc:  # title is cosmetic — never fail the turn over it
            log.warning("console title generation failed (anthropic): %s: %s", type(exc).__name__, exc)
            return FakeProvider().title(first_user_message)


class ProviderHTTPError(Exception):
    """Non-2xx answer from an OpenAI-compatible endpoint; ``friendly_error`` maps it."""

    def __init__(self, status_code, host):
        super().__init__(f"HTTP {status_code} from {host}")
        self.status_code, self.host = status_code, host


class IncompleteStreamError(Exception):
    pass


def is_deepseek_host(host):
    """DeepSeek's own API — exact domain match, so ``evil-deepseek.com`` is not it."""
    return host == "deepseek.com" or host.endswith(".deepseek.com")


class OpenAICompatibleProvider:
    """Streams from an OpenAI-style ``/chat/completions`` endpoint (DeepSeek).

    Plain httpx (already installed with the Anthropic SDK) instead of another
    SDK: the protocol is a POST plus ``data:`` lines, and keeping it generic
    means any compatible host works by changing the base URL.
    """
    name = "deepseek"

    def __init__(self, api_key, base_url, title_model=DEEPSEEK_TITLE_MODEL, transport=None):
        import httpx

        self.base_url = base_url.rstrip("/")
        self.host = urlparse(self.base_url).hostname or ""
        self.title_model = title_model
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(60.0, read=300.0),
            transport=transport,
        )

    def _payload(self, model, system, messages, **extra):
        return {
            "model": model,
            "messages": [{"role": "system", "content": system}, *messages],
            "max_tokens": MAX_TOKENS,
            **extra,
        }

    def stream(self, model, system, messages, result):
        payload = self._payload(model, system, messages, stream=True,
                                stream_options={"include_usage": True})
        done = False
        with self.client.stream("POST", f"{self.base_url}/chat/completions", json=payload) as resp:
            if not resp.is_success:  # 3xx included: redirects are not followed, so never "success"
                resp.read()
                raise ProviderHTTPError(resp.status_code, self.host)
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    done = True
                    break
                chunk = json.loads(data)
                if usage := chunk.get("usage"):
                    result.input_tokens = usage.get("prompt_tokens", 0)
                    result.output_tokens = usage.get("completion_tokens", 0)
                for choice in chunk.get("choices") or []:
                    # deepseek-reasoner also streams ``reasoning_content``; only the
                    # final answer is shown and stored, as on claude.ai.
                    if text := (choice.get("delta") or {}).get("content"):
                        yield text
                    if reason := choice.get("finish_reason"):
                        result.stop_reason = {"stop": "end_turn", "length": "max_tokens"}.get(reason, reason)
        if not done:
            # A body that just ends without the terminator is a cut connection,
            # not a finished answer — surface it instead of saving it as complete.
            raise IncompleteStreamError("The model provider closed the stream before finishing.")

    def title(self, first_user_message):
        try:
            resp = self.client.post(f"{self.base_url}/chat/completions", json={
                "model": self.title_model,
                "max_tokens": 30,
                "messages": [
                    {"role": "system", "content": "Write a 3-6 word title for a chat that starts with the user's message. "
                     "Use the message's language. Reply with the title only, no quotes or punctuation at the end."},
                    {"role": "user", "content": first_user_message[:2000]},
                ],
            })
            resp.raise_for_status()
            title = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
            return title[:120] or FakeProvider().title(first_user_message)
        except Exception as exc:  # title is cosmetic — never fail the turn over it
            log.warning("console title generation failed (%s): %s: %s", self.host, type(exc).__name__, exc)
            return FakeProvider().title(first_user_message)


def provider_choice():
    return os.environ.get("LLM_PROVIDER", getattr(settings, "LLM_PROVIDER", "auto"))


def vendor_live(vendor):
    """True when real replies are possible for this vendor: its key is set and
    ``LLM_PROVIDER`` neither forces the fake nor pins another vendor."""
    choice = provider_choice()
    if choice == "fake" or (choice in VENDORS and choice != vendor):
        return False
    if vendor == "anthropic":
        return bool(getattr(settings, "ANTHROPIC_API_KEY", ""))
    if vendor == "deepseek":
        return bool(getattr(settings, "DEEPSEEK_API_KEY", ""))
    return False


def deepseek_host():
    return urlparse(getattr(settings, "DEEPSEEK_BASE_URL", "") or "https://api.deepseek.com").hostname or ""


def catalog():
    """Models for the picker. DeepSeek is listed only once a key is set and no
    other vendor is pinned — no point offering it in demo mode only."""
    out, choice = [], provider_choice()
    for m in MODELS:
        if m["vendor"] == "deepseek" and (
            not getattr(settings, "DEEPSEEK_API_KEY", "") or choice not in ("auto", "fake", "deepseek")
        ):
            continue
        item = {**m, "vendor_name": VENDORS[m["vendor"]], "live": vendor_live(m["vendor"])}
        if m["vendor"] == "deepseek":
            host = deepseek_host()
            item["data_note"] = ("Processed by DeepSeek on servers in China" if is_deepseek_host(host)
                                 else f"Processed via {host}")
        out.append(item)
    return out


def available_model_ids():
    return {m["id"] for m in catalog()}


def get_provider(model=None):
    vendor = VENDOR_OF.get(model or DEFAULT_MODEL, "anthropic")
    choice = provider_choice()
    if not vendor_live(vendor):  # also covers LLM_PROVIDER=fake and a pin to another vendor
        return FakeProvider()
    if vendor == "deepseek":
        return OpenAICompatibleProvider(
            settings.DEEPSEEK_API_KEY,
            getattr(settings, "DEEPSEEK_BASE_URL", "") or "https://api.deepseek.com",
        )
    try:
        return AnthropicProvider(settings.ANTHROPIC_API_KEY)
    except ImportError:
        if choice == "anthropic":
            raise
        return FakeProvider()
