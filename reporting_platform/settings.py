# reporting_platform/settings.py
from pathlib import Path
import os
import dj_database_url  # used to parse DATABASE_URL and force SSL

# ---------------------------
# Core
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Keep real SECRET_KEY in env on Render
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-only-for-local")

# DEBUG from env: "1"/"true"/"True" → True
DEBUG = os.environ.get("DEBUG", "0") in ("1", "true", "True")

# Render provides this on deploy; we’ll add it to hosts/CSRF if present
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# If you also use a custom domain, add it here:
# ALLOWED_HOSTS += ["app.example.com"]

# CORS (allow your local React dev server by default)
DEFAULT_CORS = ["http://localhost:3000", "http://127.0.0.1:3000"]
ENV_CORS = [o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOWED_ORIGINS = [*DEFAULT_CORS, *ENV_CORS]

# Exact origins required for CSRF (no wildcards)
CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
# If you bind a custom domain, add it here:
# CSRF_TRUSTED_ORIGINS += ["https://app.example.com"]

# ---------------------------
# Applications
# ---------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",
    "rest_framework",

    # Your apps
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # Whitenoise must be directly after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS early in the chain
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "reporting_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "reporting_platform.wsgi.application"
ASGI_APPLICATION = "reporting_platform.asgi.application"

# ---------------------------
# Database (Render + SSL in code)
# ---------------------------
# Paste the External Database URL from your Render Postgres into the Web Service
# environment as DATABASE_URL (copy EXACTLY; do not edit the DB page).
#
# We’ll *force* SSL here with ssl_require=True, so even if the URL doesn’t
# include ?sslmode=require, TLS is still enforced.
DATABASES = {
    "default": {
        # Local/dev fallback when no DATABASE_URL is set:
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,   # keep connections pooled
        ssl_require=True,   # 🔒 critical: enforce TLS to managed Postgres
    )

# ---------------------------
# Internationalization / TZ
# ---------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

# ---------------------------
# Static files (Whitenoise)
# ---------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Django 5+ STORAGES API
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Cache-control for static files (served by Whitenoise)
WHITENOISE_MAX_AGE = 31536000  # 1 year

# ---------------------------
# Security (behind a proxy)
# ---------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "1") == "1"

# ---------------------------
# DRF
# ---------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # optionally enable session auth for admin/testing:
        # "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
