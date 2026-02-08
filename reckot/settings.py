import os
import ssl
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

_allowed_hosts = os.getenv("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
if "localhost" not in ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("localhost")
if "127.0.0.1" not in ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("127.0.0.1")

_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in _csrf_origins.split(",") if origin.strip()
]

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "slippers",
    "storages",
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
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "reckot.middleware.admin_redirect.AdminRootRedirectMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.utils.middleware.RateLimitMiddleware",
    "reckot.middleware.admin_only.AdminOnlyMiddleware",
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
                "apps.core.utils.context_processors.platform_settings",
                "apps.core.utils.context_processors.unread_notifications",
                "apps.core.utils.context_processors.user_currency",
                "apps.core.context_processors.settings.cache_version",
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
    },
    "ai_public_readonly": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": "reckot_ai_public_readonly",
        "PASSWORD": os.getenv("AI_PUBLIC_READONLY_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 5,
        },
    },
    "ai_auth_readonly": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": "reckot_ai_auth_readonly",
        "PASSWORD": os.getenv("AI_AUTH_READONLY_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 5,
        },
    },
    "ai_org_readonly": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": "reckot_ai_org_readonly",
        "PASSWORD": os.getenv("AI_ORG_READONLY_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 5,
        },
    },
}

import ssl

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")
_SSL_CERT_REQS = getattr(ssl, os.getenv("REDIS_SSL_CERT_REQS", "CERT_NONE"), ssl.CERT_NONE)

_redis_options = {
    "CLIENT_CLASS": "django_redis.client.DefaultClient",
    "CONNECTION_POOL_KWARGS": {
        "max_connections": 50,
        "retry_on_timeout": True,
    },
}

if REDIS_URL.startswith("rediss://"):
    _redis_options["CONNECTION_POOL_KWARGS"]["ssl_cert_reqs"] = _SSL_CERT_REQS

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {**_redis_options},
        "KEY_PREFIX": "reckot",
        "TIMEOUT": 300,
    },
    "analytics": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL.rsplit("/", 1)[0] + "/2",
        "OPTIONS": {**_redis_options},
        "KEY_PREFIX": "analytics",
        "TIMEOUT": 600,
    },
    "reports": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL.rsplit("/", 1)[0] + "/3",
        "OPTIONS": {**_redis_options},
        "KEY_PREFIX": "reports",
        "TIMEOUT": 900,
    },
}

TIME_ZONE = "Africa/Douala"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")

if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": _SSL_CERT_REQS}
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": _SSL_CERT_REQS}

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

CACHE_VERSION = "1770489490"

WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG

if not DEBUG:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_USE_SSL = os.getenv("AWS_S3_USE_SSL", "True") == "True"
    AWS_S3_VERIFY = True
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "path")

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "reckot.storage.NonStrictCompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/" if AWS_S3_ENDPOINT_URL else "/media/"
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "reckot.storage.NonStrictCompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "core.User"

SITE_ID = int(os.getenv("SITE_ID", "1"))
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/reports/"
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

ACCOUNT_ADAPTER = "apps.core.services.adapters.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "apps.core.services.adapters.CustomSocialAccountAdapter"
ACCOUNT_FORMS = {
    "signup": "apps.core.forms.CustomSignupForm",
}

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "optional")
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

ACCOUNT_ALLOW_REGISTRATION = os.getenv(
    "ACCOUNT_ALLOW_REGISTRATION", "true"
).lower() in ("true", "1", "yes")

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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_MODEL_THINKING = os.getenv("GEMINI_MODEL_THINKING", "gemini-3-flash-preview")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
GEMINI_LITE_MODEL = os.getenv("GEMINI_LITE_MODEL", "gemini-1.5-flash-8b")
RECKOT_AI_CHAT_DAILY_LIMIT = int(os.getenv("RECKOT_AI_CHAT_DAILY_LIMIT", "50"))

RECKOT_PLATFORM_FEE_PERCENTAGE = Decimal(
    os.getenv("RECKOT_PLATFORM_FEE_PERCENTAGE", "7")
)

