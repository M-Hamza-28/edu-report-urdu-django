# reporting_platform/settings.py
from pathlib import Path
import os

# 3rd-party libs used here:
#   pip install django-cors-headers whitenoise dj-database-url certifi
import dj_database_url          # parse DATABASE_URL when using Postgres
import certifi                  # provides a CA bundle for TLS verification

# ---------------------------
# Core
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Keep real SECRET_KEY in env on Render/Prod
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-only-for-local")

# DEBUG from env: "1"/"true"/"True" → True
DEBUG = os.environ.get("DEBUG", "1") in ("1", "true", "True")  # default True for local

# Render provides this on deploy; we’ll add it to hosts/CSRF if present
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# Add your custom domain(s) here in prod if any:
# ALLOWED_HOSTS += ["app.example.com"]

# ---------------------------
# CORS / CSRF for Frontend
# ---------------------------
# Allow your local React dev server(s)
DEFAULT_CORS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # add others if you use Vite etc.
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
ENV_CORS = [o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOWED_ORIGINS = [*DEFAULT_CORS, *ENV_CORS]

# Exact origins for CSRF (needed if you ever use cookie auth; harmless with JWT)
CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
# Trust local dev ports too (safe in DEBUG)
CSRF_TRUSTED_ORIGINS += [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

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
     "django_filters",

    # Third-party
    "corsheaders",         # <— enable CORS for React dev server
    "rest_framework",

    # Your app
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # Whitenoise must be directly after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS should be high in the chain and before CommonMiddleware
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
# Database
# ---------------------------
# Default to SQLite locally; use DATABASE_URL for Postgres in prod
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    db_cfg = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,   # connection pooling
        ssl_require=False   # set SSL options explicitly below
    )
    # Enforce TLS with CA bundle (fixes "SSL connection closed unexpectedly")
    opts = db_cfg.get("OPTIONS", {})
    opts["sslmode"] = opts.get("sslmode", "require")
    opts["sslrootcert"] = opts.get("sslrootcert", certifi.where())
    db_cfg["OPTIONS"] = opts
    DATABASES["default"] = db_cfg

# ---------------------------
# Internationalization / TZ
# ---------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

# ---------------------------
# Static files (WhiteNoise)
# ---------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for static files

# ---------------------------
# Security
# ---------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# In local dev, do NOT force HTTPS; redirects break CORS preflight (OPTIONS)
SECURE_SSL_REDIRECT = os.environ.get(
    "SECURE_SSL_REDIRECT",
    "0" if DEBUG else "1"      # default: off in DEBUG, on in production
) == "1"

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# ---------------------------
# Django REST Framework
# ---------------------------
APPEND_SLASH = True  # DRF DefaultRouter uses trailing slashes
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "reports.auth.LenientJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
     "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",   # public read by default (safe for GET)
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
        "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}


# Helpful for DRF trailing slashes (default True). Keep your frontend URLs ending in '/'
APPEND_SLASH = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
