import logging
import os

from celery.schedules import crontab

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'ymn*&*r6a+tn@*$ugdintbt+!*3u&!&pcos+zt6$5mn9tacp%)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'currencies',
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

ROOT_URLCONF = 'simple_djangorest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'simple_djangorest.wsgi.application'

# choose sqlite3 only for developmment and debug purposes
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'currency_exchange',
    #     'HOST': 'localhost',
    #     'USER': os.environ.get('EXCHANGERATES_DB_USER', 'postgres'),
    #     'PASSWORD': os.environ.get('EXCHANGERATES_DB_PASS', ''),
    #     'OPTIONS': {
    #         'sslmode': 'disable',
    #     },
    # },
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

EXCHANGERATES_API_APP_ID = os.environ.get('EXCHANGERATES_API_APP_ID', '')
EXCHANGERATES_API_CURRENCIES_URL = f"https://openexchangerates.org/api/currencies.json"
EXCHANGERATES_API_LATEST_URL = f"https://openexchangerates.org/api/latest.json?app_id={EXCHANGERATES_API_APP_ID}"
EXCHANGERATES_API_MAX_RETRIES = 3
EXCHANGERATES_API_RETRY_PAUSE = 5

LOGGING_CONF = {
    'level': logging.DEBUG if DEBUG else logging.ERROR,
    'filename': 'logs.log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s: %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S',
}

logging.basicConfig(**LOGGING_CONF)
logger = logging

REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_BEAT_SCHEDULE = {
    'update_currencies': {
        'task': 'currencies.tasks.update_currencies',
        'schedule': crontab(minute=0, hour=0),  # run every day
    },
}

ACTIVE_CURRENCIES = {
    'Czech Republic Koruna': 'Czech koruna',
    'Euro': 'Euro',
    'Polish Zloty': 'Polish złoty',
    'United States Dollar': 'US dollar',
}

BASE_CURRENCY_CODE = 'USD'
