"""GeorgeAI Console API + page (prompts 01.11, 02.03–02.08, 04.01).

Plain Django views returning JSON: the streaming endpoint needs a raw
StreamingHttpResponse anyway, and CsrfViewMiddleware protects every unsafe
method with the same csrftoken cookie auth.js already uses.
"""
import json
import logging
import uuid
from functools import wraps

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.db.models import Q
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from . import llm
from .models import Conversation, Message, MessageFeedback, Style, UserPreference, style_usable_by

MAX_MESSAGE_CHARS = 100_000
MAX_STYLES = 50
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
        "style_id": str(c.style_id) if c.style_id else None,
        "updated_at": c.updated_at.isoformat(),
    }


def msg_json(m, siblings=None, rating=0):
    return {
        "rating": rating,
        "id": str(m.id),
        "parent_id": str(m.parent_id) if m.parent_id else None,
        "siblings": [str(x) for x in siblings] if siblings else [str(m.id)],
        "role": m.role,
        "content": m.content,
        "model": m.model,
        "stop_reason": m.stop_reason,
        "created_at": m.created_at.isoformat(),
    }


class Tree:
    """All messages of one conversation, loaded in a single query (02.07).

    ``path(leaf)`` walks parents back to the root; ``siblings(m)`` lists the
    alternatives at that position (edits of a user turn, regenerations of a
    reply) oldest first — what the "< 2/3 >" control pages through.
    """

    def __init__(self, conversation):
        self.conversation = conversation
        self.msgs = list(conversation.messages.all())  # ordered by created_at
        self.by_id = {m.id: m for m in self.msgs}
        self.ratings = dict(MessageFeedback.objects.filter(
            message__conversation=conversation, user_id=conversation.owner_id,
        ).values_list("message_id", "rating"))
        self.children = {}
        for m in self.msgs:
            self.children.setdefault(m.parent_id, []).append(m)

    def leaf(self):
        leaf = self.by_id.get(self.conversation.current_leaf_id)
        return leaf or (self.msgs[-1] if self.msgs else None)

    def path(self, leaf=None):
        node, out = (leaf if leaf is not None else self.leaf()), []
        while node is not None:
            out.append(node)
            node = self.by_id.get(node.parent_id)
        return out[::-1]

    def siblings(self, m):
        return [x.id for x in self.children.get(m.parent_id, [])]

    def deepest(self, m):
        """Follow the newest child down — where switching to ``m``'s branch lands."""
        while self.children.get(m.id):
            m = self.children[m.id][-1]
        return m

    def path_json(self, leaf=None):
        return [msg_json(m, self.siblings(m), self.ratings.get(m.id, 0)) for m in self.path(leaf)]


def prefs_for(user):
    return UserPreference.objects.get_or_create(user=user)[0]


def visible_styles(user):
    return Style.objects.filter(Q(owner__isnull=True) | Q(owner=user))


def style_json(s):
    return {"id": str(s.id), "name": s.name, "description": s.description, "prompt": s.prompt,
            "key": s.key, "is_preset": s.is_preset}


def prefs_json(p, user):
    return {
        "name": user.name,
        "default_model": p.default_model,
        "default_style_id": str(p.default_style_id) if p.default_style_id else None,
        "theme": p.theme,
        "language": p.language,
        "personal_instructions": p.personal_instructions,
        "send_with_enter": p.send_with_enter,
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
        "id", "title", "model", "is_starred", "style_id", "updated_at"
    )[:300]
    return JsonResponse({
        "user": {
            "email": u.email,
            "name": getattr(u, "name", "") or u.email.split("@")[0],
            "is_staff": u.is_staff,
        },
        "models": llm.catalog(),
        "default_model": llm.default_model(),
        "provider": llm.get_provider(llm.default_model()).name,
        "conversations": [conv_json(c) for c in convs],
        "preferences": prefs_json(prefs_for(u), u),
        "styles": [style_json(s) for s in visible_styles(u)],
    })


