from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
import re
import logging
import os
import requests

logger = logging.getLogger(__name__)

class CloudinaryMediaRedirectMiddleware:
    """
    Middleware to handle media URLs by either directly serving the image
    or redirecting to Cloudinary with proper formatting
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
            
            # Check if the request has already been redirected (circular loop detection)
            redirect_count = request.META.get('HTTP_X_REDIRECT_COUNT', 0)
            try:
                redirect_count = int(redirect_count)
            except ValueError:
                redirect_count = 0
                
            # If we've redirected too many times, serve the image directly instead
            if redirect_count > 2:
                logger.warning(f"Detected redirect loop for {file_path}. Serving image directly.")
                return self.serve_image_directly(file_path)
            
            # Log the request for debugging
            logger.info(f"Media request detected for: {file_path}")
            
            # Build Cloudinary URL - use format that works for product images
            if file_path.startswith('products/'):
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{file_path}"
            else:
                # If it's not explicitly in the products folder but likely is a product
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/products/{file_path}"
            
            logger.info(f"Redirecting to Cloudinary URL: {cloudinary_url}")
            
            # Add a header to track redirect count
            response = HttpResponseRedirect(cloudinary_url)
            response['X-Redirect-Count'] = str(redirect_count + 1)
            return response
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response
        
    def serve_image_directly(self, file_path):
        """
        Instead of redirecting, fetch and serve the image directly
        This prevents redirect loops
        """
        logger.info(f"Serving image directly: {file_path}")
        
        # Try multiple possible image paths
        try:
            # Try Cloudinary first
            if file_path.startswith('products/'):
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{file_path}"
            else:
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/products/{file_path}"
                
            logger.info(f"Fetching image from: {cloudinary_url}")
            response = requests.get(cloudinary_url, stream=True, timeout=5)
            
            if response.status_code == 200:
                # Success! Return the image content directly
                content_type = response.headers.get('Content-Type', 'image/jpeg')
                django_response = HttpResponse(
                    response.content,
                    content_type=content_type
                )
                django_response['Cache-Control'] = 'max-age=86400'  # Cache for 24 hours
                return django_response
        except Exception as e:
            logger.error(f"Error serving image directly: {str(e)}")
        
        # If we get here, we couldn't fetch the image
        # Return a placeholder image
        placeholder_svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">'
            b'<rect width="200" height="200" fill="#f0f0f0"/>'
            b'<text x="50%" y="50%" font-family="Arial" font-size="14" text-anchor="middle" fill="#999">Image Not Found</text>'
            b'</svg>'
        )
        return HttpResponse(placeholder_svg, content_type='image/svg+xml')
