import os
import sys
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-test-key-for-local-dev')
DEBUG = env('DEBUG')

# Vercel deployment detection
IS_VERCEL = bool(os.environ.get('VERCEL'))

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0', '.vercel.app', '.now.sh', 'testserver'])
for _host_suffix in ['.vercel.app', '.now.sh', 'testserver']:
    if _host_suffix not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host_suffix)

CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=[
        'https://*.vercel.app',
        'https://*.now.sh',
        'http://127.0.0.1:8000',
        'http://localhost:8000',
    ]
)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'content',
    'publishing',
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
]

ROOT_URLCONF = 'core_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core_project.wsgi.application'

# Database Configuration
# Priority: DATABASE_URL -> Explicit DB_* settings -> SQLite fallback
import socket

def _resolve_db_host(host_str: str) -> str:
    """
    Safeguards against Windows/ISP DNS packet corruption for cloud databases.
    Directly maps Aiven cloud domains to IP to guarantee 100% reliable psycopg2 connection.
    """
    if not host_str or host_str in ('localhost', '127.0.0.1', '0.0.0.0'):
        return host_str
    if 'pg-38f7fc77-chuksejiogu1920-b280.g.aivencloud.com' in host_str:
        return '178.62.238.216'
    if 'aivencloud.com' in host_str:
        try:
            import requests
            resp = requests.get(f"https://dns.google/resolve?name={host_str}", timeout=4)
            if resp.status_code == 200:
                for ans in resp.json().get('Answer', []):
                    if ans.get('type') == 1 and ans.get('data'):
                        return ans.get('data')
        except Exception:
            pass
    return host_str

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif env('DATABASE_URL', default=''):
    _db_conf = env.db('DATABASE_URL')
    if 'HOST' in _db_conf:
        _db_conf['HOST'] = _resolve_db_host(_db_conf['HOST'])
    DATABASES = {
        'default': _db_conf
    }
elif env('DB_ENGINE', default='') == 'django.db.backends.postgresql':
    _host = _resolve_db_host(env('DB_HOST', default='127.0.0.1'))
    DATABASES = {
        'default': {
            'ENGINE': env('DB_ENGINE'),
            'NAME': env('DB_NAME', default='fbscheduler'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default='postgres'),
            'HOST': _host,
            'PORT': env('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TIME_ZONE', default='Africa/Lagos')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
if IS_VERCEL:
    MEDIA_ROOT = '/tmp/media'
    if 'default' in DATABASES:
        DATABASES['default']['CONN_MAX_AGE'] = 0
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Vercel Cron Security Secret (optional verification)
CRON_SECRET = env('CRON_SECRET', default='')

# Editorial Review & Forwarding via Zenia Email Provider
REVIEW_EMAIL = env('REVIEW_EMAIL', default='christian.eze.241801@unn.edu.ng')
ZENIA_EMAIL_API_URL = env('ZENIA_EMAIL_API_URL', default='https://zenia-email-api.vercel.app/api/v1/register_email')
MORNING_DISPATCH_HOUR = env.int('MORNING_DISPATCH_HOUR', default=3)
EVENING_DISPATCH_HOUR = env.int('EVENING_DISPATCH_HOUR', default=17)

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = env('TIME_ZONE', default='Africa/Lagos')

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # 3:00 AM WAT: Curate Morning Prayer & Dispatch to Christian's Email for early review (ready for 6am posting)
    'dispatch-morning-prayer-email-daily': {
        'task': 'content.tasks.dispatch_morning_prayer_email_task',
        'schedule': crontab(hour=MORNING_DISPATCH_HOUR, minute=0),
    },
    # 5:00 PM WAT: Curate Evening Bible Study & Dispatch to Christian's Email for evening review & posting
    'dispatch-evening-bible-study-email-daily': {
        'task': 'content.tasks.dispatch_evening_bible_study_email_task',
        'schedule': crontab(hour=EVENING_DISPATCH_HOUR, minute=0),
    },
    # 12:00 PM WAT: Autonomous Midday Reflection Reel (9:16 Video + Voiceover)
    'generate-daily-reflection-reel': {
        'task': 'content.tasks.generate_daily_reflection_reel_task',
        'schedule': crontab(hour=12, minute=0),
    },
}

# External APIs
META_APP_ID = env('META_APP_ID', default='')
META_APP_SECRET = env('META_APP_SECRET', default='')
META_PAGE_ID = env('META_PAGE_ID', default='')
META_PAGE_ACCESS_TOKEN = env('META_PAGE_ACCESS_TOKEN', default='')
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')
HUGGINGFACE_API_KEY = env('HUGGINGFACE_API_KEY', default='')
