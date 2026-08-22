"""
Django settings for georgeai.dev.

Configuration is read from a .env file (see .env.example) via django-environ,
so no secrets live in source control.
"""
from pathlib import Path

import environ

# backend/config/settings.py -> BASE_DIR = backend/ , ROOT_DIR = project root
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# The static design export that deploy.sh mirrors here from exports/.
# Django serves these files as-is (no template rendering — they use {{ }} client-side).
FRONTEND_DIR = ROOT_DIR / "frontend" / "template"

# repo-owned assets injected alongside the export (e.g. auth.js) — survive re-exports
ASSETS_DIR = BASE_DIR / "assets"

# ---------------------------------------------------------------------------
# environment (.env)
# ---------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "jazzmin",  # admin theme — must precede django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    # local apps
    "accounts",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Only Django's own templates (admin overrides, future server-rendered
        # pages) belong here. FRONTEND_DIR is deliberately NOT in DIRS: the
        # export's {{ }} placeholders are rendered client-side by support.js and
        # would be eaten by this engine. It is served verbatim by serve_frontend.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

# ---------------------------------------------------------------------------
# database (PostgreSQL via DATABASE_URL)
# ---------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}

# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
# The design export is NOT collected here — serve_frontend already serves it at
# the paths its HTML references. staticfiles only carries admin/DRF assets.
STATIC_ROOT = ROOT_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = ROOT_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework (session auth keeps the same cookie + CSRF model)
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # closed by default — the public auth views opt out with AllowAny explicitly
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    # brute-force / signup-spam guard, keyed by IP for anonymous callers
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": env("THROTTLE_AUTH_LOGIN", default="10/min"),
        "auth_signup": env("THROTTLE_AUTH_SIGNUP", default="5/hour"),
    },
}

# ScopedRateThrottle counts in the cache; LocMemCache is per-process, so with
# several gunicorn workers the effective rate is <rate> × <workers>. Point
# CACHE_URL at Redis in production to make the limit global.
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

# ---------------------------------------------------------------------------
# sessions / CSRF (auth uses the session cookie; auth.js reads csrftoken)
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# csrftoken must stay readable by JS (auth.js sends it as X-CSRFToken)
CSRF_COOKIE_HTTPONLY = False
# secure cookies in production (HTTPS); overridable via .env
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://georgeai.dev", "https://www.georgeai.dev"],
)

LOGIN_URL = "/admin/login/"

# ---------------------------------------------------------------------------
# transport security
#
# nginx currently terminates TLS and sets HSTS itself; these settings make the
# same guarantees hold once gunicorn serves the site directly. All are no-ops
# under DEBUG so local http:// dev keeps working.
# ---------------------------------------------------------------------------
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
# Traefik terminates TLS and sets X-Forwarded-Proto; only trustworthy because
# nothing but Traefik can reach the container on the gethub network.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# logging (console + rotating file, YaSaaS-style)
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "logfile"], "level": "INFO"},
}

# ---------------------------------------------------------------------------
# jazzmin admin theme
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "georgeai.dev admin",
    "site_header": "georgeai.dev",
    "site_brand": "georgeai.dev",
    "welcome_sign": "Welcome to the georgeai.dev admin",
    "copyright": "georgeai.dev",
    "search_model": ["accounts.User"],
}
