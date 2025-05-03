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

# Ensure WhiteNoise is properly configured
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Keep local media configuration as fallback
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Amazon S3 Configuration for Heroku
if 'AWS_ACCESS_KEY_ID' in os.environ:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'koshimart-api')
    AWS_S3_REGION_NAME = 'eu-north-1'  # Corrected region - bucket is in eu-north-1 (Stockholm)
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    
    # Media settings for S3
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Set the dyno count
WEB_CONCURRENCY = os.environ.get('WEB_CONCURRENCY', 3)

# CORS settings for Heroku
CORS_ALLOW_ALL_ORIGINS = False  # Set to False for security

CORS_ALLOWED_ORIGINS = [
    "https://koshimart.com",
    "https://www.koshimart.com",
    "https://koshimart-frontend.vercel.app",
    "https://koshimart-store.vercel.app",
    "https://koshimart.vercel.app",  # Add the main Vercel domain
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000"
]

CSRF_TRUSTED_ORIGINS = [
    "https://koshimart.com",
    "https://www.koshimart.com",
    "https://koshimart-frontend.vercel.app",
    "https://koshimart-store.vercel.app",
    "https://koshimart.vercel.app"  # Add the main Vercel domain
]

# Additional CORS settings for handling media files
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Ensure SSL connection
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True 

# Modify logging for Heroku (use stdout instead of file)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
} 