@api_login_required
@require_http_methods(["GET", "POST"])
def conversations(request):
    if request.method == "POST":
        data = body(request)
        prefs = prefs_for(request.user)
        allowed = llm.available_model_ids()
        model = next((m for m in (data.get("model"), prefs.default_model) if m in allowed), llm.default_model())
        # A style deleted in another tab must not block a new chat: fall back
        # to the saved default instead of 404ing the create.
        style = _visible_style(request.user, data.get("style_id")) if data.get("style_id") else None
        if style is None and style_usable_by(prefs.default_style, request.user.id):
            style = prefs.default_style
        c = Conversation.objects.create(owner=request.user, model=model, style=style)
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
        if data.get("model") in llm.available_model_ids():
            c.model = data["model"]
        if "style_id" in data:
            c.style = _own_style(request.user, data["style_id"]) if data["style_id"] else None
        c.save()
        return JsonResponse(conv_json(c))
    return JsonResponse({**conv_json(c), "messages": Tree(c).path_json()})


@api_login_required
@require_http_methods(["POST"])
def switch_branch(request, pk):
    """Show another branch: ``message_id`` is any message, typically a sibling
    picked with "< 2/3 >"; the view lands on that branch's newest leaf."""
    c = own_conversation(request, pk)
    tree = Tree(c)
    try:
        target = tree.by_id.get(uuid.UUID(str(body(request).get("message_id", ""))))
    except ValueError:
        target = None
    if target is None:
        return error(404, "not_found_error", "Message not found in this conversation.")
    leaf = tree.deepest(target)
    Conversation.objects.filter(pk=c.pk).update(current_leaf=leaf)
    return JsonResponse({**conv_json(c), "messages": tree.path_json(leaf)})


