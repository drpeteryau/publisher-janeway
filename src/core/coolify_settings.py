"""Production settings for container deployments (Coolify + Cloudflare Tunnel).

Selected with JANEWAY_SETTINGS_MODULE=core.coolify_settings and layered on top
of core.janeway_global_settings. Everything is driven by environment variables
so no settings file needs to be edited per deployment.

TLS terminates at Cloudflare, which forwards to the container over plain HTTP
through the tunnel, so the app must trust X-Forwarded-Proto/Host.
"""

import os


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default=""):
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


SECRET_KEY = os.environ["JANEWAY_SECRET_KEY"]
DEBUG = _env_bool("JANEWAY_DEBUG", False)

# Hostnames served through the tunnel, e.g. "journals.example.org,www.example.org".
ALLOWED_HOSTS = _env_list("JANEWAY_ALLOWED_HOSTS", "*")
_public_hosts = [h for h in ALLOWED_HOSTS if h != "*" and not h.startswith(".")]
CSRF_TRUSTED_ORIGINS = _env_list(
    "JANEWAY_CSRF_TRUSTED_ORIGINS",
    ",".join("https://%s" % h for h in _public_hosts),
)

# Cloudflare Tunnel -> cloudflared -> container is HTTP; trust the proxy headers.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = _env_bool("JANEWAY_SECURE_COOKIES", True)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

DEFAULT_HOST = os.environ.get("JANEWAY_DEFAULT_HOST", "https://www.example.org")
URL_CONFIG = os.environ.get("JANEWAY_URL_CONFIG", "path")  # path or domain

# Persistent locations (mounted as volumes in compose.yaml).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
MEDIA_ROOT = os.environ.get("JANEWAY_MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
STATIC_ROOT = os.environ.get(
    "JANEWAY_STATIC_ROOT", os.path.join(BASE_DIR, "collected-static")
)

EMAIL_BACKEND = os.environ.get(
    "JANEWAY_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_USE_TLS = _env_bool("JANEWAY_EMAIL_USE_TLS", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {
        "level": os.environ.get("JANEWAY_LOG_LEVEL", "INFO"),
        "handlers": ["console"],
    },
}
