# Django settings for sensible_data_service project.

import os
import LOCAL_SETTINGS

DEBUG = True
TEMPLATE_DEBUG = DEBUG



ADMINS = (
     ('Dude', 'dude@rug.com'),
)

MANAGERS = ADMINS
BASE_DIR = LOCAL_SETTINGS.BASE_DIR
ROOT_DIR = LOCAL_SETTINGS.ROOT_DIR
ROOT_URL = LOCAL_SETTINGS.ROOT_URL
BASE_URL = LOCAL_SETTINGS.BASE_URL
DATA_DATABASE = LOCAL_SETTINGS.DATA_DATABASE
DATA_BASE_DIR = LOCAL_SETTINGS.DATA_BASE_DIR
DATA_LOG_DIR = LOCAL_SETTINGS.DATA_LOG_DIR
DATA_BACKUP_DIR = LOCAL_SETTINGS.DATA_BACKUP_DIR
DATABASES = LOCAL_SETTINGS.DATABASES
PLATFORM = LOCAL_SETTINGS.PLATFORM
CONNECTORS = LOCAL_SETTINGS.CONNECTORS
SERVICE_NAME = LOCAL_SETTINGS.SERVICE_NAME

# Make this unique, and don't share it with anybody.
SECRET_KEY = LOCAL_SETTINGS.SECRET_KEY

import djcelery
djcelery.setup_loader()

from connectors.connector_answer import schedule

CELERYBEAT_SCHEDULE = schedule.CELERYBEAT_SCHEDULE

LOGIN_URL = ROOT_URL+'openid/login/'
LOGIN_REDIRECT_URL = ROOT_URL
OPENID_SSO_SERVER_URL = LOCAL_SETTINGS.OPENID_SSO_SERVER_URL
OPENID_USE_EMAIL_FOR_USERNAME = False
AUTHENTICATION_BACKENDS = (
            'django_openid_auth.auth.OpenIDBackend',
            'django.contrib.auth.backends.ModelBackend',
        )

OPENID_CREATE_USERS = True
OPENID_UPDATE_DETAILS_FROM_SREG = False

def failure_handler_function(request, message, status=None, template_name=None, exception=None):
	from django.shortcuts import redirect
	from django.http import HttpResponse
	registration = request.REQUEST.get('registration', False)
	next = request.REQUEST.get('next', '')
	if registration: return redirect(next)
	return redirect('openid_failed')

OPENID_RENDER_FAILURE = failure_handler_function

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['54.229.13.160']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Copenhagen'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ROOT_DIR+'static_root'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = ROOT_URL+'static/'

# Additional locations of static files
STATICFILES_DIRS = (
	ROOT_DIR + 'static',
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.static',
        'django.contrib.auth.context_processors.auth',
)

ROOT_URLCONF = 'sensible_data_service.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sensible_data_service.wsgi.application'

TEMPLATE_DIRS = (
	ROOT_DIR+'templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_openid_auth',
    'bootstrap_toolkit',
    'uni_form',
    'south',
    'connectors',
    'utils',
    'authorization_manager',
    'application_manager',
    'accounts',
    'platform_manager',
    'testing',
    'connectors.connector_funf',
    'connectors.connector_questionnaire',
    'connectors.connector_facebook',
    'connectors.connector_raw',
    'connectors.connector_answer',
    'anonymizer',
    'oauth2app',
    'documents',
    'render',
    'backup',
	'djcelery',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

import hashlib
SESSION_COOKIE_NAME = str(hashlib.sha1(SECRET_KEY).hexdigest())
