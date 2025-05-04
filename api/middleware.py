from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
import re
import logging
import os
import requests

logger = logging.getLogger(__name__)

class CloudinaryMediaRedirectMiddleware:
    """
    DISABLED middleware - now simply passes requests through to avoid redirect loops
    Media files are now handled directly by the media_proxy view
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Get Cloudinary cloud name from settings
        self.cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', 'deepsimage')
        logger.info(f"CloudinaryMediaRedirectMiddleware initialized with cloud_name: {self.cloud_name}")
        logger.info("NOTE: This middleware is now disabled and passes all requests through")

    def __call__(self, request):
        # DISABLED - now we simply pass the request through without redirecting
        # The media_proxy view handles serving media files directly
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response
        
    def serve_image_directly(self, file_path):
        """
        DEPRECATED: Now handled by media_proxy view
        """
        logger.info(f"serve_image_directly called but is now deprecated")
        # Return a placeholder image
        placeholder_svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">'
            b'<rect width="200" height="200" fill="#f0f0f0"/>'
            b'<text x="50%" y="50%" font-family="Arial" font-size="14" text-anchor="middle" fill="#999">Middleware Disabled</text>'
            b'</svg>'
        )
        return HttpResponse(placeholder_svg, content_type='image/svg+xml')
