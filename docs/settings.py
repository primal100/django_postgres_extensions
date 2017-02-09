INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_postgres_extensions'
]

DATABASES = {
    'default': {
        'ENGINE': 'django_postgres_extensions.backends.postgresql',
        'NAME': 'db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': 5432,
    }
}