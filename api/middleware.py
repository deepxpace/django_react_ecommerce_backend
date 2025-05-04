from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
import re
import logging
import os

logger = logging.getLogger(__name__)

class CloudinaryMediaRedirectMiddleware:
    """
    Simple middleware to redirect media URLs to Cloudinary
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Keep track of cloud name
        self.cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        # Keep track of media root
        self.media_root = settings.MEDIA_ROOT

    def __call__(self, request):
        # Check if it's a media URL
        if request.path.startswith('/media/'):
            # Extract the file path
            file_path = request.path[7:]  # Remove '/media/'
            
            # Build Cloudinary URL
            cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{file_path}"
            
            # Always redirect to Cloudinary
            return HttpResponseRedirect(cloudinary_url)
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response
