from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404
import re
import logging
import os
import mimetypes
import requests
from requests.exceptions import RequestException

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
        self.api_key = os.environ.get('CLOUDINARY_API_KEY') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY')
        self.api_secret = os.environ.get('CLOUDINARY_API_SECRET') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET')
        
        # Log what we're using for debugging
        logger.info(f"Cloudinary middleware initialized with cloud_name: {self.cloud_name}")
        
        # Check if all required credentials are available
        self.is_cloudinary = all([
            'cloudinary' in getattr(settings, 'DEFAULT_FILE_STORAGE', ''),
            self.cloud_name,
            self.api_key,
            self.api_secret
        ])
        
        if not self.is_cloudinary:
            logger.warning("Cloudinary configuration incomplete - some credentials missing")
            missing = []
            if not self.cloud_name:
                missing.append("CLOUD_NAME")
            if not self.api_key:
                missing.append("API_KEY")
            if not self.api_secret:
                missing.append("API_SECRET")
            if missing:
                logger.warning(f"Missing Cloudinary credentials: {', '.join(missing)}")
        
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
                cloudinary_path = file_path
                
                # Handle product images with or without the 'products/' prefix
                if not cloudinary_path.startswith('products/') and 'product' in request.path.lower():
                    cloudinary_path = f"products/{cloudinary_path}"
                
                cloudinary_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{cloudinary_path}"
                logger.info(f"Trying Cloudinary URL: {cloudinary_url}")
                
                try:
                    # Check if the file exists on Cloudinary
                    head_response = requests.head(cloudinary_url, timeout=5)
                    
                    if head_response.status_code == 200:
                        return HttpResponseRedirect(cloudinary_url)
                    else:
                        logger.warning(f"File not found on Cloudinary: {cloudinary_url} (Status: {head_response.status_code})")
                        
                        # Try alternative paths for Cloudinary
                        alt_paths = []
                        
                        # Try with/without products/ prefix
                        if cloudinary_path.startswith('products/'):
                            alt_paths.append(cloudinary_path[9:])  # Remove 'products/'
                        else:
                            alt_paths.append(f"products/{cloudinary_path}")
                            
                        # Try without any file extension
                        base_path = cloudinary_path.rsplit('.', 1)[0] if '.' in cloudinary_path else cloudinary_path
                        alt_paths.append(base_path)
                        
                        # Try alternative paths
                        for alt_path in alt_paths:
                            alt_url = f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{alt_path}"
                            try:
                                alt_response = requests.head(alt_url, timeout=3)
                                if alt_response.status_code == 200:
                                    logger.info(f"Found at alternative Cloudinary path: {alt_url}")
                                    return HttpResponseRedirect(alt_url)
                            except RequestException as e:
                                logger.warning(f"Error checking alternative Cloudinary path {alt_url}: {str(e)}")
                except RequestException as e:
                    logger.warning(f"Error checking Cloudinary: {str(e)}")
            else:
                logger.warning(f"Cloudinary not properly configured - falling back to local storage")
            
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
        return response
