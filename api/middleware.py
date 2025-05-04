from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
import re
import logging
import os

logger = logging.getLogger(__name__)

class CloudinaryMediaRedirectMiddleware:
    """
    Middleware to redirect media URLs to Cloudinary with proper formatting
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Get Cloudinary cloud name from settings
        self.cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', 'deepsimage')
        logger.info(f"CloudinaryMediaRedirectMiddleware initialized with cloud_name: {self.cloud_name}")

    def __call__(self, request):
        # Check if it's a media URL
        if request.path.startswith('/media/'):
            # Extract the file path
            file_path = request.path[7:]  # Remove '/media/'
            
            # Log the request for debugging
            logger.info(f"Media request detected for: {file_path}")
            
            # Build Cloudinary URL - use format that works for product images
            if file_path.startswith('products/'):
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{file_path}"
            else:
                # If it's not explicitly in the products folder but likely is a product
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/products/{file_path}"
            
            logger.info(f"Redirecting to Cloudinary URL: {cloudinary_url}")
            return HttpResponseRedirect(cloudinary_url)
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response
