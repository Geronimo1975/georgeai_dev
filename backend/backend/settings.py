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
        # Django's own templates (admin overrides, future server-rendered pages)
        # live here. The design export is served raw, never through this engine.
        "DIRS": [FRONTEND_DIR],
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
# serve the design export's assets (js/css/images/screenshots) through staticfiles too
STATICFILES_DIRS = [FRONTEND_DIR]
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
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

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
