from django.shortcuts import render
import requests
from django.http import HttpResponse, Http404
from django.conf import settings

# Create your views here.

def proxy_s3_media(request, path):
    """
    Proxy for S3 media files to bypass CORS restrictions.
    This fetches and serves files from S3 through the Django backend.
    """
    if not path:
        raise Http404("No path specified")
    
    # Build the full S3 URL
    s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{path}"
    
    try:
        # Fetch the file from S3
        response = requests.get(s3_url, stream=True)
        
        # If S3 returns a 404 or other error, generate a placeholder
        if response.status_code != 200:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"S3 returned status {response.status_code} for URL {s3_url}")
            
            # Return a placeholder image
            # Extract a name from the path to personalize the placeholder
            path_parts = path.split('/')
            filename = path_parts[-1] if path_parts else 'unknown'
            name_part = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
            
            # Generate a placeholder URL
            placeholder_url = f"https://placehold.co/400x400/EEE/999?text={name_part[:10]}"
            
            # Fetch the placeholder
            placeholder_response = requests.get(placeholder_url, stream=True)
            
            if placeholder_response.status_code == 200:
                return HttpResponse(
                    placeholder_response.content,
                    content_type=placeholder_response.headers.get('Content-Type', 'image/jpeg')
                )
            else:
                # If even the placeholder fails, return a simple 1x1 transparent GIF
                transparent_gif = (
                    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
                    b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
                    b'\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
                )
                return HttpResponse(transparent_gif, content_type='image/gif')
        
        # Determine content type from response or fall back to application/octet-stream
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        # Create Django response with the same content
        django_response = HttpResponse(
            response.content,
            content_type=content_type
        )
        
        # Add caching headers
        django_response['Cache-Control'] = 'max-age=86400'  # Cache for a day
        
        return django_response
    
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error proxying S3 file: {str(e)}")
        
        # Return a fallback image for any errors
        transparent_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
        )
        return HttpResponse(transparent_gif, content_type='image/gif')
