import os
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
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0'])

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
if env('DATABASE_URL', default=''):
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
elif env('DB_ENGINE', default='') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': env('DB_ENGINE'),
            'NAME': env('DB_NAME', default='fbscheduler'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default='postgres'),
            'HOST': env('DB_HOST', default='127.0.0.1'),
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Scan and publish due posts every 5 minutes
    'publish-due-posts-every-5-mins': {
        'task': 'publishing.tasks.publish_due_posts_task',
        'schedule': crontab(minute='*/5'),
    },
    # Autonomous Morning Prayer (05:00 UTC, scheduled for 06:00)
    'generate-morning-prayer-daily': {
        'task': 'content.tasks.generate_morning_prayer_task',
        'schedule': crontab(hour=5, minute=0),
    },
    # Autonomous Midday Reflection Reel (11:00 UTC, scheduled for 12:00)
    'generate-daily-reflection-reel': {
        'task': 'content.tasks.generate_daily_reflection_reel_task',
        'schedule': crontab(hour=11, minute=0),
    },
    # Autonomous Evening Reflection (18:00 UTC, scheduled for 19:00)
    'generate-evening-reflection-daily': {
        'task': 'content.tasks.generate_evening_reflection_task',
        'schedule': crontab(hour=18, minute=0),
    },
    # Daily Facebook Token Health Verification at midnight
    'verify-meta-token-daily': {
        'task': 'publishing.tasks.verify_meta_tokens_task',
        'schedule': crontab(hour=0, minute=15),
    },
}

# External APIs
META_APP_ID = env('META_APP_ID', default='')
META_APP_SECRET = env('META_APP_SECRET', default='')
META_PAGE_ID = env('META_PAGE_ID', default='')
META_PAGE_ACCESS_TOKEN = env('META_PAGE_ACCESS_TOKEN', default='')
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')
HUGGINGFACE_API_KEY = env('HUGGINGFACE_API_KEY', default='')
