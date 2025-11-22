from Bathelicious.settings import *
from decouple import config

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


CSRF_TRUSTED_ORIGINS = [
    "https://bathelicious.in",
    "https://www.bathelicious.in",
]


# ✅ Allowed hosts
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="bathelicious.in,www.bathelicious.in,localhost,127.0.0.1"
).split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ✅ Database (PostgreSQL inside Docker)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="postgres"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="db"),  # Docker service name
        "PORT": config("DB_PORT", default="5432"),
    }
}

# ✅ Static files served via WhiteNoise
STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE   = True
# WhiteNoise settings
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Disable manifest strict mode to prevent missing file errors
WHITENOISE_MANIFEST_STRICT = False

# --- Ensure WhiteNoise middleware is present (insert after SecurityMiddleware) ---
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    try:
        i = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1
    except ValueError:
        # If SecurityMiddleware isn't present for some reason, put WhiteNoise at the front
        i = 0
    MIDDLEWARE = MIDDLEWARE[:i] + ["whitenoise.middleware.WhiteNoiseMiddleware"] + MIDDLEWARE[i:]

SHIPPING_FLAT_RATE = int(config("SHIPPING_FLAT_RATE", default="80"))      # ₹80
FREE_SHIPPING_THRESHOLD = int(config("FREE_SHIPPING_THRESHOLD", default="999"))  # free ≥ ₹999
