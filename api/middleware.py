from django.conf import settings
from django.http import HttpResponseRedirect
import re
import logging
import os

logger = logging.getLogger(__name__)

class CloudinaryMediaRedirectMiddleware:
    """
    Middleware to redirect media URLs directly to Cloudinary
    for better performance. This avoids the multiple lookups
    in the proxy view for simple media requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Regex to match media URLs (only jpg, png, webp, avif, gif)
        self.media_pattern = re.compile(r'^/media/(.+\.(jpg|jpeg|png|webp|avif|gif))$', re.IGNORECASE)
        
        # First try environment variables, then settings
        self.cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        
        # Log what we're using for debugging
        logger.info(f"Cloudinary middleware initialized with cloud_name: {self.cloud_name}")
        
        self.is_cloudinary = 'cloudinary' in getattr(settings, 'DEFAULT_FILE_STORAGE', '') and self.cloud_name

    def __call__(self, request):
        # Only try to redirect if Cloudinary is configured
        if self.is_cloudinary:
            path = request.path_info
            match = self.media_pattern.match(path)
            
            if match:
                file_path = match.group(1)
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{file_path}"
                logger.info(f"Redirecting {path} directly to Cloudinary: {cloudinary_url}")
                return HttpResponseRedirect(cloudinary_url)
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response 