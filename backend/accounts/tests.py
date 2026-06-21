from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

User = get_user_model()
PW = "sup3r-secret-pw"


class AuthFlowTests(APITestCase):
    def test_signup_creates_user_and_session(self):
        r = self.client.post(
            "/api/auth/signup",
            {"name": "Tester", "email": "Tester@Ex.com", "password": PW},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["authenticated"])
        self.assertEqual(r.data["email"], "tester@ex.com")  # normalised
        self.assertTrue(User.objects.filter(email="tester@ex.com").exists())
        self.assertTrue(self.client.get("/api/auth/me").data["authenticated"])

    def test_duplicate_email(self):
        User.objects.create_user(email="a@b.com", password=PW)
        r = self.client.post(
            "/api/auth/signup", {"email": "a@b.com", "password": PW}, format="json"
        )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["error"], "email_taken")

    def test_weak_password(self):
        r = self.client.post(
            "/api/auth/signup", {"email": "w@b.com", "password": "123"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["error"], "weak_password")

    def test_login_then_logout(self):
        User.objects.create_user(email="c@d.com", password=PW, name="Cee")
        r = self.client.post(
            "/api/auth/login", {"email": "C@D.com", "password": PW}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.client.get("/api/auth/me").data["authenticated"])
        self.client.post("/api/auth/logout", {}, format="json")
        self.assertFalse(self.client.get("/api/auth/me").data["authenticated"])

    def test_wrong_password(self):
        User.objects.create_user(email="e@f.com", password=PW)
        r = self.client.post(
            "/api/auth/login", {"email": "e@f.com", "password": "nope"}, format="json"
        )
        self.assertEqual(r.status_code, 401)

    def test_csrf_enforced_on_anonymous_post(self):
        client = APIClient(enforce_csrf_checks=True)
        r = client.post(
            "/api/auth/login", {"email": "x@y.z", "password": "p"}, format="json"
        )
        self.assertEqual(r.status_code, 403)
