"""GeorgeAI Console API + page (prompts 01.11, 02.03–02.08, 04.01).

Plain Django views returning JSON: the streaming endpoint needs a raw
StreamingHttpResponse anyway, and CsrfViewMiddleware protects every unsafe
method with the same csrftoken cookie auth.js already uses.
"""
import json
import logging
import uuid
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from . import llm
from .models import Conversation, Message

MAX_MESSAGE_CHARS = 100_000
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- helpers

def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error(401, "authentication_error", "Sign in to use the console.")
        return view(request, *args, **kwargs)
    return wrapper


def error(status, type_, message):
    return JsonResponse({"error": {"type": type_, "message": message}}, status=status)


def body(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


def own_conversation(request, pk):
    # 404 (not 403) for someone else's conversation — don't leak that it exists.
    try:
        return Conversation.objects.get(pk=pk, owner=request.user)
    except Conversation.DoesNotExist:
        raise Http404


def conv_json(c):
    return {
        "id": str(c.id),
        "title": c.title,
        "model": c.model,
        "is_starred": c.is_starred,
        "updated_at": c.updated_at.isoformat(),
    }


def msg_json(m):
    return {
        "id": str(m.id),
        "role": m.role,
        "content": m.content,
        "model": m.model,
        "stop_reason": m.stop_reason,
        "created_at": m.created_at.isoformat(),
    }


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# --------------------------------------------------------------------------- page

@login_required(login_url="/console/login/")
@ensure_csrf_cookie
def console_page(request, rest=""):
    return render(request, "console/index.html")


# --------------------------------------------------------------------------- API

@api_login_required
@require_http_methods(["GET"])
def bootstrap(request):
    u = request.user
    convs = Conversation.objects.filter(owner=u).only(
        "id", "title", "model", "is_starred", "updated_at"
    )[:300]
    return JsonResponse({
        "user": {
            "email": u.email,
            "name": getattr(u, "name", "") or u.email.split("@")[0],
            "is_staff": u.is_staff,
        },
        "models": llm.MODELS,
        "default_model": llm.DEFAULT_MODEL,
        "provider": llm.get_provider().name,
        "conversations": [conv_json(c) for c in convs],
    })


@api_login_required
@require_http_methods(["GET", "POST"])
def conversations(request):
    if request.method == "POST":
        data = body(request)
        model = data.get("model") if data.get("model") in llm.MODEL_IDS else llm.DEFAULT_MODEL
        c = Conversation.objects.create(owner=request.user, model=model)
        return JsonResponse(conv_json(c), status=201)
    qs = Conversation.objects.filter(owner=request.user)
    if q := request.GET.get("q", "").strip():
        qs = qs.filter(title__icontains=q)
    return JsonResponse({"data": [conv_json(c) for c in qs[:300]]})


@api_login_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def conversation_detail(request, pk):
    c = own_conversation(request, pk)
    if request.method == "DELETE":
        c.delete()
        return JsonResponse({}, status=204)
    if request.method == "PATCH":
        data = body(request)
        if "title" in data:
            c.title = str(data["title"]).strip()[:200]
        if "is_starred" in data:
            c.is_starred = bool(data["is_starred"])
        if data.get("model") in llm.MODEL_IDS:
            c.model = data["model"]
        c.save()
        return JsonResponse(conv_json(c))
    return JsonResponse({
        **conv_json(c),
        "messages": [msg_json(m) for m in c.messages.all()],
    })


@api_login_required
@require_http_methods(["POST"])
def send_message(request, pk):
    """Save the user turn (or regenerate the last reply) and stream the answer as SSE."""
    c = own_conversation(request, pk)
    data = body(request)
    regenerate = bool(data.get("regenerate"))
    model = data.get("model") if data.get("model") in llm.MODEL_IDS else (c.model or llm.DEFAULT_MODEL)
    content = str(data.get("content", "")).strip()

    with transaction.atomic():
        history = list(c.messages.all())
        if regenerate:
            if history and history[-1].role == Message.Role.ASSISTANT:
                history.pop().delete()
            if not history:
                return error(400, "invalid_request_error", "Nothing to regenerate.")
            user_msg, new_user = history[-1], False
        else:
            if not content:
                return error(400, "invalid_request_error", "Message is empty.")
            if len(content) > MAX_MESSAGE_CHARS:
                return error(400, "invalid_request_error", "Message is too long.")
            user_msg = Message.objects.create(
                conversation=c, role=Message.Role.USER, content=content,
                parent=history[-1] if history else None,
            )
            history.append(user_msg)
            new_user = True
        if c.model != model:
            c.model = model
        c.save()  # bumps updated_at so the sidebar re-sorts

    needs_title = not c.title
    provider = llm.get_provider()
    api_messages = [{"role": m.role, "content": m.content} for m in history if m.content]
    assistant_id = uuid.uuid4()

    def stream():
        if new_user:
            yield sse("user_message", msg_json(user_msg))
        yield sse("message_start", {"id": str(assistant_id), "model": model})
        parts, result, state = [], llm.StreamResult(), {"status": "cancelled", "error": None}
        try:
            for chunk in provider.stream(model, llm.SYSTEM_PROMPT, api_messages, result):
                parts.append(chunk)
                yield sse("delta", {"text": chunk})
            state["status"] = "done"
        except GeneratorExit:  # client pressed Stop / closed the tab
            raise
        except Exception as exc:  # noqa: BLE001 — surfaced to the UI, never crashes the stream
            log.warning("console stream failed: %s: %s", type(exc).__name__, exc)
            state["status"] = "error"
            state["error"] = friendly_error(exc)
        finally:
            Message.objects.create(
                id=assistant_id, conversation=c, parent=user_msg,
                role=Message.Role.ASSISTANT, content="".join(parts), model=model,
                stop_reason=result.stop_reason or ("user_cancelled" if state["status"] == "cancelled" else state["status"]),
                input_tokens=result.input_tokens, output_tokens=result.output_tokens,
            )
        if state["error"]:
            yield sse("error", state["error"])
        yield sse("message_stop", {"id": str(assistant_id), "stop_reason": result.stop_reason})
        if needs_title and state["status"] == "done":
            c.title = provider.title(user_msg.content)
            c.save(update_fields=["title", "updated_at"])
            yield sse("conversation_title", {"id": str(c.id), "title": c.title})

    resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"  # nginx/Traefik: don't buffer the stream
    return resp


def friendly_error(exc):
    name = type(exc).__name__
    if "credit balance" in str(exc).lower():
        return {"type": "billing_error", "message": "The Anthropic account has no API credit left. Top up under Plans & Billing in the Anthropic Console, or run with LLM_PROVIDER=fake."}
    messages = {
        "OverloadedError": "Claude is temporarily overloaded. Please try again in a moment.",
        "RateLimitError": "Rate limit reached. Please wait a moment and try again.",
        "AuthenticationError": "The API key is invalid. Check ANTHROPIC_API_KEY in backend/.env.",
        "NotFoundError": "This model is not available for the configured API key.",
        "APIConnectionError": "Could not reach the model provider. Check the network and retry.",
    }
    return {"type": name, "message": messages.get(name, "Something went wrong while generating the reply.")}
