from Ideconference.settings import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'conference',
        'USER': 'root',
        'PASSWORD': 'r00tPasswd123',
        'HOST': 'db',
        'PORT': 3306,
    },
    'api': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db/apidb2.sqlite3'),
    }
}

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '743751098666-ou4nsoppkv28hdrftf0c0t2236u38a5i.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'oIfRAHtAhxeCtZYDhh1ojVsv'
