"""Passwordless console sign-in: email -> 6-digit one-time code -> session.

The first successful code for an unknown email creates the account, so signing
in and signing up are the same two steps. Staff keep password login at /admin/
(an admin session also opens the console).

Issuing a code is serialized per email (and per client IP) with a database
lock, and the new code only replaces older ones once its email has actually
been sent: a failed delivery rolls back and leaves the previous code valid.
"""
import hashlib
import hmac
import logging
import secrets
import zlib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError, connection, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .copy import copy_for
from .models import LoginCode

log = logging.getLogger(__name__)

CODES_PER_EMAIL = 3   # per 10 minutes
CODES_PER_IP = 10     # per hour
ATTEMPT_SALT = "console.login.attempt"
ATTEMPT_MAX_AGE = 30 * 60
CONSOLE_BACKEND = "django.core.mail.backends.console.EmailBackend"


class IssueError(Exception):
    def __init__(self, kind):
        self.kind = kind  # "rate" | "send"


def code_hash(email, code):
    msg = f"{email}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


def _client_ip(request):
    # nginx's realip module rewrites $remote_addr from Traefik's X-Forwarded-For
    # and forwards it as X-Real-IP (deploy/nginx.conf).
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


def _safe_next(request, value):
    if value and url_has_allowed_host_and_scheme(value, {request.get_host()}, require_https=request.is_secure()):
        return value
    return "/console/"


def _lock(key):
    """Transaction-scoped lock on Postgres (SQLite serializes writers anyway)."""
    if connection.vendor == "postgresql":
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", [zlib.crc32(key.encode())])


def _issue_code(request, email, t):
    if not settings.DEBUG and settings.EMAIL_BACKEND == CONSOLE_BACKEND:
        log.error("login code not sent: no SMTP configured (EMAIL_HOST is empty)")
        raise IssueError("send")
    now = timezone.now()
    ip = _client_ip(request)
    with transaction.atomic():
        _lock(f"login-email:{email}")
        if ip:
            _lock(f"login-ip:{ip}")
        if LoginCode.objects.filter(email=email, created_at__gte=now - timedelta(minutes=10)).count() >= CODES_PER_EMAIL:
            raise IssueError("rate")
        if ip and LoginCode.objects.filter(ip=ip, created_at__gte=now - timedelta(hours=1)).count() >= CODES_PER_IP:
            raise IssueError("rate")
        LoginCode.objects.filter(created_at__lt=now - timedelta(days=1)).delete()  # keep the table small
        code = f"{secrets.randbelow(10**6):06d}"
        LoginCode.objects.filter(email=email, used_at__isnull=True).update(used_at=now)
        LoginCode.objects.create(email=email, code_hash=code_hash(email, code), ip=ip,
                                 expires_at=now + timedelta(seconds=LoginCode.TTL_SECONDS))
        try:
            send_mail(t["mail_subject"].format(code=code), t["mail_body"].format(code=code),
                      settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        except Exception as exc:  # noqa: BLE001 — rolls back: old code stays valid, quota not spent
            log.error("login code email failed: %s: %s", type(exc).__name__, exc)
            raise IssueError("send") from exc


def _error_response(request, template, ctx, kind, t):
    ctx["error"] = t["err_rate"] if kind == "rate" else t["err_send"]
    return render(request, template, ctx, status=429 if kind == "rate" else 503)


@require_http_methods(["GET", "POST"])
def login_email(request):
    t = copy_for(request)
    nxt = _safe_next(request, request.POST.get("next") or request.GET.get("next"))
    if request.user.is_authenticated:
        return redirect(nxt)
    ctx = {"t": t, "email": "", "error": "", "next": nxt}
    if request.method == "GET":
        return render(request, "console/login.html", ctx)
    email = (request.POST.get("email") or "").strip().lower()
    ctx["email"] = email
    try:
        validate_email(email)
    except ValidationError:
        ctx["error"] = t["err_email"]
        return render(request, "console/login.html", ctx, status=400)
    try:
        _issue_code(request, email, t)
    except IssueError as e:
        return _error_response(request, "console/login.html", ctx, e.kind, t)
    # Per-attempt state travels in a signed token, not the session, so two tabs
    # signing in with different emails can't overwrite each other.
    token = signing.dumps({"e": email, "n": nxt}, salt=ATTEMPT_SALT)
    return redirect(f"{reverse('console_login_code')}?a={token}")


def _user_for(email):
    """The account for a verified email, created on first sign-in. None if the
    address is ambiguous (two accounts differing only by case)."""
    User = get_user_model()
    matches = list(User.objects.filter(email__iexact=email)[:2])
    if len(matches) > 1:
        log.warning("login code: ambiguous accounts for one email; refusing")
        return None
    if matches:
        return matches[0]
    try:
        with transaction.atomic():
            return User.objects.create_user(email=email, password=None)  # unusable password
    except IntegrityError:  # created concurrently (e.g. password signup) — use it
        return User.objects.filter(email__iexact=email).first()


@require_http_methods(["GET", "POST"])
def login_code(request):
    t = copy_for(request)
    token = request.POST.get("a") or request.GET.get("a") or ""
    try:
        attempt = signing.loads(token, salt=ATTEMPT_SALT, max_age=ATTEMPT_MAX_AGE)
        email, nxt = attempt["e"], _safe_next(request, attempt.get("n"))
    except (signing.BadSignature, KeyError, TypeError):
        return redirect("console_login")
    ctx = {"t": t, "email": email, "token": token, "lede": t["code_lede"].format(email=email),
           "error": "", "notice": ""}
    if request.method == "GET":
        return render(request, "console/login_code.html", ctx)
    if request.POST.get("resend"):
        try:
            _issue_code(request, email, t)
        except IssueError as e:
            return _error_response(request, "console/login_code.html", ctx, e.kind, t)
        ctx["notice"] = t["sent_again"]
        return render(request, "console/login_code.html", ctx)
    code = "".join(ch for ch in request.POST.get("code", "") if ch.isdigit())
    user = None
    with transaction.atomic():
        lc = (LoginCode.objects.select_for_update()
              .filter(email=email, used_at__isnull=True, expires_at__gt=timezone.now()).first())
        if lc is None:
            ctx["error"] = t["err_code"]
        elif lc.attempts >= LoginCode.MAX_ATTEMPTS:
            ctx["error"] = t["err_attempts"]
        elif len(code) == 6 and hmac.compare_digest(lc.code_hash, code_hash(email, code)):
            lc.used_at = timezone.now()
            lc.save(update_fields=["used_at"])
            user = _user_for(email)
        else:
            lc.attempts += 1
            lc.save(update_fields=["attempts"])
            ctx["error"] = t["err_attempts"] if lc.attempts >= LoginCode.MAX_ATTEMPTS else t["err_code"]
    if user is not None and user.is_active:
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(nxt)
    ctx["error"] = ctx["error"] or t["err_code"]
    return render(request, "console/login_code.html", ctx, status=400)