RECKOT_AI_CHAT_DAILY_LIMIT = int(os.getenv("RECKOT_AI_CHAT_DAILY_LIMIT", "50"))

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
            "webhook_secret": os.getenv("FLUTTERWAVE_WEBHOOK_SECRET", ""),
        },
    },
    "CALLBACK_BASE_URL": os.getenv("PAYMENT_CALLBACK_URL", "https://reckot.com"),
    "DEFAULT_CURRENCY": os.getenv("DEFAULT_CURRENCY", "XAF"),
}

CAMPAY_USERNAME = os.getenv("CAMPAY_APP_USERNAME", "")
CAMPAY_PASSWORD = os.getenv("CAMPAY_APP_PASSWORD", "")
CAMPAY_TOKEN = os.getenv("CAMPAY_PERMANENT_TOKEN", "")
CAMPAY_PRODUCTION = os.getenv("CAMPAY_IS_PRODUCTION", "False").lower() in (
    "true",
    "1",
    "yes",
)

RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "True").lower() in (
    "true",
    "1",
    "yes",
)

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

UNFOLD = {
    "SITE_TITLE": "Reckot Admin",
    "SITE_HEADER": "Reckot Administration",
    "SITE_URL": "/",
    "SITE_ICON": "apps.core.services.utils.get_logo_path",
    "SITE_LOGO": "apps.core.services.utils.get_logo_path",
    "SITE_SYMBOL": "event",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "apps.core.services.utils.environment_callback",
    "DASHBOARD_CALLBACK": "apps.analytics.views.dashboard_callback",
    "STYLES": [
        lambda request: static("css/admin_custom.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇧🇪",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Analytics"),
                "collapsible": True,
                "icon": "analytics",
                "items": [
                    {
                        "title": _("Revenue"),
                        "icon": "attach_money",
                        "link": "/admin/reports/revenue/",
                    },
                    {
                        "title": _("Event Performance"),
                        "icon": "bar_chart",
                        "link": "/admin/reports/events/",
                    },
                    {
                        "title": _("Ticket Sales"),
                        "icon": "confirmation_number",
                        "link": "/admin/reports/tickets/",
                    },
                    {
                        "title": _("Payment Tracking"),
                        "icon": "payment",
                        "link": "/admin/reports/payments/",
                    },
                ],
            },
            {
                "title": _("Organizations"),
                "collapsible": True,
                "icon": "business",
                "items": [
                    {
                        "title": _("Organizations"),
                        "icon": "corporate_fare",
                        "link": reverse_lazy("admin:orgs_organization_changelist"),
                    },
                    {
                        "title": _("Members"),
                        "icon": "people",
                        "link": reverse_lazy("admin:orgs_membership_changelist"),
                    },
                ],
            },
            {
                "title": _("Events"),
                "collapsible": True,
                "icon": "event",
                "items": [
                    {
                        "title": _("Events"),
                        "icon": "event_available",
                        "link": reverse_lazy("admin:events_event_changelist"),
                    },
                    {
                        "title": _("Event Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:events_eventcategory_changelist"),
                    },
                ],
            },
            {
                "title": _("Tickets & Sales"),
                "collapsible": True,
                "icon": "receipt",
                "items": [
                    {
                        "title": _("Tickets"),
                        "icon": "local_activity",
                        "link": reverse_lazy("admin:tickets_ticket_changelist"),
                    },
                    {
                        "title": _("Bookings"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:tickets_booking_changelist"),
                    },
                    {
                        "title": _("Ticket Types"),
                        "icon": "confirmation_number",
                        "link": reverse_lazy("admin:tickets_tickettype_changelist"),
                    },
                    {
                        "title": _("Guest Sessions"),
                        "icon": "person_outline",
                        "link": reverse_lazy("admin:tickets_guestsession_changelist"),
                    },
                ],
            },
            {
                "title": _("Payments"),
                "collapsible": True,
                "icon": "payments",
                "items": [
                    {
                        "title": _("Transactions"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:payments_payment_changelist"),
                    },
                    {
                        "title": _("Offline Payments"),
                        "icon": "money",
                        "link": reverse_lazy(
                            "admin:payments_offlinepayment_changelist"
                        ),
                    },
                    {
                        "title": _("Refunds"),
                        "icon": "currency_exchange",
                        "link": reverse_lazy("admin:payments_refund_changelist"),
                    },
                    {
                        "title": _("Withdrawals"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:payments_withdrawal_changelist"),
                    },
                    {
                        "title": _("Payment Gateways"),
                        "icon": "credit_card",
                        "link": reverse_lazy(
                            "admin:payments_paymentgatewayconfig_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Check-in & Swag"),
                "collapsible": True,
                "icon": "how_to_reg",
                "items": [
                    {
                        "title": _("Check-ins"),
                        "icon": "check_circle",
                        "link": reverse_lazy("admin:checkin_checkin_changelist"),
                    },
                    {
                        "title": _("Swag Items"),
                        "icon": "card_giftcard",
                        "link": reverse_lazy("admin:checkin_swagitem_changelist"),
                    },
                    {
                        "title": _("Swag Collections"),
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:checkin_swagcollection_changelist"),
                    },
                ],
            },
            {
                "title": _("Marketing"),
                "collapsible": True,
                "icon": "campaign",
                "items": [
                    {
                        "title": _("Affiliate Links"),
                        "icon": "people_outline",
                        "link": reverse_lazy(
                            "admin:marketing_affiliatelink_changelist"
                        ),
                    },
                    {
                        "title": _("Conversions"),
                        "icon": "trending_up",
                        "link": reverse_lazy(
                            "admin:marketing_affiliateconversion_changelist"
                        ),
                    },
                    {
                        "title": _("Social Shares"),
                        "icon": "share",
                        "link": reverse_lazy("admin:marketing_socialshare_changelist"),
                    },
                ],
            },
            {
                "title": _("AI & Support"),
                "collapsible": True,
                "icon": "support_agent",
                "items": [
                    {
                        "title": _("Support Tickets"),
                        "icon": "support",
                        "link": reverse_lazy("admin:ai_supportticket_changelist"),
                    },
                    {
                        "title": _("AI Conversations"),
                        "icon": "chat",
                        "link": reverse_lazy("admin:ai_aiconversation_changelist"),
                    },
                    {
                        "title": _("AI Messages"),
                        "icon": "message",
                        "link": reverse_lazy("admin:ai_aimessage_changelist"),
                    },
                ],
            },
            {
                "title": _("Messaging"),
                "collapsible": True,
                "icon": "mail",
                "items": [
                    {
                        "title": _("Campaigns"),
                        "icon": "campaign",
                        "link": reverse_lazy(
                            "admin:messaging_messagecampaign_changelist"
                        ),
                    },
                    {
                        "title": _("Templates"),
                        "icon": "email",
                        "link": reverse_lazy(
                            "admin:messaging_messagetemplate_changelist"
                        ),
                    },
                    {
                        "title": _("Message Delivery"),
                        "icon": "send",
                        "link": reverse_lazy(
                            "admin:messaging_messagedelivery_changelist"
                        ),
                    },
                    {
                        "title": _("Notifications"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:core_notification_changelist"),
                    },
                ],
            },
            {
                "title": _("Widgets"),
                "collapsible": True,
                "icon": "widgets",
                "items": [
                    {
                        "title": _("Embed Widgets"),
                        "icon": "code",
                        "link": reverse_lazy("admin:widgets_embedwidget_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Permissions"),
                "collapsible": True,
                "icon": "group",
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:core_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group_work",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Analytics Data"),
                "collapsible": True,
                "icon": "assessment",
                "items": [
                    {
                        "title": _("Daily Metrics"),
                        "icon": "calendar_today",
                        "link": reverse_lazy("admin:analytics_dailymetrics_changelist"),
                    },
                    {
                        "title": _("Event Metrics"),
                        "icon": "insights",
                        "link": reverse_lazy("admin:analytics_eventmetrics_changelist"),
                    },
                    {
                        "title": _("Payment Metrics"),
                        "icon": "analytics",
                        "link": reverse_lazy(
                            "admin:analytics_paymentmetrics_changelist"
                        ),
                    },
                    {
                        "title": _("Organization Metrics"),
                        "icon": "business_center",
                        "link": reverse_lazy(
                            "admin:analytics_organizationmetrics_changelist"
                        ),
                    },
                ],
            },
        ],
    },
    "SIDEBAR_CUSTOM_BACKUP": {
        "show_search": True,
        "show_all_applications": False,
        "navigation_expanded": True,
        "navigation": [
            {
                "title": _("Dashboard"),
                "separator": True,
                "collapsible": True,
                "icon": "dashboard",
                "items": [
                    {
                        "title": _("Overview"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Analytics"),
                "separator": True,
                "separator": True,
                "collapsible": True,
                "icon": "analytics",
                "items": [
                    {
                        "title": _("Revenue"),
                        "icon": "attach_money",
                        "link": "/admin/reports/revenue/",
                    },
                    {
                        "title": _("Event Performance"),
                        "icon": "bar_chart",
                        "link": "/admin/reports/events/",
                    },
                    {
                        "title": _("Ticket Sales"),
                        "icon": "confirmation_number",
                        "link": "/admin/reports/tickets/",
                    },
                    {
                        "title": _("Payment Tracking"),
                        "icon": "payment",
                        "link": "/admin/reports/payments/",
                    },
                ],
            },
            {
                "title": _("Organizations"),
                "separator": True,
                "collapsible": True,
                "icon": "business",
                "items": [
                    {
                        "title": _("Organizations"),
                        "icon": "corporate_fare",
                        "link": reverse_lazy("admin:orgs_organization_changelist"),
                    },
                    {
                        "title": _("Members"),
                        "icon": "people",
                        "link": reverse_lazy("admin:orgs_membership_changelist"),
                    },
                ],
            },
            {
                "title": _("Events"),
                "separator": True,
                "collapsible": True,
                "icon": "event",
                "items": [
                    {
                        "title": _("Events"),
                        "icon": "event_available",
                        "link": reverse_lazy("admin:events_event_changelist"),
                    },
                    {
                        "title": _("Event Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:events_eventcategory_changelist"),
                    },
                ],
            },
            {
                "title": _("Tickets & Sales"),
                "separator": True,
                "collapsible": True,
                "icon": "receipt",
                "items": [
                    {
                        "title": _("Tickets"),
                        "icon": "local_activity",
                        "link": reverse_lazy("admin:tickets_ticket_changelist"),
                    },
                    {
                        "title": _("Bookings"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:tickets_booking_changelist"),
                    },
                    {
                        "title": _("Ticket Types"),
                        "icon": "confirmation_number",
                        "link": reverse_lazy("admin:tickets_tickettype_changelist"),
                    },
                    {
                        "title": _("Guest Sessions"),
                        "icon": "person_outline",
                        "link": reverse_lazy("admin:tickets_guestsession_changelist"),
                    },
                ],
            },
            {
                "title": _("Payments"),
                "separator": True,
                "collapsible": True,
                "icon": "payments",
                "items": [
                    {
                        "title": _("Transactions"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:payments_payment_changelist"),
                    },
                    {
                        "title": _("Offline Payments"),
                        "icon": "money",
                        "link": reverse_lazy(
                            "admin:payments_offlinepayment_changelist"
                        ),
                    },
                    {
                        "title": _("Refunds"),
                        "icon": "currency_exchange",
                        "link": reverse_lazy("admin:payments_refund_changelist"),
                    },
                    {
                        "title": _("Withdrawals"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:payments_withdrawal_changelist"),
                    },
                    {
                        "title": _("Payment Gateways"),
                        "icon": "credit_card",
                        "link": reverse_lazy(
                            "admin:payments_paymentgatewayconfig_changelist"
                        ),
                    },
                ],
            },
            {
                "title": _("Check-in & Swag"),
                "separator": True,
                "collapsible": True,
                "icon": "how_to_reg",
                "items": [
                    {
                        "title": _("Check-ins"),
                        "icon": "check_circle",
                        "link": reverse_lazy("admin:checkin_checkin_changelist"),
                    },
                    {
                        "title": _("Swag Items"),
                        "icon": "card_giftcard",
                        "link": reverse_lazy("admin:checkin_swagitem_changelist"),
                    },
                    {
                        "title": _("Swag Collections"),
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:checkin_swagcollection_changelist"),
                    },
                ],
            },
            {
                "title": _("Marketing"),
                "separator": True,
                "collapsible": True,
                "icon": "campaign",
                "items": [
                    {
                        "title": _("Affiliate Links"),
                        "icon": "people_outline",
                        "link": reverse_lazy(
                            "admin:marketing_affiliatelink_changelist"
                        ),
                    },
                    {
                        "title": _("Conversions"),
                        "icon": "trending_up",
                        "link": reverse_lazy(
                            "admin:marketing_affiliateconversion_changelist"
                        ),
                    },
                    {
                        "title": _("Social Shares"),
                        "icon": "share",
                        "link": reverse_lazy("admin:marketing_socialshare_changelist"),
                    },
                ],
            },
            {
                "title": _("AI & Support"),
                "separator": True,
                "collapsible": True,
                "icon": "support_agent",
                "items": [
                    {
                        "title": _("Support Tickets"),
                        "icon": "support",
                        "link": reverse_lazy("admin:ai_supportticket_changelist"),
                    },
                    {
                        "title": _("AI Conversations"),
                        "icon": "chat",
                        "link": reverse_lazy("admin:ai_aiconversation_changelist"),
                    },
                    {
                        "title": _("AI Messages"),
                        "icon": "message",
                        "link": reverse_lazy("admin:ai_aimessage_changelist"),
                    },
                ],
            },
            {
                "title": _("Messaging"),
                "separator": True,
                "collapsible": True,
                "icon": "mail",
                "items": [
                    {
                        "title": _("Campaigns"),
                        "icon": "campaign",
                        "link": reverse_lazy(
                            "admin:messaging_messagecampaign_changelist"
                        ),
                    },
                    {
                        "title": _("Templates"),
                        "icon": "email",
                        "link": reverse_lazy(
                            "admin:messaging_messagetemplate_changelist"
                        ),
                    },
                    {
                        "title": _("Message Delivery"),
                        "icon": "send",
                        "link": reverse_lazy(
                            "admin:messaging_messagedelivery_changelist"
                        ),
                    },
                    {
                        "title": _("Notifications"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:core_notification_changelist"),
                    },
                ],
            },
            {
                "title": _("Widgets"),
                "separator": True,
                "collapsible": True,
                "icon": "widgets",
                "items": [
                    {
                        "title": _("Embed Widgets"),
                        "icon": "code",
                        "link": reverse_lazy("admin:widgets_embedwidget_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Permissions"),
                "separator": True,
                "collapsible": True,
                "icon": "group",
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:core_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group_work",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Analytics Data"),
                "separator": True,
                "collapsible": True,
                "icon": "assessment",
                "items": [
                    {
                        "title": _("Daily Metrics"),
                        "icon": "calendar_today",
                        "link": reverse_lazy("admin:analytics_dailymetrics_changelist"),
                    },
                    {
                        "title": _("Event Metrics"),
                        "icon": "insights",
                        "link": reverse_lazy("admin:analytics_eventmetrics_changelist"),
                    },
                    {
                        "title": _("Payment Metrics"),
                        "icon": "analytics",
                        "link": reverse_lazy(
                            "admin:analytics_paymentmetrics_changelist"
                        ),
                    },
                    {
                        "title": _("Organization Metrics"),
                        "icon": "business_center",
                        "link": reverse_lazy(
                            "admin:analytics_organizationmetrics_changelist"
                        ),
                    },
                ],
            },
        ],
    },
}

ADMIN_ONLY_MODE = os.getenv("ADMIN_ONLY_MODE", "False").lower() in ("true", "1", "yes")
