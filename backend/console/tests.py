import uuid
"""Console API tests — always on the offline fake provider (prompts 09.02 / 09.06)."""
import json
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .models import Conversation, Message, MessageFeedback, Style

API = "/api/console/v1"


# CI runs with DEBUG=False, which turns SECURE_SSL_REDIRECT on and 301s every
# plain-http test request (same reason as accounts/tests.py).
@override_settings(SECURE_SSL_REDIRECT=False)
@mock.patch.dict(os.environ, {"LLM_PROVIDER": "fake"})
@mock.patch("console.llm.time.sleep", lambda s: None)
class ConsoleApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="a@example.com", password="pw-123456!")
        self.other = User.objects.create_user(email="b@example.com", password="pw-123456!")
        self.client.force_login(self.user)

    def stream(self, conv_id, payload):
        r = self.client.post(f"{API}/conversations/{conv_id}/messages", json.dumps(payload),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200, getattr(r, "content", b""))
        body = b"".join(r.streaming_content).decode()
        return [line[7:] for line in body.splitlines() if line.startswith("event: ")]

    def test_anonymous_gets_401(self):
        self.client.logout()
        self.assertEqual(self.client.get(f"{API}/bootstrap").status_code, 401)

    def test_bootstrap(self):
        data = self.client.get(f"{API}/bootstrap").json()
        self.assertEqual(data["user"]["email"], "a@example.com")
        self.assertEqual(data["provider"], "fake")
        self.assertTrue(data["models"])

    def test_send_streams_saves_and_titles(self):
        c = self.client.post(f"{API}/conversations", "{}", content_type="application/json").json()
        events = self.stream(c["id"], {"content": "Hello there"})
        self.assertEqual(events[0], "user_message")
        self.assertIn("delta", events)
        self.assertIn("message_stop", events)
        self.assertEqual(events[-1], "conversation_title")
        conv = Conversation.objects.get(pk=c["id"])
        self.assertEqual(conv.title, "Hello there")
        roles = list(conv.messages.values_list("role", flat=True))
        self.assertEqual(roles, ["user", "assistant"])
        self.assertTrue(conv.messages.get(role="assistant").content)

    def test_regenerate_adds_sibling_reply(self):
        c = self.client.post(f"{API}/conversations", "{}", content_type="application/json").json()
        self.stream(c["id"], {"content": "Hi"})
        events = self.stream(c["id"], {"regenerate": True})
        self.assertNotIn("user_message", events)
        self.assertEqual(Message.objects.filter(conversation_id=c["id"]).count(), 3)
        path = self.detail(c["id"])["messages"]
        self.assertEqual([m["role"] for m in path], ["user", "assistant"])
        self.assertEqual(len(path[1]["siblings"]), 2)
        self.assertEqual(path[1]["siblings"][-1], path[1]["id"])  # newest is shown

    # ---------------------------------------------------------------- branches (02.07)

    def detail(self, conv_id):
        return self.client.get(f"{API}/conversations/{conv_id}").json()

    def sent_history(self, conv_id, payload):
        """Run a turn and capture the messages actually sent to the model."""
        from . import llm

        seen = {}
        real = llm.FakeProvider.stream

        def spy(provider, model, system, messages, result):
            seen["messages"] = [m["content"] for m in messages]
            yield from real(provider, model, system, messages, result)

        with mock.patch.object(llm.FakeProvider, "stream", spy):
            self.stream(conv_id, payload)
        return seen["messages"]

    def test_three_levels_of_branches_send_only_the_active_path(self):
        c = Conversation.objects.create(owner=self.user)
        cid = str(c.id)
        self.stream(cid, {"content": "A1"})
        self.stream(cid, {"content": "B1"})
        self.stream(cid, {"content": "C1"})
        path = self.detail(cid)["messages"]
        a1, b1, c1 = path[0]["id"], path[2]["id"], path[4]["id"]

        # level 1: edit A1 -> fresh branch with nothing below it
        sent = self.sent_history(cid, {"content": "A2", "edit_of": a1})
        self.assertEqual(sent, ["A2"])
        path = self.detail(cid)["messages"]
        self.assertEqual([m["content"] for m in path if m["role"] == "user"], ["A2"])
        self.assertEqual(len(path[0]["siblings"]), 2)

        # back to the A1 branch: lands on its newest leaf (C1's reply)
        r = self.client.post(f"{API}/conversations/{cid}/branch", json.dumps({"message_id": a1}),
                             content_type="application/json").json()
        self.assertEqual([m["content"] for m in r["messages"] if m["role"] == "user"], ["A1", "B1", "C1"])

        # level 2: edit B1 on that branch
        sent = self.sent_history(cid, {"content": "B2", "edit_of": b1})
        self.assertEqual([x for x in sent if not x.startswith("**Demo")], ["A1", "B2"])

        # level 3: back to B1, edit C1
        self.client.post(f"{API}/conversations/{cid}/branch", json.dumps({"message_id": b1}),
                         content_type="application/json")
        sent = self.sent_history(cid, {"content": "C2", "edit_of": c1})
        self.assertEqual([x for x in sent if not x.startswith("**Demo")], ["A1", "B1", "C2"])
        path = self.detail(cid)["messages"]
        self.assertEqual([m["content"] for m in path if m["role"] == "user"], ["A1", "B1", "C2"])
        self.assertEqual([len(m["siblings"]) for m in path if m["role"] == "user"], [2, 2, 2])

        # regenerate the C2 reply: 2 replies at that slot, history unchanged
        sent = self.sent_history(cid, {"regenerate": True})
        self.assertEqual([x for x in sent if not x.startswith("**Demo")], ["A1", "B1", "C2"])
        self.assertEqual(len(self.detail(cid)["messages"][-1]["siblings"]), 2)

    def test_branch_rejects_foreign_message(self):
        mine = Conversation.objects.create(owner=self.user)
        theirs = Conversation.objects.create(owner=self.other)
        foreign = Message.objects.create(conversation=theirs, role="user", content="secret")
        r = self.client.post(f"{API}/conversations/{mine.id}/branch", json.dumps({"message_id": str(foreign.id)}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 404)
        r = self.client.post(f"{API}/conversations/{mine.id}/messages",
                             json.dumps({"content": "x", "edit_of": str(foreign.id)}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 404)

    # ---------------------------------------------------------------- search (02.09)

    def test_search_finds_messages_and_respects_ownership(self):
        mine = Conversation.objects.create(owner=self.user, title="Invoices")
        Message.objects.create(conversation=mine, role="user", content="How do I configure the gunicorn workers?")
        theirs = Conversation.objects.create(owner=self.other, title="gunicorn secrets")
        Message.objects.create(conversation=theirs, role="user", content="gunicorn workers for b")
        data = self.client.get(f"{API}/search", {"q": "gunicorn"}).json()
        ids = [r["conversation"]["id"] for r in data["results"]]
        self.assertEqual(ids, [str(mine.id)])
        self.assertIn("\x02", data["results"][0]["snippet"])
        self.assertEqual(self.client.get(f"{API}/search", {"q": "invoices"}).json()["results"][0]["message_id"], None)
        self.assertEqual(self.client.get(f"{API}/search", {"q": "x"}).json()["results"], [])

    def test_other_users_conversation_is_404(self):
        theirs = Conversation.objects.create(owner=self.other)
        for method in ("get", "patch", "delete"):
            r = getattr(self.client, method)(f"{API}/conversations/{theirs.id}", content_type="application/json")
            self.assertEqual(r.status_code, 404, method)
        r = self.client.post(f"{API}/conversations/{theirs.id}/messages", json.dumps({"content": "x"}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 404)

    def test_patch_and_delete(self):
        c = Conversation.objects.create(owner=self.user)
        r = self.client.patch(f"{API}/conversations/{c.id}", json.dumps({"title": "Renamed", "is_starred": True}),
                              content_type="application/json")
        self.assertEqual(r.json()["title"], "Renamed")
        self.assertTrue(r.json()["is_starred"])
        self.assertEqual(self.client.delete(f"{API}/conversations/{c.id}").status_code, 204)
        self.assertFalse(Conversation.objects.filter(pk=c.id).exists())

    def test_empty_message_rejected(self):
        c = Conversation.objects.create(owner=self.user)
        r = self.client.post(f"{API}/conversations/{c.id}/messages", json.dumps({"content": "  "}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_page_requires_login(self):
        self.client.logout()
        r = self.client.get("/console/")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/console/login/"))


# ------------------------------------------------------------------ preferences, styles, feedback

@override_settings(SECURE_SSL_REDIRECT=False)
@mock.patch.dict(os.environ, {"LLM_PROVIDER": "fake"})
@mock.patch("console.llm.time.sleep", lambda s: None)
class PreferencesStylesFeedbackTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="p@example.com", password="pw-123456!")
        self.other = User.objects.create_user(email="q@example.com", password="pw-123456!")
        self.client.force_login(self.user)

    def patch(self, url, data):
        return self.client.patch(url, json.dumps(data), content_type="application/json")

    def post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type="application/json")

    def captured_system(self, conv_id, payload):
        from . import llm

        seen, real = {}, llm.FakeProvider.stream

        def spy(provider, model, system, messages, result):
            seen["system"] = system
            yield from real(provider, model, system, messages, result)

        with mock.patch.object(llm.FakeProvider, "stream", spy):
            r = self.post(f"{API}/conversations/{conv_id}/messages", payload)
            b"".join(r.streaming_content)
        return seen["system"]

    def test_preferences_roundtrip_and_validation(self):
        r = self.client.get(f"{API}/me/preferences").json()
        self.assertEqual(r["theme"], "dark")
        self.assertTrue(r["send_with_enter"])
        r = self.patch(f"{API}/me/preferences", {"name": "George", "theme": "light", "send_with_enter": False,
                                                 "personal_instructions": "I run a B2B agency in Munich."})
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["name"], r.json()["theme"], r.json()["send_with_enter"]), ("George", "light", False))
        bad = self.patch(f"{API}/me/preferences", {"theme": "neon", "personal_instructions": "x" * 4001})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(set(bad.json()["error"]["fields"]), {"theme", "personal_instructions"})
        self.assertEqual(self.client.get(f"{API}/me/preferences").json()["theme"], "light")  # nothing half-saved

    def test_review_fixes_types_fallbacks_and_foreign_styles(self):
        from .models import Conversation, Message, Style
        # send_with_enter must be a JSON boolean; rating must not be a bool.
        bad = self.patch(f"{API}/me/preferences", {"send_with_enter": "false"})
        self.assertEqual(bad.status_code, 400)
        self.assertIn("send_with_enter", bad.json()["error"]["fields"])
        # A deleted / unknown style falls back to the default instead of 404ing the create.
        r = self.post(f"{API}/conversations", {"style_id": str(uuid.uuid4())})
        self.assertEqual(r.status_code, 201)
        conv_id = r.json()["id"]
        # A bad style id on send fails *before* the user turn is saved.
        r = self.post(f"{API}/conversations/{conv_id}/messages", {"content": "hi", "style_id": str(uuid.uuid4())})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(Message.objects.filter(conversation_id=conv_id).count(), 0)
        # Another user's style attached by hand is never used in the prompt.
        foreign = Style.objects.create(owner=self.other, name="Pirate", prompt="ARRR-SECRET")
        Conversation.objects.filter(pk=conv_id).update(style=foreign)
        self.assertNotIn("ARRR-SECRET", self.captured_system(conv_id, {"content": "hello"}))
        from django.core.exceptions import ValidationError
        c = Conversation.objects.get(pk=conv_id)
        with self.assertRaises(ValidationError):
            c.clean()
        reply = Message.objects.filter(conversation_id=conv_id, role="assistant").first()
        self.assertEqual(self.post(f"{API}/messages/{reply.id}/feedback", {"rating": True}).status_code, 400)

    def test_personal_instructions_and_style_reach_the_system_prompt(self):
        self.patch(f"{API}/me/preferences", {"personal_instructions": "Answer in Romanian."})
        concise = Style.objects.get(owner=None, key="concise")
        c = self.post(f"{API}/conversations", {}).json()
        system = self.captured_system(c["id"], {"content": "Hi", "style_id": str(concise.id)})
        self.assertIn("Answer in Romanian.", system)
        self.assertIn("Keep answers short", system)
        self.assertTrue(system.startswith(llm_base()))  # stable prefix stays first for caching
        self.assertEqual(Conversation.objects.get(pk=c["id"]).style, concise)

    def test_custom_style_crud_and_ownership(self):
        r = self.post(f"{API}/styles", {"name": "Pirate", "prompt": "Talk like a pirate."})
        self.assertEqual(r.status_code, 201)
        sid = r.json()["id"]
        self.assertEqual(self.patch(f"{API}/styles/{sid}", {"name": "Captain"}).json()["name"], "Captain")
        self.assertEqual(self.post(f"{API}/styles", {"name": "", "prompt": ""}).status_code, 400)
        preset = Style.objects.get(owner=None, key="formal")
        self.assertEqual(self.patch(f"{API}/styles/{preset.id}", {"name": "x"}).status_code, 403)
        theirs = Style.objects.create(owner=self.other, name="Secret", prompt="x")
        self.assertEqual(self.client.delete(f"{API}/styles/{theirs.id}").status_code, 404)
        c = self.post(f"{API}/conversations", {}).json()
        self.assertEqual(self.patch(f"{API}/conversations/{c['id']}", {"style_id": str(theirs.id)}).status_code, 404)
        names = [s["name"] for s in self.client.get(f"{API}/bootstrap").json()["styles"]]
        self.assertEqual(names[:4], ["Normal", "Concise", "Explanatory", "Formal"])
        self.assertIn("Captain", names)
        self.assertNotIn("Secret", names)
        self.assertEqual(self.client.delete(f"{API}/styles/{sid}").status_code, 204)

    def test_default_style_and_model_apply_to_new_chats(self):
        formal = Style.objects.get(owner=None, key="formal")
        self.patch(f"{API}/me/preferences", {"default_style_id": str(formal.id), "default_model": "claude-opus-5-5"})
        c = self.post(f"{API}/conversations", {}).json()
        self.assertEqual((c["style_id"], c["model"]), (str(formal.id), "claude-opus-5-5"))

    def test_feedback_set_change_clear_and_ownership(self):
        c = self.post(f"{API}/conversations", {}).json()
        b"".join(self.post(f"{API}/conversations/{c['id']}/messages", {"content": "Hi"}).streaming_content)
        reply = Message.objects.get(conversation_id=c["id"], role="assistant")
        url = f"{API}/messages/{reply.id}/feedback"
        self.assertEqual(self.post(url, {"rating": -1, "comment": "Too long"}).json()["rating"], -1)
        self.assertEqual(self.client.get(f"{API}/conversations/{c['id']}").json()["messages"][-1]["rating"], -1)
        self.assertEqual(self.post(url, {"rating": 1}).json()["comment"], "")
        self.assertEqual(MessageFeedback.objects.count(), 1)
        self.assertEqual(self.post(url, {"rating": 0}).json()["rating"], 0)
        self.assertFalse(MessageFeedback.objects.exists())
        self.assertEqual(self.post(url, {"rating": 5}).status_code, 400)
        user_msg = Message.objects.get(conversation_id=c["id"], role="user")
        self.assertEqual(self.post(f"{API}/messages/{user_msg.id}/feedback", {"rating": 1}).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.post(url, {"rating": 1}).status_code, 404)


def llm_base():
    from . import llm

    return llm.SYSTEM_PROMPT.rstrip()


# ------------------------------------------------------------------ DeepSeek vendor

def _deepseek_transport(seen, status=200, truncate=False):
    """httpx MockTransport speaking the OpenAI-compatible streaming protocol."""
    import httpx

    def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        if status != 200:
            return httpx.Response(status, json={"error": {"message": "nope"}})
        if not body.get("stream"):  # title call
            return httpx.Response(200, json={"choices": [{"message": {"content": "DeepSeek Title"}}]})
        chunks = [
            {"choices": [{"delta": {"reasoning_content": "thinking…"}}]},
            {"choices": [{"delta": {"content": "Hello "}}]},
            {"choices": [{"delta": {"content": "from DeepSeek"}, "finish_reason": "stop"}]},
            {"choices": [], "usage": {"prompt_tokens": 12, "completion_tokens": 4}},
        ]
        sse_body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks[: 2 if truncate else None])
        if not truncate:
            sse_body += "data: [DONE]\n\n"
        return httpx.Response(200, content=sse_body.encode(), headers={"content-type": "text/event-stream"})

    return httpx.MockTransport(handler)


