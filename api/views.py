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
        
        if response.status_code != 200:
            raise Http404(f"File not found at {s3_url}")
        
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
        raise Http404(f"Error fetching file: {str(e)}")
