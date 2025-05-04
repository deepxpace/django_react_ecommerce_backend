from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404
import re
import logging
import os
import mimetypes

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
        
        # Keep track of media root
        self.media_root = settings.MEDIA_ROOT

    def __call__(self, request):
        # Only try to handle if it's a media URL
        path = request.path_info
        match = self.media_pattern.match(path)
        
        if match:
            file_path = match.group(1)
            logger.info(f"Handling media request for {file_path}")
            
            # Try Cloudinary redirection if configured
            if self.is_cloudinary:
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{file_path}"
                logger.info(f"Redirecting {path} to Cloudinary: {cloudinary_url}")
                
                try:
                    # Check if the file exists on Cloudinary
                    import requests
                    head_response = requests.head(cloudinary_url, timeout=2)
                    
                    if head_response.status_code == 200:
                        return HttpResponseRedirect(cloudinary_url)
                    else:
                        logger.warning(f"File not found on Cloudinary: {cloudinary_url}")
                except Exception as e:
                    logger.warning(f"Error checking Cloudinary: {str(e)}")
            
            # If we get here, try serving from local media as fallback
            try:
                local_path = os.path.join(self.media_root, file_path)
                if os.path.exists(local_path) and os.path.isfile(local_path):
                    logger.info(f"Serving file from local media: {local_path}")
                    
                    # Get the content type
                    content_type, _ = mimetypes.guess_type(local_path)
                    # Force AVIF content type if needed
                    if local_path.lower().endswith('.avif'):
                        content_type = 'image/avif'
                    
                    # Serve the file
                    with open(local_path, 'rb') as f:
                        response = HttpResponse(f.read(), content_type=content_type or 'application/octet-stream')
                        response['Content-Disposition'] = f'inline; filename="{os.path.basename(local_path)}"'
                        response['Cache-Control'] = 'max-age=86400'  # Cache for 1 day
                        return response
                else:
                    logger.warning(f"File not found locally: {local_path}")
                    # Fall through to media-proxy
                    return HttpResponseRedirect(f"/media-proxy/{file_path}")
            except Exception as e:
                logger.error(f"Error serving local file: {str(e)}")
                return HttpResponseRedirect(f"/media-proxy/{file_path}")
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response // Test update Sun May  4 04:54:13 CEST 2025
