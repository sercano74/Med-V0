# ==================================================
# ====================  ACCESO =====================
# ==================================================
# En CMD entrar al:
#* A00_Env\scripts\activate
#* python manage.py runserver
# ==================================================
# usuario   : admin
# kw        : 123
# email     :
# ==================================================
# usuario   : sercano
# kw        : 123
# email     :
# rol       : Gerencia
# ==================================================

# Limpia la caché de Django: En algunos casos, puede ser útil limpiar la caché de Django:
#* python manage.py clean_pyc.
# Este comando verifica la configuración de tu proyecto y te mostrará cualquier error o advertencia.
#* python manage.py check


import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-q94ue$4ao6+z+xhpszyj&t9rvt#$ws)&pnnxxs5xknmq%a1%tx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'A10_Usu',
    'A20_Hrs',
    'A30_Fic',
    'A31_Con',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',
    'django_select2',
]

SITE_ID = 1

# ACCOUNT_FORMS = { 'signup': 'A10_Usu.forms.PacienteSignupForm',}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'Med.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

WSGI_APPLICATION = 'Med.wsgi.application'


SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True #Recomendado por seguridad
# Recuerda cambiar SESSION_COOKIE_SECURE y SESSION_COOKIE_HTTPONLY a True en producción, cuando uses HTTPS.

CSRF_COOKIE_SECURE = False
# Recuerda cambiarlo a True en producción.

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# Para producción, se recomienda usar db o cache.



# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'A10_Usu.CustomUser'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'es' # Para que Django use el idioma español
USE_I18N = True #Para que Django use la configuración de idioma
USE_THOUSAND_SEPARATOR = True # Para que Django use separadores de miles en los números

# TIME_ZONE = 'UTC'
TIME_ZONE = 'America/Santiago'
USE_TZ = True #Para que Django use la zona horaria definida en TIME_ZONE

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = '/static/'
# * <img src="{% static 'my-app/example.jpg' %}" alt="No image">

#Esta configuración le dice a Django dónde están tus archivos estáticos durante el desarrollo.
# Es una lista de directorios donde Django buscará archivos estáticos que luego copiará a STATIC_ROOT.
# Aquí es donde debes incluir la carpeta static de tus apps.
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),  # Archivos estáticos generales del proyecto
                    os.path.join(BASE_DIR, 'A10_Usu', 'static'), # Archivos estáticos de la app A10_Usu
                    os.path.join(BASE_DIR, 'A20_Hrs', 'static'), # Archivos estáticos de la app A20_Hrs
                    os.path.join(BASE_DIR, 'A31_Con', 'static'), # Archivos estáticos de la app A20_Hrs
                ]

# Esta configuración define la carpeta final donde se almacenarán todos tus archivos estáticos
# después de ejecutar python manage.py collectstatic.  Esta carpeta es la que tu servidor web (Nginx, Apache, etc.)
# servirá en producción.  Nunca debes poner tus archivos estáticos directamente en STATIC_ROOT.
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root') #  python manage.py collectstatic

# Ejecutar python manage.py collectstatic en producción para recopilar todos los archivos estáticos en una sola carpeta.
# Esto copiará todos los archivos estáticos desde las carpetas especificadas en STATICFILES_DIRS
# (incluyendo tu imagen calendar.jpeg desde A20_Hrs/static/images) a la carpeta STATIC_ROOT.



MEDIA_URL = '/media/'     # Ruta para acceder desde web
# MEDIA_URL = 'https://tu-dominio.com/media/'  # Para producción

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')   # Ruta en el pc


LOGIN_URL = 'account_login'  # Nombre de la URL de allauth
# LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/accounts/redireccion_despues_login/'
LOGOUT_REDIRECT_URL = '/'


# ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_USER_DISPLAY = lambda user: user.username #Como se muestra el usuario, si lo modificaste revisalo
# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
# ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_REDIRECT_URL = 'home'
# ACCOUNT_ADAPTER = 'A10_Usu.adapters.NoNewUsersAccountAdapter'
# ACCOUNT_ADAPTER = 'A10_Usu.adapters.CustomAccountAdapter'


ACCOUNT_FORMS = { 'signup': 'A10_Usu.forms.PacienteSignupForm',}

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' '''ESTO ES PARA UN SERVIDOR DE PRUEBA'''
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ordered.dev.01@gmail.com'
EMAIL_HOST_PASSWORD = 'bedwoujjjskxbvod'



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuración de la sesión
# Con esta configuración, la duración de las variables de sesión se establece a no más de 6 horas. La cookie de sesión expirará después de 6 horas de inactividad. Si deseas que la sesión se renueve en cada solicitud, puedes usar la opción SESSION_SAVE_EVERY_REQUEST = True. Esto hará que la sesión se actualice cada vez que el usuario haga una solicitud, manteniendo la sesión activa mientras el usuario esté interactuando con la aplicación.
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Usa la base de datos para almacenar sesiones
SESSION_COOKIE_AGE = 6 * 60 * 60  # 6 horas
SESSION_SAVE_EVERY_REQUEST = True  # Opcional: Guarda la sesión en cada solicitud

# TODO   Lo BUENO nunca es fácil, lo fácil nunca es BUENO.