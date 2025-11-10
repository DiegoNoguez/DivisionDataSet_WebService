import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

#  Usar variable de entorno para seguridad
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-for-render')

# DEBUG debe ser False en producción
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

#  Hosts permitidos para Render
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'https://divisiondataset-webservice.onrender.com',  # Dominio de Render
]

#  Agregar el hostname externo de Render si existe
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'processor',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Primero
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  #  Para archivos estáticos en Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dataset_processor.urls'

#  CORS configurado para producción
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://divisiondataset-webservice-front.onrender.com/",
]

#  Permitir todos los orígenes en desarrollo, pero no en producción
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo True si DEBUG es True

#  Métodos permitidos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

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

#  Base de datos para Render
#DATABASES = {
#    'default': dj_database_url.config(
#        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
#        conn_max_age=600
#    )
#}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

#  Configuración CRÍTICA para archivos estáticos en Render
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

#  WhiteNoise para servir archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#  Configuración de seguridad para producción
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True