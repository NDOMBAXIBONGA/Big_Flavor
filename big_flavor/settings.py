import os
import dj_database_url
from pathlib import Path
#from dotenv import load_dotenv # Devo comentar em desenvolvimento
#load_dotenv()  # Carrega variáveis do .env Devo comentar em desenvolvimento

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-chave-temporaria-dev'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
DEBUG = True
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1', 
    'big-flovar.up.railway.app',  # SEU DOMÍNIO RAILWAY
    '.railway.app',  # Todos subdomínios Railway
]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://big-flovar.up.railway.app',
    'https://*.railway.app',
    'https://*.up.railway.app',
]

# Se estiver usando HTTPS (Railway usa)
CSRF_COOKIE_SECURE = True # Devo comentar em desemvolvimento
SESSION_COOKIE_SECURE = True

# CORS settings (se estiver fazendo requisições de outros domínios)
CORS_ALLOWED_ORIGINS = [
    "https://big-flovar.up.railway.app",
    "https://*.railway.app",
]

# Ou permitir todos (apenas para desenvolvimento)
CORS_ALLOW_ALL_ORIGINS = True  # Cuidado em produção!


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Devo comentar em desenvolvimento
    'django.contrib.staticfiles',
    # suas apps personalizadas aqui

    'balanco',
    'blog',
    'carinho',
    'conta',
    'contacto',
    'index',
    'menu',
    'sobre',
]

# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',  # ← Adicione mas devo comentar em Desenvolvimento
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # ← Adicione mas devo comentar em Desenvolvimento
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuração do cache middleware
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutos # Devo comentar em Desenvolvimento
CACHE_MIDDLEWARE_KEY_PREFIX = 'site'

ROOT_URLCONF = 'big_flavor.urls'

# settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        #'APP_DIRS': True, # Devo comentar antes de fazer a atualizacao no servidor
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'index.context_processors.videos_context',
                'index.context_processors.dashboard_stats'
            ],
            'loaders': [
                # Cache de templates em produção mas devo comentar em Desenvolvimento
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
           ],
        },
    },
]

WSGI_APPLICATION = 'big_flavor.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:FXCXRkozcXVYOTXNXpgjXXECikZgviaw@interchange.proxy.rlwy.net:24064/railway',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

"""# DESENVOLVIMENTO (Local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 60,
    }
}"""
   
# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379',
    }
}

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379') # Devo comentar em Desenvolvimento

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # Note: backend diferente
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',  # Agora sim funciona
            'IGNORE_EXCEPTIONS': True,
        }
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

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'Africa/Luanda'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de autenticação
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Configurações de sessão
SESSION_COOKIE_AGE = 1209600  # 2 semanas em segundos

# Adicionar no settings.py
CONTACT_EMAIL = 'seu-email@dominio.com'

# Configurações de email (opcional)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.seu-servidor.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@dominio.com'
EMAIL_HOST_PASSWORD = 'sua-senha'
DEFAULT_FROM_EMAIL = 'seu-email@dominio.com'

# ... resto das configurações ...

# Adicionar no settings.py
ADMIN_EMAIL = 'admin@seusite.com'

# User model
AUTH_USER_MODEL = 'conta.Usuario'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' # Devo comentar em Desenvolvimento
#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage' # Devo comnetar em Producao
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage' # Devo comentar em Desenvolvimento

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')