import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(override=True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent #Настройка котороая содержит путь до текущего приложения
#Нужен для построения абсолютных путей

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Специальный секретный путь используемый для криптографических подписей
# Нельзя загружать в удаленный репозиторий
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv('DEBUG') else False #Режим отладки

ALLOWED_HOSTS = []#Список доменных имен которые могут обслуживаться нашим приложением


BASE_DIR = Path(__file__).resolve().parent.parent #Настройка котороая содержит путь до текущего приложения
#Нужен для построения абсолютных путей


# Application definition
#Список приложений
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'mailing',
]

#Список приложений предосталяемых промежуточное ПО,которое обрабатывает входящие запрсы и исходящие ответы
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls" #Путь до модуля с маршрутами

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application" #Путь к WSGI приложениям,точа входа для совместимости с WSGI серверами


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#Настройка для подключения к базе данных
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv('NAME'),
        "USER": os.getenv('USER'),
        "PASSWORD": os.getenv('PASSWORD'),
        'HOST': os.getenv('HOST'),
        'PORT': os.getenv('PORT')
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
#Список валидаторов, который используется для проверки надежности паролей пользователей
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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us" #Язык для проекта

TIME_ZONE = "Europe/Moscow" #Часовая зона для проекта

USE_I18N = True #Поддержка интернацинализации
USE_L18N = True #Поддержка локализации
USE_TZ = True #Поддержка временных зон


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/" #Маршрут для доступа к статике
STATICFILES_DIRS = [BASE_DIR / 'static'] #Список директорий на диске из которых подгружаются статические файлы

MEDIA_URL = '/media/' #Маршрут для доступа к медиа-файлам
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"