@override_settings(SECURE_SSL_REDIRECT=False, DEEPSEEK_API_KEY="test-key",
                   DEEPSEEK_BASE_URL="https://eu.example.test/v1", ANTHROPIC_API_KEY="")
@mock.patch.dict(os.environ, {"LLM_PROVIDER": "auto"})
class DeepSeekProviderTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="d@example.com", password="pw-123456!")
        self.client.force_login(self.user)
        self.seen = []

    def run_turn(self, status=200, truncate=False):
        import httpx

        real = httpx.Client
        transport = _deepseek_transport(self.seen, status, truncate)

        def client(*args, **kwargs):
            kwargs["transport"] = transport
            return real(*args, **kwargs)

        c = Conversation.objects.create(owner=self.user)
        with mock.patch("httpx.Client", client):
            r = self.client.post(f"{API}/conversations/{c.id}/messages",
                                 json.dumps({"content": "Hi", "model": "deepseek-chat"}),
                                 content_type="application/json")
            body = b"".join(r.streaming_content).decode()
        return c, body

    def test_catalog_lists_deepseek_with_data_note(self):
        models = {m["id"]: m for m in self.client.get(f"{API}/bootstrap").json()["models"]}
        self.assertTrue(models["deepseek-chat"]["live"])
        self.assertFalse(models["claude-sonnet-5-5"]["live"])  # no Anthropic key here
        self.assertIn("eu.example.test", models["deepseek-chat"]["data_note"])

    @override_settings(DEEPSEEK_API_KEY="")
    def test_deepseek_hidden_without_key(self):
        ids = [m["id"] for m in self.client.get(f"{API}/bootstrap").json()["models"]]
        self.assertNotIn("deepseek-chat", ids)

    def test_streams_reply_usage_and_title(self):
        c, body = self.run_turn()
        reply = Message.objects.get(conversation=c, role="assistant")
        self.assertEqual(reply.content, "Hello from DeepSeek")  # reasoning not stored
        self.assertEqual((reply.input_tokens, reply.output_tokens), (12, 4))
        self.assertEqual(reply.stop_reason, "end_turn")
        self.assertEqual(reply.model, "deepseek-chat")
        c.refresh_from_db()
        self.assertEqual(c.title, "DeepSeek Title")
        sent = self.seen[0]
        self.assertEqual(sent["messages"][0]["role"], "system")
        self.assertEqual(sent["messages"][-1], {"role": "user", "content": "Hi"})

    def test_insufficient_balance_is_explained(self):
        c, body = self.run_turn(status=402)
        self.assertIn("event: error", body)
        self.assertIn("no balance", body)
        self.assertEqual(Message.objects.get(conversation=c, role="assistant").stop_reason, "error")

    def test_cut_stream_is_an_error_not_a_finished_reply(self):
        c, body = self.run_turn(truncate=True)
        self.assertIn("cut off", body)
        self.assertEqual(Message.objects.get(conversation=c, role="assistant").stop_reason, "error")

    def test_redirect_is_not_success(self):
        c, body = self.run_turn(status=307)
        self.assertIn("event: error", body)

    @mock.patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"})
    def test_anthropic_pin_hides_and_never_routes_to_deepseek(self):
        from . import llm

        ids = [m["id"] for m in self.client.get(f"{API}/bootstrap").json()["models"]]
        self.assertNotIn("deepseek-chat", ids)
        self.assertEqual(llm.get_provider("deepseek-chat").name, "fake")

    @override_settings(DEEPSEEK_BASE_URL="https://api.evil-deepseek.com/v1")
    def test_lookalike_host_is_not_called_deepseek(self):
        note = {m["id"]: m for m in self.client.get(f"{API}/bootstrap").json()["models"]}["deepseek-chat"]["data_note"]
        self.assertEqual(note, "Processed via api.evil-deepseek.com")

    def test_unavailable_saved_model_is_kept_not_swapped(self):
        c = Conversation.objects.create(owner=self.user, model="deepseek-chat")
        with self.settings(DEEPSEEK_API_KEY=""):
            r = self.client.post(f"{API}/conversations/{c.id}/messages", json.dumps({"content": "Hi"}),
                                 content_type="application/json")
        self.assertEqual(r.status_code, 409)
        c.refresh_from_db()
        self.assertEqual(c.model, "deepseek-chat")
        self.assertFalse(c.messages.exists())