@api_login_required
@require_http_methods(["POST"])
def send_message(request, pk):
    """Save the user turn (or regenerate the last reply) and stream the answer as SSE."""
    c = own_conversation(request, pk)
    data = body(request)
    regenerate = bool(data.get("regenerate"))
    allowed = llm.available_model_ids()
    requested = data.get("model") if data.get("model") in allowed else None
    if requested is None and c.model and c.model not in allowed:
        # The chat's model is unavailable right now (its key was removed). Don't
        # silently answer with another vendor and don't overwrite the saved choice.
        return error(409, "model_unavailable",
                     f"{c.model} is not available right now. Pick another model to continue this chat.")
    model = requested or c.model or llm.default_model()
    content = str(data.get("content", "")).strip()

    # Resolve everything that can fail *before* the user turn is committed, so
    # a bad style id never leaves an unanswered message behind.
    style_change = "style_id" in data and data["style_id"] is not None
    if style_change:
        new_style = _own_style(request.user, data["style_id"]) if data["style_id"] else None
    personal = prefs_for(request.user).personal_instructions

    with transaction.atomic():
        tree = Tree(c)
        if regenerate:
            # A new sibling of the reply, not an overwrite: the old one stays
            # reachable through "< 1/2 >". Defaults to the last reply on screen.
            target = tree.by_id.get(_uuid(data.get("message_id"))) if data.get("message_id") else None
            if target is None:
                path = tree.path()
                target = path[-1] if path else None
            if target is not None and target.role == Message.Role.ASSISTANT:
                target = tree.by_id.get(target.parent_id)
            if target is None or target.role != Message.Role.USER:
                return error(400, "invalid_request_error", "Nothing to regenerate.")
            user_msg, new_user = target, False
            history = tree.path(user_msg)
        else:
            if not content:
                return error(400, "invalid_request_error", "Message is empty.")
            if len(content) > MAX_MESSAGE_CHARS:
                return error(400, "invalid_request_error", "Message is too long.")
            if data.get("edit_of"):
                # Editing a user turn forks a new branch from that turn's parent.
                edited = tree.by_id.get(_uuid(data["edit_of"]))
                if edited is None or edited.role != Message.Role.USER:
                    return error(404, "not_found_error", "Message not found in this conversation.")
                parent = tree.by_id.get(edited.parent_id)
            else:
                parent = tree.leaf()
            history = tree.path(parent) if parent else []
            user_msg = Message.objects.create(
                conversation=c, role=Message.Role.USER, content=content, parent=parent,
            )
            history.append(user_msg)
            new_user = True
        c.model = model
        c.current_leaf = user_msg
        if style_change:  # "applied to the next message" (02.11)
            c.style = new_style
        c.save()  # bumps updated_at so the sidebar re-sorts

    # Never another user's prompt, even if an admin attached one by hand.
    style_prompt = c.style.prompt if style_usable_by(c.style, c.owner_id) else ""
    system = llm.build_system(personal, style_prompt)
    needs_title = not c.title
    provider = llm.get_provider(model)
    api_messages = [{"role": m.role, "content": m.content} for m in history if m.content]
    assistant_id = uuid.uuid4()

    def stream():
        if new_user:
            yield sse("user_message", msg_json(user_msg))
        yield sse("message_start", {"id": str(assistant_id), "model": model})
        parts, result, state = [], llm.StreamResult(), {"status": "cancelled", "error": None}
        try:
            for chunk in provider.stream(model, system, api_messages, result):
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
            reply = Message.objects.create(
                id=assistant_id, conversation=c, parent=user_msg,
                role=Message.Role.ASSISTANT, content="".join(parts), model=model,
                stop_reason=result.stop_reason or ("user_cancelled" if state["status"] == "cancelled" else state["status"]),
                input_tokens=result.input_tokens, output_tokens=result.output_tokens,
            )
            Conversation.objects.filter(pk=c.pk).update(current_leaf=reply)
        if state["error"]:
            yield sse("error", state["error"])
        yield sse("message_stop", {"id": str(assistant_id), "stop_reason": result.stop_reason})
        if needs_title and state["status"] == "done":
            c.title = provider.title(user_msg.content)
            Conversation.objects.filter(pk=c.pk).update(title=c.title)
            yield sse("conversation_title", {"id": str(c.id), "title": c.title})

    resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"  # nginx/Traefik: don't buffer the stream
    return resp


def _visible_style(user, style_id):
    """A preset or one of the user's styles, else None."""
    pk = _uuid(style_id)
    return visible_styles(user).filter(pk=pk).first() if pk else None


def _own_style(user, style_id):
    """Like ``_visible_style`` but anything else is a 404."""
    s = _visible_style(user, style_id)
    if s is None:
        raise Http404
    return s


@api_login_required
@require_http_methods(["GET", "PATCH"])
def preferences(request):
    """GET/PATCH /me/preferences (02.10). Unknown fields are ignored; invalid
    values are rejected with a field-level message the settings UI shows."""
    p, u = prefs_for(request.user), request.user
    if request.method == "PATCH":
        data, errors, changed = body(request), {}, set()
        if "name" in data:
            name = str(data["name"]).strip()
            if len(name) > 150:
                errors["name"] = "Keep the name under 150 characters."
            else:
                u.name = name
        if "default_model" in data:
            if data["default_model"] in ("", None) or data["default_model"] in llm.available_model_ids():
                p.default_model = data["default_model"] or ""
                changed.add("default_model")
            else:
                errors["default_model"] = "That model is not available."
        if "default_style_id" in data:
            try:
                p.default_style = _own_style(u, data["default_style_id"]) if data["default_style_id"] else None
                changed.add("default_style")
            except Http404:
                errors["default_style_id"] = "That style does not exist."
        if "theme" in data:
            if data["theme"] in UserPreference.Theme.values:
                p.theme = data["theme"]
                changed.add("theme")
            else:
                errors["theme"] = "Choose system, dark or light."
        if "language" in data:
            if data["language"] in ("", "en", "de", "ro"):
                p.language = data["language"]
                changed.add("language")
            else:
                errors["language"] = "Choose English, Deutsch or Română."
        if "personal_instructions" in data:
            text = str(data["personal_instructions"] or "")
            if len(text) > 4000:
                errors["personal_instructions"] = "Keep it under 4,000 characters."
            else:
                p.personal_instructions = text
                changed.add("personal_instructions")
        if "send_with_enter" in data:
            if isinstance(data["send_with_enter"], bool):
                p.send_with_enter = data["send_with_enter"]
                changed.add("send_with_enter")
            else:
                errors["send_with_enter"] = "Must be true or false."
        if errors:
            return JsonResponse({"error": {"type": "invalid_request_error", "message": "Some settings are invalid.",
                                           "fields": errors}}, status=400)
        # One transaction, and only the fields this request touched, so a
        # concurrent PATCH of other fields isn't overwritten with stale values.
        with transaction.atomic():
            if "name" in data:
                u.save(update_fields=["name"])
            if changed:
                p.save(update_fields=[*changed, "updated_at"])
    return JsonResponse(prefs_json(p, u))


