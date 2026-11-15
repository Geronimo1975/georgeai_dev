"""Passwordless console sign-in: email -> 6-digit one-time code -> session.

The first successful code for an unknown email creates the account, so signing
in and signing up are the same two steps. Staff keep password login at /admin/
(an admin session also opens the console).
"""
import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .copy import copy_for
from .models import LoginCode

log = logging.getLogger(__name__)

SESSION_EMAIL = "console_login_email"
SESSION_NEXT = "console_login_next"
CODES_PER_EMAIL = 3   # per 10 minutes
CODES_PER_IP = 10     # per hour


def _hash(email, code):
    msg = f"{email}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


def _client_ip(request):
    # Traefik -> nginx -> gunicorn: nginx sets X-Real-IP to the client address.
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


def _safe_next(request, value):
    if value and url_has_allowed_host_and_scheme(value, {request.get_host()}, require_https=request.is_secure()):
        return value
    return "/console/"


def _issue_code(request, email, t):
    """Create and email a code. Returns an error string or None."""
    now = timezone.now()
    ip = _client_ip(request)
    if LoginCode.objects.filter(email=email, created_at__gte=now - timedelta(minutes=10)).count() >= CODES_PER_EMAIL:
        return t["err_rate"]
    if ip and LoginCode.objects.filter(ip=ip, created_at__gte=now - timedelta(hours=1)).count() >= CODES_PER_IP:
        return t["err_rate"]
    code = f"{secrets.randbelow(10**6):06d}"
    with transaction.atomic():
        LoginCode.objects.filter(email=email, used_at__isnull=True).update(used_at=now)  # older codes die
        LoginCode.objects.create(email=email, code_hash=_hash(email, code), ip=ip,
                                 expires_at=now + timedelta(seconds=LoginCode.TTL_SECONDS))
    try:
        send_mail(t["mail_subject"].format(code=code), t["mail_body"].format(code=code),
                  settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    except Exception as exc:  # noqa: BLE001 — SMTP down / misconfigured
        log.error("login code email failed: %s: %s", type(exc).__name__, exc)
        return t["err_send"]
    return None


@require_http_methods(["GET", "POST"])
def login_email(request):
    t = copy_for(request)
    if request.user.is_authenticated:
        return redirect(_safe_next(request, request.GET.get("next")))
    ctx = {"t": t, "email": "", "error": ""}
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            ctx.update(email=email, error=t["err_email"])
            return render(request, "console/login.html", ctx, status=400)
        error = _issue_code(request, email, t)
        if error:
            ctx.update(email=email, error=error)
            return render(request, "console/login.html", ctx, status=429 if error == t["err_rate"] else 503)
        request.session[SESSION_EMAIL] = email
        request.session[SESSION_NEXT] = _safe_next(request, request.POST.get("next"))
        return redirect("console_login_code")
    ctx["next"] = _safe_next(request, request.GET.get("next"))
    return render(request, "console/login.html", ctx)


@require_http_methods(["GET", "POST"])
def login_code(request):
    t = copy_for(request)
    email = request.session.get(SESSION_EMAIL)
    if not email:
        return redirect("console_login")
    ctx = {"t": t, "email": email, "lede": t["code_lede"].format(email=email), "error": "", "notice": ""}
    if request.method == "POST" and request.POST.get("resend"):
        error = _issue_code(request, email, t)
        ctx["error" if error else "notice"] = error or t["sent_again"]
        return render(request, "console/login_code.html", ctx, status=429 if error else 200)
    if request.method == "POST":
        code = "".join(ch for ch in request.POST.get("code", "") if ch.isdigit())
        with transaction.atomic():
            lc = (LoginCode.objects.select_for_update()
                  .filter(email=email, used_at__isnull=True, expires_at__gt=timezone.now()).first())
            if lc is None:
                ctx["error"] = t["err_code"]
            elif lc.attempts >= LoginCode.MAX_ATTEMPTS:
                ctx["error"] = t["err_attempts"]
            elif len(code) == 6 and hmac.compare_digest(lc.code_hash, _hash(email, code)):
                lc.used_at = timezone.now()
                lc.save(update_fields=["used_at"])
                User = get_user_model()
                user = User.objects.filter(email__iexact=email).first()
                if user is None:
                    user = User.objects.create_user(email=email, password=None)  # unusable password
                if not user.is_active:
                    ctx["error"] = t["err_code"]
                else:
                    nxt = request.session.get(SESSION_NEXT) or "/console/"
                    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                    request.session.pop(SESSION_EMAIL, None)
                    request.session.pop(SESSION_NEXT, None)
                    return redirect(_safe_next(request, nxt))
            else:
                lc.attempts += 1
                lc.save(update_fields=["attempts"])
                ctx["error"] = t["err_attempts"] if lc.attempts >= LoginCode.MAX_ATTEMPTS else t["err_code"]
        return render(request, "console/login_code.html", ctx, status=400)
    return render(request, "console/login_code.html", ctx)
