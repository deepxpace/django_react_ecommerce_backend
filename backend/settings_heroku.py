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

# Add Cloudinary apps
INSTALLED_APPS += [
    'cloudinary',
    'cloudinary_storage',
]

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'deepsimage',
    'API_KEY': '855942689195483',
    'API_SECRET': 'pRzA_eY3dPJeiFiQn88LUa1gGA4',
}

# Use Cloudinary for media storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Set the dyno count
WEB_CONCURRENCY = os.environ.get('WEB_CONCURRENCY', 3)

# CORS settings for Heroku
CORS_ALLOW_ALL_ORIGINS = False  # Keep security by not allowing all origins
CORS_ALLOW_CREDENTIALS = True   # Allow credentials (cookies, authorization headers)

# Make sure the frontend domains are added to CORS allowed origins
CORS_ALLOWED_ORIGINS = [
    "https://koshimart.com",
    "https://www.koshimart.com",
    "https://koshimart-frontend.vercel.app",
    "https://koshimart-store.vercel.app",
    "https://koshimart.vercel.app",
    # Add all possible Vercel domains
    "https://koshimart-git-main.vercel.app",
    "https://koshimart-web.vercel.app",
    "https://koshimart-frontend-git-main.vercel.app", 
    # Development environments
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    # Add your specific Vercel deployment URL here if not covered above
    "https://django-react-ecommerce-frontend-1.vercel.app"
]

# Add Cloudinary to CORS allowed origins
CORS_ALLOWED_ORIGINS += ["https://res.cloudinary.com"]

# Enable CORS for all API endpoints, not just media
CORS_URLS_REGEX = r'^.*$'

# These headers are needed for proper image loading
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
    "range",  # Important for video/large file streaming
]

# Enable response compression for better performance
MIDDLEWARE.append('django.middleware.gzip.GZipMiddleware')

# Make sure Cloudinary is properly set up for media storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Set DEBUG to False for production
DEBUG = False

# Add the middleware to the MIDDLEWARE list
MIDDLEWARE.insert(2, 'api.middleware.CloudinaryMediaRedirectMiddleware')

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