def _style_fields(data, s, errors):
    """Apply the posted fields to ``s``; returns the names it changed."""
    changed = [f for f in ("name", "description", "prompt") if f in data]
    if "name" in data:
        name = str(data["name"] or "").strip()
        if not name or len(name) > 60:
            errors["name"] = "Give the style a name of up to 60 characters."
        s.name = name[:60]
    if "description" in data:
        s.description = str(data["description"] or "").strip()[:160]
    if "prompt" in data:
        text = str(data["prompt"] or "").strip()
        if not text or len(text) > 4000:
            errors["prompt"] = "Describe the style in up to 4,000 characters."
        s.prompt = text[:4000]
    return changed


@api_login_required
@require_http_methods(["GET", "POST"])
def styles(request):
    if request.method == "POST":
        data, errors = body(request), {}
        s = Style(owner=request.user)
        _style_fields({"name": "", "prompt": "", **data}, s, errors)
        if errors:
            return JsonResponse({"error": {"type": "invalid_request_error", "message": "The style is incomplete.",
                                           "fields": errors}}, status=400)
        with transaction.atomic():
            # Lock the user row so two concurrent creates can't both pass the cap.
            get_user_model().objects.select_for_update().filter(pk=request.user.pk).first()
            if Style.objects.filter(owner=request.user).count() >= MAX_STYLES:
                return error(400, "invalid_request_error", f"You can keep up to {MAX_STYLES} custom styles.")
            s.save()
        return JsonResponse(style_json(s), status=201)
    return JsonResponse({"data": [style_json(s) for s in visible_styles(request.user)]})


@api_login_required
@require_http_methods(["PATCH", "DELETE"])
def style_detail(request, pk):
    s = _own_style(request.user, pk)
    if s.is_preset:
        return error(403, "permission_error", "Preset styles can't be changed. Create your own instead.")
    if request.method == "DELETE":
        s.delete()
        return JsonResponse({}, status=204)
    errors = {}
    changed = _style_fields(body(request), s, errors)
    if errors:
        return JsonResponse({"error": {"type": "invalid_request_error", "message": "The style is incomplete.",
                                       "fields": errors}}, status=400)
    if changed:
        s.save(update_fields=changed)
    return JsonResponse(style_json(s))


@api_login_required
@require_http_methods(["POST"])
def message_feedback(request, pk):
    """👍/👎 (+ optional comment) on one of the user's assistant replies; rating 0 clears it."""
    try:
        m = Message.objects.get(pk=pk, conversation__owner=request.user, role=Message.Role.ASSISTANT)
    except Message.DoesNotExist:
        raise Http404
    data = body(request)
    rating = data.get("rating")
    if isinstance(rating, bool) or rating not in (1, -1, 0):
        return error(400, "invalid_request_error", "rating must be 1, -1 or 0.")
    if rating == 0:
        MessageFeedback.objects.filter(message=m, user=request.user).delete()
        return JsonResponse({"message_id": str(m.id), "rating": 0, "comment": ""})
    fb, _ = MessageFeedback.objects.update_or_create(
        message=m, user=request.user,
        defaults={"rating": rating, "comment": str(data.get("comment") or "").strip()[:2000]},
    )
    return JsonResponse({"message_id": str(m.id), "rating": fb.rating, "comment": fb.comment})


