"""
Django settings for the Onmer Yemek Organizasyon project.

Premium catering company website backed by Django 6 and Bootstrap 5.
"""

from pathlib import Path
import os

try:
    from load_env import bootstrap as _load_project_env

    _load_project_env()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Security / Debug
# ---------------------------------------------------------------------------
# NOTE: For production, move SECRET_KEY to an environment variable and turn
# DEBUG off. These defaults are for local development only.
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-onmer-yemek-organizasyon-dev-secret-CHANGE-ME',
)
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes')

_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
if _render_host:
    ALLOWED_HOSTS = [_render_host, 'localhost', '127.0.0.1']
else:
    _allowed = os.environ.get('ALLOWED_HOSTS', '*').strip()
    ALLOWED_HOSTS = ['*'] if _allowed == '*' else [
        h.strip() for h in _allowed.split(',') if h.strip()
    ]

# Render gibi ortamlarda admin yüklemeleri repo ile deploy edilir; /media/ servis edilir.
SERVE_MEDIA = os.environ.get('SERVE_MEDIA', '1') == '1'


# ---------------------------------------------------------------------------
# Installed apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third-party
    'widget_tweaks',

    # Local apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'menu.apps.MenuConfig',
    'orders.apps.OrdersConfig',
    'reservations.apps.ReservationsConfig',
    'portfolio.apps.PortfolioConfig',
    'inventory.apps.InventoryConfig',
]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ---------------------------------------------------------------------------
# URLs / WSGI
# ---------------------------------------------------------------------------
ROOT_URLCONF = 'onmer.urls'
WSGI_APPLICATION = 'onmer.wsgi.application'


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Project-wide templates folder so we can ship a shared base.html.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Varsayılan: PostgreSQL (psycopg3: pip install -r requirements.txt).
# Yerel olarak SQLite kullanmak için ortam değişkeni: USE_SQLITE=1
#
# PostgreSQL ilk kurulum (örnek, psql):
#   CREATE USER onmer WITH PASSWORD 'onmer';
#   CREATE DATABASE onmer_yemek OWNER onmer;
#   GRANT ALL PRIVILEGES ON DATABASE onmer_yemek TO onmer;
#
# Ortam değişkenleri (üretimde mutlaka güçlü şifre):
#   POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
#
USE_SQLITE = os.environ.get('USE_SQLITE', '').lower() in ('1', 'true', 'yes')

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            },
        }
    }
else:
    _pg_options: dict = {'connect_timeout': 10}
    _sslmode = os.environ.get('POSTGRES_SSLMODE', '').strip()
    if _sslmode:
        _pg_options['sslmode'] = _sslmode

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'onmer_yemek'),
            'USER': os.environ.get('POSTGRES_USER', 'onmer'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'onmer'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': _pg_options,
        }
    }


# ---------------------------------------------------------------------------
# Auth password validators
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Internationalization (Turkish locale)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Auth redirects
# ---------------------------------------------------------------------------
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'


# ---------------------------------------------------------------------------
# Messages framework — map levels to Bootstrap alert classes
# ---------------------------------------------------------------------------
from django.contrib.messages import constants as messages  # noqa: E402

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
# Behaviour:
#   * If EMAIL_HOST_USER + EMAIL_HOST_PASSWORD are set in the environment,
#     real SMTP is used (Gmail by default — change EMAIL_HOST for others).
#   * Otherwise the console backend prints e-mails to the runserver terminal,
#     so development never fails because of missing credentials.
#
# Quick Gmail setup (PowerShell, current shell only):
#   $env:EMAIL_HOST_USER="senin.adresin@gmail.com"
#   $env:EMAIL_HOST_PASSWORD="xxxx xxxx xxxx xxxx"   # Google App Password
#   python manage.py runserver

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').replace(' ', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '1') == '1'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', '0') == '1'
EMAIL_TIMEOUT = 15

# Admin > Site ayarları e-postası yoksa bu adrese düşer (Render ortam değişkeni).
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL', '').strip()

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'Onmer Yemek <{EMAIL_HOST_USER or "info@onmeryemek.com"}>',
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ---------------------------------------------------------------------------
# Site-wide branding constants used by the `site_settings` context processor
# ---------------------------------------------------------------------------
SITE_NAME = 'Onmer Yemek Organizasyon'
SITE_TAGLINE = 'Premium Catering & Toplu Yemek Hizmetleri'
SITE_PHONE = '+90 555 123 45 67'
SITE_WHATSAPP = '905551234567'
SITE_EMAIL = 'info@onmeryemek.com'
SITE_ADDRESS = 'Kadıköy, İstanbul, Türkiye'
SITE_SOCIAL = {
    'instagram': 'https://instagram.com/onmeryemek',
    'facebook': 'https://facebook.com/onmeryemek',
    'twitter': 'https://twitter.com/onmeryemek',
    'youtube': 'https://youtube.com/@onmeryemek',
}
