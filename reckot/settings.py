import os
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(',') if origin.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'slippers',

    'django_tasks',
    'django_tasks.backends.database',

    'apps.core',
    'apps.orgs',
    'apps.events',
    'apps.tickets',
    'apps.payments',
    'apps.checkin',
    'apps.reports',
    'apps.messaging',
    'apps.widgets',
    'apps.marketing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'reckot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'components'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.platform_settings',
            ],
            'builtins': [
                'slippers.templatetags.slippers',
            ]
        },
    },
]

SLIPPERS = {
    'COMPONENTS_DIRS': [BASE_DIR / 'templates' / 'components'],
}

WSGI_APPLICATION = 'reckot.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = "Africa/Douala"

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AUTH_USER_MODEL = 'core.User'

SITE_ID = int(os.getenv('SITE_ID', '1'))
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/events/'
LOGOUT_REDIRECT_URL = '/'


SOCIALACCOUNT_PROVIDERS = {}

_google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
_google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
if _google_client_id and _google_client_secret:
    SOCIALACCOUNT_PROVIDERS['google'] = {
        'APPS': [{
            'client_id': _google_client_id,
            'secret': _google_client_secret,
            'key': '',
        }],
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }

ACCOUNT_ADAPTER = 'apps.core.adapters.CustomAccountAdapter'
ACCOUNT_FORMS = {
    'signup': 'apps.core.forms.CustomSignupForm',
}

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION', 'optional')
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@reckot.com')

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
TWILIO_MESSAGING_SERVICE_SID = os.getenv('TWILIO_MESSAGING_SERVICE_SID', '')
TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID', '')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

RECKOT_PLATFORM_FEE_PERCENTAGE = Decimal(os.getenv('RECKOT_PLATFORM_FEE_PERCENTAGE', '7'))

PAYMENT_GATEWAYS = {
    'PRIMARY': os.getenv('PAYMENT_PRIMARY_GATEWAY', 'CAMPAY'),
    'FALLBACKS': os.getenv('PAYMENT_FALLBACK_GATEWAYS', 'PAWAPAY,FLUTTERWAVE').split(','),

    'CREDENTIALS': {
        'CAMPAY': {
            'app_username': os.getenv('CAMPAY_APP_USERNAME', ''),
            'app_password': os.getenv('CAMPAY_APP_PASSWORD', ''),
            'permanent_token': os.getenv('CAMPAY_PERMANENT_TOKEN', ''),
            'webhook_key': os.getenv('CAMPAY_WEBHOOK_KEY', ''),
            'is_production': os.getenv('CAMPAY_IS_PRODUCTION', 'False').lower() in ('true', '1', 'yes'),
        },
        'PAWAPAY': {
            'api_token': os.getenv('PAWAPAY_API_TOKEN', ''),
            'is_production': os.getenv('PAWAPAY_PRODUCTION', 'False').lower() in ('true', '1', 'yes'),
        },
        'FLUTTERWAVE': {
            'secret_key': os.getenv('FLUTTERWAVE_SECRET_KEY', ''),
            'public_key': os.getenv('FLUTTERWAVE_PUBLIC_KEY', ''),
            'encryption_key': os.getenv('FLUTTERWAVE_ENCRYPTION_KEY', ''),
        },
    },

    'CALLBACK_BASE_URL': os.getenv('PAYMENT_CALLBACK_URL', 'https://reckot.com'),
    'DEFAULT_CURRENCY': os.getenv('DEFAULT_CURRENCY', 'XAF'),
}

TASKS = {
    'default': {
        'BACKEND': 'django_tasks.backends.database.DatabaseBackend',
        'QUEUES': ['default', 'emails', 'payments'],
    }
}

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}