def _uuid(value):
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


SEARCH_LIMIT = 30


@api_login_required
@require_http_methods(["GET"])
def search(request):
    """Full-text search over the user's chat titles and messages (02.09).

    PostgreSQL: ``simple``-config tsvector (language-neutral, so EN/DE/RO all
    match) backed by the GIN index from migration 0002, with ts_headline
    snippets. Other backends (local SQLite) fall back to icontains.
    """
    q = request.GET.get("q", "").strip()[:200]
    if len(q) < 2:
        return JsonResponse({"query": q, "results": []})
    msgs = Message.objects.filter(conversation__owner=request.user).select_related("conversation")
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank, SearchVector

        query = SearchQuery(q, config="simple", search_type="websearch")
        vector = SearchVector("content", config="simple")
        msgs = (
            msgs.annotate(rank=SearchRank(vector, query))
            .filter(rank__gt=0)
            .annotate(snippet=SearchHeadline(
                "content", query, config="simple", start_sel="\x02", stop_sel="\x03",
                max_words=24, min_words=8, max_fragments=1,
            ))
            .order_by("-rank", "-created_at")
        )
    else:
        msgs = msgs.filter(content__icontains=q).order_by("-created_at")

    results, seen = [], set()
    for c in Conversation.objects.filter(owner=request.user, title__icontains=q)[:10]:
        seen.add(c.id)
        results.append({"conversation": conv_json(c), "message_id": None, "snippet": ""})
    for m in msgs[: SEARCH_LIMIT * 3]:
        if m.conversation_id in seen:
            continue
        seen.add(m.conversation_id)
        snippet = getattr(m, "snippet", None) or _snippet(m.content, q)
        results.append({"conversation": conv_json(m.conversation), "message_id": str(m.id), "snippet": snippet})
        if len(results) >= SEARCH_LIMIT:
            break
    return JsonResponse({"query": q, "results": results})


def _snippet(text, q, width=90):
    """Fallback highlight, same \x02/\x03 markers as ts_headline (client renders <mark>)."""
    text = " ".join(text.split())
    i = text.lower().find(q.lower())
    if i < 0:
        return text[:width * 2]
    start, end = max(0, i - width), min(len(text), i + len(q) + width)
    return (("…" if start else "") + text[start:i] + "\x02" + text[i:i + len(q)] + "\x03"
            + text[i + len(q):end] + ("…" if end < len(text) else ""))


def friendly_error(exc):
    name = type(exc).__name__
    if name == "ProviderHTTPError":  # OpenAI-compatible vendors (DeepSeek or a custom host)
        code = exc.status_code
        who = "DeepSeek" if llm.is_deepseek_host(exc.host) else exc.host
        return {"type": f"http_{code}", "message": {
            401: f"The API key for {who} is invalid. Check DEEPSEEK_API_KEY in backend/.env.",
            402: f"The {who} account has no balance left. Top it up with that provider.",
            429: "Rate limit reached. Please wait a moment and try again.",
            500: "The model provider had an internal error. Please retry.",
            503: "The model provider is overloaded. Please try again in a moment.",
        }.get(code, f"The model provider returned an error ({code}).")}
    if name == "IncompleteStreamError":
        return {"type": name, "message": "The reply was cut off by the model provider. Please retry."}
    if name in ("ConnectError", "ConnectTimeout", "ReadTimeout", "RemoteProtocolError"):
        return {"type": name, "message": "Could not reach the model provider. Check the network and retry."}
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
