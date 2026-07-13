from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import os
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "authentification",
    "entreprise",
    "clients",
    "fournisseurs",
    "categories",
    "produits",
    "stock",
    "ventes",
    "paiements",
    "achats",
    "prets",
    "historique",
    "dashboard",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "isowo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "isowo.wsgi.application"

# Base de données MySQL (Railway en prod, local en dev)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": os.getenv("DB_NAME", "isowo"),
#         "USER": os.getenv("DB_USER", "root"),
#         "PASSWORD": os.getenv("DB_PASSWORD", ""),
#         "HOST": os.getenv("DB_HOST", "localhost"),
#         "PORT": os.getenv("DB_PORT", "3306"),
#         "OPTIONS": {
#             "charset": "utf8mb4",
#             "ssl": {"ssl-mode": "REQUIRED"} if os.getenv("DB_SSL", "False") == "True" else {},
#         },
#     }
# }

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    parsed = urllib.parse.urlparse(DATABASE_URL)
    if parsed.scheme.startswith("postgres"):
        DATABASES = {
            "default": dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                ssl_require=True,
            )
        }
    elif parsed.scheme.startswith("mysql"):
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": parsed.path.lstrip("/"),
                "USER": parsed.username,
                "PASSWORD": parsed.password,
                "HOST": parsed.hostname,
                "PORT": str(parsed.port or 3306),
                "OPTIONS": {
                    "charset": "utf8mb4",
                },
            }
        }
    else:
        DATABASES = {
            "default": dj_database_url.parse(DATABASE_URL)
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "isowo"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Porto-Novo"
USE_I18N = True
USE_TZ = True

# Fichiers statiques
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# CORS
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True

AUTH_USER_MODEL = "authentification.Utilisateur"

# Email
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com"))
EMAIL_PORT = int(os.getenv("EMAIL_PORT", os.getenv("BREVO_SMTP_PORT", "587")))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", os.getenv("BREVO_SMTP_USERNAME", ""))
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", os.getenv("BREVO_SMTP_PASSWORD", ""))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", os.getenv("EMAIL_FROM", "noreply@isowo.com"))
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SMTP_HOST = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
BREVO_SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT", "587"))
BREVO_SMTP_USERNAME = os.getenv("BREVO_SMTP_USERNAME", EMAIL_HOST_USER)
BREVO_SMTP_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD", EMAIL_HOST_PASSWORD)
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Isowo")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")