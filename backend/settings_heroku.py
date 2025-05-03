import os
import dj_database_url
from .settings_prod import *

# Heroku database configuration
DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True)

# Allow Heroku host
ALLOWED_HOSTS = ['.herokuapp.com', 'koshimart.com', 'www.koshimart.com']

# Configure static files for Heroku
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files should use Amazon S3 for Heroku
if 'AWS_ACCESS_KEY_ID' in os.environ:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'koshimart-media')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    
    # Media settings
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Set the dyno count
WEB_CONCURRENCY = os.environ.get('WEB_CONCURRENCY', 3)

# CORS settings for Heroku
CORS_ALLOWED_ORIGINS = [
    "https://koshimart.com",
    "https://www.koshimart.com",
    "https://koshimart-frontend.vercel.app"
]

CSRF_TRUSTED_ORIGINS = [
    "https://koshimart.com",
    "https://www.koshimart.com",
    "https://koshimart-frontend.vercel.app"
]

# Security middleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static file compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Ensure SSL connection
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True 