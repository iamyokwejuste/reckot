import os
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in _csrf_origins.split(",") if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "slippers",
    "apps.core",
    "apps.orgs",
    "apps.events",
    "apps.tickets",
    "apps.payments",
    "apps.checkin",
    "apps.reports",
    "apps.messaging",
    "apps.widgets",
    "apps.marketing",
    "apps.ai",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.RateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "True").lower() in (
    "true",
    "1",
    "yes",
)

ROOT_URLCONF = "reckot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "components"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.platform_settings",
            ],
            "builtins": [
                "slippers.templatetags.slippers",
            ],
        },
    },
]

SLIPPERS = {
    "COMPONENTS_DIRS": [BASE_DIR / "templates" / "components"],
}

WSGI_APPLICATION = "reckot.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": 600,
        "ATOMIC_REQUESTS": True,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection._HiredisParser",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
        },
        "KEY_PREFIX": "reckot",
        "TIMEOUT": 300,
    },
    "analytics": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/2"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "analytics",
        "TIMEOUT": 600,
    },
    "reports": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/3"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "reports",
        "TIMEOUT": 900,
    },
}

TIME_ZONE = "Africa/Douala"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

CELERY_TASK_ROUTES = {
    "apps.core.tasks.send_email_task": {"queue": "emails"},
    "apps.core.tasks.send_sms_task": {"queue": "emails"},
    "apps.core.tasks.send_otp_sms_task": {"queue": "emails"},
    "apps.core.tasks.send_otp_verification_task": {"queue": "emails"},
    "apps.core.tasks.send_welcome_email_task": {"queue": "emails"},
    "apps.payments.tasks.*": {"queue": "payments"},
    "apps.reports.tasks.*": {"queue": "exports"},
    "apps.messaging.tasks.*": {"queue": "emails"},
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("fr", "Français"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AUTH_USER_MODEL = "core.User"

SITE_ID = int(os.getenv("SITE_ID", "1"))
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/events/"
LOGOUT_REDIRECT_URL = "/"


SOCIALACCOUNT_PROVIDERS = {}

_google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
_google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
if _google_client_id and _google_client_secret:
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APPS": [
            {
                "client_id": _google_client_id,
                "secret": _google_client_secret,
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }

ACCOUNT_ADAPTER = "apps.core.adapters.CustomAccountAdapter"
ACCOUNT_FORMS = {
    "signup": "apps.core.forms.CustomSignupForm",
}

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@reckot.com")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

RECKOT_PLATFORM_FEE_PERCENTAGE = Decimal(
    os.getenv("RECKOT_PLATFORM_FEE_PERCENTAGE", "7")
)

# campay docs: https://documenter.getpostman.com/view/2391374/T1LV8PVA

PAYMENT_GATEWAYS = {
    "PRIMARY": os.getenv("PAYMENT_PRIMARY_GATEWAY", "CAMPAY"),
    "FALLBACKS": os.getenv("PAYMENT_FALLBACK_GATEWAYS", "PAWAPAY,FLUTTERWAVE").split(
        ","
    ),
    "CREDENTIALS": {
        "CAMPAY": {
            "app_username": os.getenv("CAMPAY_APP_USERNAME", ""),
            "app_password": os.getenv("CAMPAY_APP_PASSWORD", ""),
            "permanent_token": os.getenv("CAMPAY_PERMANENT_TOKEN", ""),
            "webhook_key": os.getenv("CAMPAY_WEBHOOK_KEY", ""),
            "is_production": os.getenv("CAMPAY_IS_PRODUCTION", "False").lower()
            in ("true", "1", "yes"),
        },
        "PAWAPAY": {
            "api_token": os.getenv("PAWAPAY_API_TOKEN", ""),
            "is_production": os.getenv("PAWAPAY_PRODUCTION", "False").lower()
            in ("true", "1", "yes"),
        },
        "FLUTTERWAVE": {
            "secret_key": os.getenv("FLUTTERWAVE_SECRET_KEY", ""),
            "public_key": os.getenv("FLUTTERWAVE_PUBLIC_KEY", ""),
            "encryption_key": os.getenv("FLUTTERWAVE_ENCRYPTION_KEY", ""),
        },
    },
    "CALLBACK_BASE_URL": os.getenv("PAYMENT_CALLBACK_URL", "https://reckot.com"),
    "DEFAULT_CURRENCY": os.getenv("DEFAULT_CURRENCY", "XAF"),
}

RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "True").lower() in ("true", "1", "yes")

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