class HostLanguageTests(TestCase):
    """georgeai.de serves German, georgeai.dev (and anything else) English."""

    def test_language_for_host(self):
        from .middleware import language_for_host
        self.assertEqual(language_for_host("georgeai.de"), "de")
        self.assertEqual(language_for_host("www.georgeai.de:443"), "de")
        self.assertEqual(language_for_host("georgeai.dev"), "en")
        self.assertEqual(language_for_host("evilgeorgeai.de"), "en")

    @override_settings(ALLOWED_HOSTS=["georgeai.de", "georgeai.dev"], SECURE_SSL_REDIRECT=False)
    def test_admin_login_is_german_on_de(self):
        de = self.client.get("/admin/login/", HTTP_HOST="georgeai.de")
        en = self.client.get("/admin/login/", HTTP_HOST="georgeai.dev")
        self.assertEqual(de["Content-Language"], "de")
        self.assertContains(de, "Passwort")
        self.assertEqual(en["Content-Language"], "en")
        self.assertContains(en, "Password")


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver", "georgeai.de", "georgeai.dev"],
                   EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordlessLoginTests(TestCase):
    def code_from_mail(self):
        import re
        from django.core import mail
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    def start(self, email, nxt="/console/"):
        r = self.client.post("/console/login/", {"email": email, "next": nxt})
        self.assertEqual(r.status_code, 302, r.content[:200])
        self.assertTrue(r["Location"].startswith("/console/login/code/?a="))
        return r["Location"].split("?a=", 1)[1]

    def verify(self, token, code):
        return self.client.post("/console/login/code/", {"a": token, "code": code})

    def test_signup_and_login_with_emailed_code(self):
        from django.core import mail
        from .auth_views import code_hash
        from .models import LoginCode
        token = self.start("New.Lead@Example.com", "/console/new")
        self.assertEqual(mail.outbox[-1].to, ["new.lead@example.com"])
        code = self.code_from_mail()
        self.assertEqual(LoginCode.objects.get().code_hash, code_hash("new.lead@example.com", code))  # keyed HMAC
        r = self.verify(token, code)
        self.assertRedirects(r, "/console/new", fetch_redirect_response=False)
        user = get_user_model().objects.get(email="new.lead@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(self.client.get("/api/console/v1/bootstrap").status_code, 200)

    def test_wrong_code_attempts_and_lockout(self):
        token = self.start("a@example.com")
        good = self.code_from_mail()
        bad = "000000" if good != "000000" else "111111"
        for _ in range(5):
            self.assertEqual(self.verify(token, bad).status_code, 400)
        self.assertEqual(self.verify(token, good).status_code, 400)  # locked after 5 misses
        self.assertFalse(get_user_model().objects.filter(email="a@example.com").exists())

    def test_rate_limit_keeps_next_and_blocks_open_redirect(self):
        for _ in range(3):
            self.start("b@example.com", "https://evil.example/")
        r = self.client.post("/console/login/", {"email": "b@example.com", "next": "/console/new"})
        self.assertEqual(r.status_code, 429)
        self.assertContains(r, 'value="/console/new"', status_code=429)  # destination survives the error
        token = self.start("c@example.com", "https://evil.example/")
        self.assertEqual(self.verify(token, self.code_from_mail())["Location"], "/console/")

    def test_failed_delivery_keeps_previous_code(self):
        token = self.start("d@example.com")
        first = self.code_from_mail()
        with mock.patch("console.auth_views.send_mail", side_effect=OSError("smtp down")):
            r = self.client.post("/console/login/code/", {"a": token, "resend": "1"})
        self.assertEqual(r.status_code, 503)
        self.assertRedirects(self.verify(token, first), "/console/", fetch_redirect_response=False)

    def test_tampered_token_and_ambiguous_case(self):
        self.assertRedirects(self.client.get("/console/login/code/?a=forged"), "/console/login/",
                             fetch_redirect_response=False)
        User = get_user_model()
        User.objects.create_user(email="Mixed@example.com", password="x-12345678")
        User.objects.create_user(email="mixed@example.com", password="x-12345678")
        token = self.start("mixed@example.com")
        self.assertEqual(self.verify(token, self.code_from_mail()).status_code, 400)

    @override_settings(DEBUG=False, EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_no_smtp_in_production_refuses_to_issue(self):
        r = self.client.post("/console/login/", {"email": "e@example.com"})
        self.assertEqual(r.status_code, 503)
        from .models import LoginCode
        self.assertFalse(LoginCode.objects.exists())

    def test_landing_and_signin_language_by_host(self):
        de = self.client.get("/", HTTP_HOST="georgeai.de")
        en = self.client.get("/", HTTP_HOST="georgeai.dev")
        self.assertContains(de, 'lang="de"')
        self.assertContains(de, "Zur Konsole")
        self.assertContains(en, 'lang="en"')
        self.assertContains(en, "Open the console")
        self.assertContains(self.client.get("/console/login/", HTTP_HOST="georgeai.de"), "Code per E-Mail senden")

