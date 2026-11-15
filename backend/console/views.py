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
from django.db import connection, transaction
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


def msg_json(m, siblings=None):
    return {
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
        return [msg_json(m, self.siblings(m)) for m in self.path(leaf)]


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
        "models": llm.catalog(),
        "default_model": llm.DEFAULT_MODEL,
        "provider": llm.get_provider(llm.DEFAULT_MODEL).name,
        "conversations": [conv_json(c) for c in convs],
    })


@api_login_required
@require_http_methods(["GET", "POST"])
def conversations(request):
    if request.method == "POST":
        data = body(request)
        model = data.get("model") if data.get("model") in llm.available_model_ids() else llm.DEFAULT_MODEL
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
        if data.get("model") in llm.available_model_ids():
            c.model = data["model"]
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
    model = requested or c.model or llm.DEFAULT_MODEL
    content = str(data.get("content", "")).strip()

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
        c.save()  # bumps updated_at so the sidebar re-sorts

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
