from django.shortcuts import render
import requests
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings

# Create your views here.

def proxy_s3_media(request, path):
    """
    Proxy for S3 media files to bypass CORS restrictions.
    This fetches and serves files from S3 through the Django backend.
    """
    if not path:
        raise Http404("No path specified")
    
    # Try different possible image paths
    possible_paths = [
        # Original path as requested
        path,
        
        # Without 'products/' prefix if it exists
        path.replace('products/', '') if path.startswith('products/') else None,
        
        # With 'products/' prefix if not already there
        f"products/{path}" if not path.startswith('products/') else None,
        
        # Try with media/ prefix
        f"media/{path}" if not path.startswith('media/') else None,
        
        # Common variations
        path.replace('_', '-') if '_' in path else None,
        path.replace('-', '_') if '-' in path else None
    ]
    
    # Filter out None values
    possible_paths = [p for p in possible_paths if p]
    
    # Try all possible paths
    last_error = None
    for try_path in possible_paths:
        try:
            # Build the full S3 URL
            s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{try_path}"
            
            # Fetch the file from S3
            response = requests.get(s3_url, stream=True)
            
            if response.status_code == 200:
                # Success! Return the image
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                django_response = HttpResponse(
                    response.content,
                    content_type=content_type
                )
                django_response['Cache-Control'] = 'max-age=86400'
                return django_response
            else:
                last_error = f"S3 returned status {response.status_code} for URL {s3_url}"
        except Exception as e:
            last_error = str(e)
    
    # If we get here, all paths failed
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"All image paths failed for {path}. Last error: {last_error}")
    
    # Try Django's local media folder as a last resort
    try:
        from django.conf import settings
        import os
        
        # Check if the file exists in the media directory
        media_root = settings.MEDIA_ROOT
        
        for local_path in possible_paths:
            local_file_path = os.path.join(media_root, local_path)
            if os.path.exists(local_file_path):
                # File exists in media directory, serve it directly
                with open(local_file_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                import mimetypes
                content_type, _ = mimetypes.guess_type(local_file_path)
                
                django_response = HttpResponse(
                    content,
                    content_type=content_type or 'application/octet-stream'
                )
                django_response['Cache-Control'] = 'max-age=86400'
                return django_response
    except Exception as e:
        logger.error(f"Error checking local media: {str(e)}")
    
    # Generate placeholder as last resort
    try:
        # Extract a name from the path to personalize the placeholder
        path_parts = path.split('/')
        filename = path_parts[-1] if path_parts else 'unknown'
        name_part = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
        
        # Generate a placeholder URL
        placeholder_url = f"https://placehold.co/400x400/EEE/999?text=Image+Pending"
        
        # Fetch the placeholder
        placeholder_response = requests.get(placeholder_url, stream=True)
        
        if placeholder_response.status_code == 200:
            return HttpResponse(
                placeholder_response.content,
                content_type=placeholder_response.headers.get('Content-Type', 'image/jpeg')
            )
    except Exception:
        pass
        
    # If even the placeholder fails, return a simple 1x1 transparent GIF
    transparent_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
        b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
        b'\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
    )
    return HttpResponse(transparent_gif, content_type='image/gif')

def debug_image_paths(request):
    """
    Debug view to list available images and their locations
    """
    try:
        # Get a list of S3 objects
        import boto3
        from django.http import JsonResponse
        from django.conf import settings
        
        # Use the AWS credentials from settings
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
        # Get a list of objects in the bucket
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        max_objects = 100  # Limit to prevent excessive responses
        
        # Get bucket objects
        result = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=max_objects)
        
        # Format the results
        objects = []
        if 'Contents' in result:
            for obj in result['Contents']:
                key = obj['Key']
                # Build the full S3 URL
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
                objects.append({
                    'key': key,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': s3_url,
                    'proxy_url': f"/media-proxy/{key}"
                })
        
        # Also list files from local media directory
        import os
        local_media = []
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
                    local_media.append({
                        'path': rel_path,
                        'size': os.path.getsize(full_path),
                        'url': f"{settings.MEDIA_URL}{rel_path}"
                    })
        
        # Return the results
        return JsonResponse({
            'bucket_name': bucket_name,
            's3_objects': objects,
            'local_media': local_media,
            'media_root': str(settings.MEDIA_ROOT),
            'media_url': settings.MEDIA_URL,
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
