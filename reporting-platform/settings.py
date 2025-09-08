# settings.py
from pathlib import Path
import os
import dj_database_url

# ---------------------------
# Core
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Always keep the secret key in env on Render
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-only-for-local")

DEBUG = os.environ.get("DEBUG", "0") in ("1", "true", "True")

# Render populates this environment variable
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# If you know your frontend origin(s), list them here (comma-separated in env)
DEFAULT_CORS = ["http://localhost:3000"]
ENV_CORS = [o for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOWED_ORIGINS = [*DEFAULT_CORS, *ENV_CORS]

CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    # Django requires exact origins, not wildcards
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# ---------------------------
# Applications
# ---------------------------
INSTALLED_APPS = [
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
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "reporting_platform.urls"  # <- change 'reporting_platform' to your project package if different

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

WSGI_APPLICATION = "reporting_platform.wsgi.application"  # <- change 'reporting_platform' if your project package differs

# ---------------------------
# Database (Render + SSL)
# ---------------------------
# Keep your URL in an env var on Render → DATABASE_URL
# We'll also accept a local .env variable for local dev.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    # Fallback only for local dev; prefer env var on Render
    # (You may remove this fallback if you don't want secrets in code)
    # "postgresql://rep_gen_db_user:PEbTKNRHV9FkEebcDrdQqQegtIXyWb7q@dpg-d29qbpngi27c73anlb20-a.oregon-postgres.render.com/rep_gen_db"
    None
)

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,  # << important: require SSL for managed Postgres
    ) if DATABASE_URL else {
        # Safe local default (e.g., if you use SQLite in dev)
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# If you don't use dj_database_url, you could enforce:
# DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

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
STATIC_ROOT = BASE_DIR / "staticfiles"  # Render collects here
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Django 5+ uses STORAGES for static handling
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Optional caching headers for whitenoise
WHITENOISE_MAX_AGE = 31536000  # 1 year

# ---------------------------
# Security (behind a proxy)
# ---------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "1") == "1"

# ---------------------------
# DRF (optional – tweak as needed)
# ---------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # You can add SessionAuthentication for admin usage:
        # "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",  # Your views can override this
    ],
}

# ---------------------------
# Default PK
# ---------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
