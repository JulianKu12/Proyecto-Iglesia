import os
import secrets
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


def cargar_env(ruta):
    """Carga pares sencillos KEY=VALUE desde el .env fuera del repositorio."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


cargar_env(BASE_DIR / ".env")
cargar_env(BASE_DIR.parent / ".env")

DEBUG = os.getenv("DEBUG", "True").lower() in {"true", "1", "yes", "on"}
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("SECRET_KEY es obligatorio cuando DEBUG=False. Configúralo en .env.")
    SECRET_KEY = secrets.token_urlsafe(64)
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "core",
    "members",
    "institution",
    "ministries",
    "events",
    "attendance",
    "finance",
    "announcements",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.NoCacheAuthenticatedMiddleware",
    "core.middleware.FriendlyMethodNotAllowedMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.SessionInactivityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
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
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "accounts.validators.ValidadorSimilitud"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "accounts.validators.ValidadorComun"},
    {"NAME": "accounts.validators.ValidadorNumerica"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Merida"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.Usuario"
LOGIN_URL = "/cuentas/login/"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "login"
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {"true", "1", "yes", "on"}
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in {"true", "1", "yes", "on"}
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@iglesia.local")
PASSWORD_RESET_TIMEOUT = 3600
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "7200"))
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", str(not DEBUG)).lower() in {"true", "1", "yes", "on"}
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", str(not DEBUG)).lower() in {"true", "1", "yes", "on"}
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", str(not DEBUG)).lower() in {"true", "1", "yes", "on"}
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() in {"true", "1", "yes", "on"}
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", str(not DEBUG)).lower() in {"true", "1", "yes", "on"}
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv("SECURE_CONTENT_TYPE_NOSNIFF", "True" if not DEBUG else "False").lower() in {"true", "1", "yes", "on"}
X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY" if not DEBUG else "DENY")
SECURE_REFERRER_POLICY = os.getenv("SECURE_REFERRER_POLICY", "same-origin")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if os.getenv("USE_PROXY_SSL_HEADER", "False").lower() in {"true", "1", "yes", "on"} else None
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": "{levelname} {asctime} {name} {message}", "style": "{"}},
    "handlers": {"app_file": {"class": "logging.handlers.RotatingFileHandler", "filename": LOG_DIR / "app.log", "maxBytes": 5 * 1024 * 1024, "backupCount": 5, "formatter": "verbose", "encoding": "utf-8"}},
    "loggers": {"django": {"handlers": ["app_file"], "level": "ERROR", "propagate": False}},
}
TEMPLATES[0]["OPTIONS"]["context_processors"].append("institution.context_processors.iglesia")
TEMPLATES[0]["OPTIONS"]["context_processors"].append("finance.context_processors.permisos_finanzas")
