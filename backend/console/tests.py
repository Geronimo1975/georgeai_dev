"""Console API tests — always on the offline fake provider (prompts 09.02 / 09.06)."""
import json
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Conversation, Message

API = "/api/console/v1"


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

    def test_regenerate_replaces_last_reply(self):
        c = self.client.post(f"{API}/conversations", "{}", content_type="application/json").json()
        self.stream(c["id"], {"content": "Hi"})
        events = self.stream(c["id"], {"regenerate": True})
        self.assertNotIn("user_message", events)
        self.assertEqual(Message.objects.filter(conversation_id=c["id"]).count(), 2)

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
