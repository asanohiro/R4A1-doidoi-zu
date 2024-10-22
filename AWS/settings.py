# AWS/settings.py
from pathlib import Path
import environ
import os
from dotenv import load_dotenv
import pymysql

# pymysql.install_as_MySQLdb()
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent

# .envファイルからの読み込み
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))

# load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*',
                 'https://327f-153-246-98-230.ngrok-free.app',
                 'https://ee1f-153-246-98-230.ngrok-free.app',
                 'https://f920-153-246-98-230.ngrok-free.app',
                 'https://7a0a-153-246-98-230.ngrok-free.app',
                 'cc96-153-246-98-230.ngrok-free.app',
                 'https://0142-153-246-98-230.ngrok-free.app',
                 'https://e98f-153-246-98-230.ngrok-free.app'
                 ]


CSRF_TRUSTED_ORIGINS = [
    'https://2f79-240a-61-60d3-d79e-2800-9c7-dd24-e684.ngrok-free.app',
    'https://327f-153-246-98-230.ngrok-free.app',
    'https://ee1f-153-246-98-230.ngrok-free.app',
    'https://f920-153-246-98-230.ngrok-free.app',
    'https://7a0a-153-246-98-230.ngrok-free.app',
    'https://cc96-153-246-98-230.ngrok-free.app',
    'https://0142-153-246-98-230.ngrok-free.app',
    'https://e98f-153-246-98-230.ngrok-free.app'
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',  # ここに追加
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # 他のミドルウェア
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'AWS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'app/templates'],
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

WSGI_APPLICATION = 'AWS.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASSWORD'),
        'HOST': env('DATABASE_HOST'),  # あるいは、MySQLサーバーのホスト名
        'PORT': env('DATABASE_PORT'),  # あるいは、使用しているポート番号
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'app': {  # 'app'は実際のアプリケーション名
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AWS credentials
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_REGION = env('AWS_REGION')
AWS_S3_REGION_NAME = env('AWS_REGION')
GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY')

# S3をデフォルトのファイルストレージに設定
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# 画像やファイルのURLを取得するための設定
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'