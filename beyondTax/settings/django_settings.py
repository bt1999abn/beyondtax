import logging
import os

from beyondTax.settings.base import BASE_DIR, env
from . import base as base_settings


SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')
IS_LIVE = env("IS_LIVE")

ALLOWED_HOSTS = ["localhost", "stage-api.beyondtaxindia.com"]

PROJECT_APPS = [
    'accounts',
    'beyondTaxServices',
    'blogs',
    'payments',
    'services.incomeTax',
    'workOrder',
]

# Application definition
INSTALLED_APPS = [
    'shared.libs.external.jet.apps.JetAppConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',



    # External packages
    'storages',
    'corsheaders',
    'django_filters',
    'django_cleanup.apps.CleanupConfig',
    'rest_framework',
    'knox',
    'rangefilter',
    'ckeditor',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'drf_yasg',

] + PROJECT_APPS + [    # Config
    'beyondTax.apps.BoilerPlateConfig',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication','rest_framework.authentication'
                                                                       '.SessionAuthentication'),
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'beyondTax.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "templates",
            BASE_DIR / "services/incomeTax/templates"
        ],
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

WSGI_APPLICATION = 'beyondTax.wsgi.application'
AUTH_USER_MODEL = 'accounts.User'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': env.db_url("DATABASE_URL")
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = False

USE_L10N = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/


MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
MEDIA_ROOT = BASE_DIR / 'media'


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ['https://*.beyondtaxindia.com']

INJECTION_MAPPINGS = PROJECT_APPS + ["shared"]

PRELOAD_ALPHAID_LIMIT = 100000

DATETIME_INPUT_FORMATS = base_settings.BASE_INPUT_DATETIME_FORMATS
TIME_INPUT_FORMATS = base_settings.BASE_TIME_INPUT_FORMATS
X_FRAME_OPTIONS = "SAMEORIGIN"

CKEDITOR_UPLOAD_PATH = "uploads/"

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'

GOOGLE_OAUTH2_CLIENT_ID = "617719846999-tl7ep6u0j6356pf1g38t3nvrtrd4v1vg.apps.googleusercontent.com"
GOOGLE_OAUTH2_CLIENT_SECRET = "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"

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'test9871798695@gmail.com'
EMAIL_HOST_PASSWORD = 'bszs aazu jhqt kyjn'