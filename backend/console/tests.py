"""Console API tests — always on the offline fake provider (prompts 09.02 / 09.06)."""
import json
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .models import Conversation, Message

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


# ------------------------------------------------------------------ DeepSeek vendor

def _deepseek_transport(seen, status=200):
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
        sse_body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
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

    def run_turn(self, status=200):
        import httpx

        real = httpx.Client
        transport = _deepseek_transport(self.seen, status)

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
