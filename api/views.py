from django.shortcuts import render
import requests
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
import mimetypes
import os
import datetime

# Register AVIF MIME type to ensure proper content type detection
mimetypes.add_type('image/avif', '.avif')

# Create your views here.

def proxy_s3_media(request, path):
    """
    Proxy for S3 media files to bypass CORS restrictions.
    This fetches and serves files from S3 through the Django backend.
    """
    # Import logging for troubleshooting
    import logging
    logger = logging.getLogger(__name__)
    
    if not path:
        logger.warning("No path specified in proxy request")
        raise Http404("No path specified")
    
    logger.info(f"Proxying media request for path: {path}")
    
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
        
        # Remove static/media/ prefix if it exists (to handle frontend requests)
        path.replace('static/media/', '') if 'static/media/' in path else None,
        
        # Common variations
        path.replace('_', '-') if '_' in path else None,
        path.replace('-', '_') if '-' in path else None
    ]
    
    # Filter out None values
    possible_paths = [p for p in possible_paths if p]
    logger.info(f"Will try these paths: {possible_paths}")
    
    # Get the current S3 bucket name and region
    current_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'koshimart-api')
    s3_region = getattr(settings, 'AWS_S3_REGION_NAME', 'eu-north-1')
    
    # Try all possible paths
    last_error = None
    for try_path in possible_paths:
        try:
            # Build the full S3 URL with region
            s3_url = f"https://{current_bucket}.s3.{s3_region}.amazonaws.com/{try_path}"
            logger.info(f"Trying S3 URL: {s3_url}")
            
            # Fetch the file from S3
            response = requests.get(s3_url, stream=True)
            
            if response.status_code == 200:
                logger.info(f"Found image at {s3_url}")
                # Success! Return the image
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                django_response = HttpResponse(
                    response.content,
                    content_type=content_type
                )
                django_response['Cache-Control'] = 'max-age=86400'
                return django_response
            else:
                # Try URL without region
                alt_s3_url_1 = f"https://{current_bucket}.s3.amazonaws.com/{try_path}"
                logger.info(f"Trying S3 URL without region: {alt_s3_url_1}")
                
                alt_response_1 = requests.get(alt_s3_url_1, stream=True)
                if alt_response_1.status_code == 200:
                    logger.info(f"Found image at URL without region: {alt_s3_url_1}")
                    content_type = alt_response_1.headers.get('Content-Type', 'application/octet-stream')
                    django_response = HttpResponse(
                        alt_response_1.content,
                        content_type=content_type
                    )
                    django_response['Cache-Control'] = 'max-age=86400'
                    return django_response
                
                # Try alternative bucket name
                alternative_bucket = 'koshimart-media' if current_bucket == 'koshimart-api' else 'koshimart-api'
                alt_s3_url_2 = f"https://{alternative_bucket}.s3.{s3_region}.amazonaws.com/{try_path}"
                logger.info(f"Trying alternative bucket with region: {alt_s3_url_2}")
                
                alt_response_2 = requests.get(alt_s3_url_2, stream=True)
                if alt_response_2.status_code == 200:
                    logger.info(f"Found image at alternative bucket with region: {alt_s3_url_2}")
                    content_type = alt_response_2.headers.get('Content-Type', 'application/octet-stream')
                    django_response = HttpResponse(
                        alt_response_2.content,
                        content_type=content_type
                    )
                    django_response['Cache-Control'] = 'max-age=86400'
                    return django_response
                
                # Try alternative bucket without region
                alt_s3_url_3 = f"https://{alternative_bucket}.s3.amazonaws.com/{try_path}"
                logger.info(f"Trying alternative bucket without region: {alt_s3_url_3}")
                
                alt_response_3 = requests.get(alt_s3_url_3, stream=True)
                if alt_response_3.status_code == 200:
                    logger.info(f"Found image at alternative bucket without region: {alt_s3_url_3}")
                    content_type = alt_response_3.headers.get('Content-Type', 'application/octet-stream')
                    django_response = HttpResponse(
                        alt_response_3.content, 
                        content_type=content_type
                    )
                    django_response['Cache-Control'] = 'max-age=86400'
                    return django_response
                
                last_error = f"S3 returned status {response.status_code} for URL {s3_url}"
                logger.warning(last_error)
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Error fetching {s3_url}: {last_error}")
    
    # Try Cloudinary as the next option
    try:
        # Check if Cloudinary is configured - first try env vars, then settings
        cloudinary_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        cloudinary_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        
        logger.info(f"Checking Cloudinary with name: {cloudinary_name}, storage: {cloudinary_storage}")
        
        if 'cloudinary' in cloudinary_storage and cloudinary_name:
            logger.info(f"Trying Cloudinary with cloud name: {cloudinary_name}")
            
            for try_path in possible_paths:
                # Try both with and without the products/ prefix
                cloudinary_paths = [try_path]
                if not try_path.startswith('products/') and 'products/' not in try_path:
                    cloudinary_paths.append(f"products/{try_path}")
                elif try_path.startswith('products/'):
                    cloudinary_paths.append(try_path[9:])  # Remove 'products/'
                
                # Also try without any file extension for raw assets
                base_path = try_path.rsplit('.', 1)[0] if '.' in try_path else try_path
                if base_path not in cloudinary_paths:
                    cloudinary_paths.append(base_path)
                
                for cloud_path in cloudinary_paths:
                    try:
                        # Construct Cloudinary URL
                        # Format: https://res.cloudinary.com/{cloud_name}/image/upload/{path}
                        cloudinary_url = f"https://res.cloudinary.com/{cloudinary_name}/image/upload/{cloud_path}"
                        logger.info(f"Trying Cloudinary URL: {cloudinary_url}")
                        
                        cloud_response = requests.get(cloudinary_url, stream=True)
                        if cloud_response.status_code == 200:
                            logger.info(f"Found image at Cloudinary: {cloudinary_url}")
                            # Detect content type - if it's AVIF, explicitly set it
                            content_type = cloud_response.headers.get('Content-Type', 'application/octet-stream')
                            if try_path.lower().endswith('.avif'):
                                content_type = 'image/avif'
                                
                            django_response = HttpResponse(
                                cloud_response.content,
                                content_type=content_type
                            )
                            django_response['Cache-Control'] = 'max-age=86400'
                            return django_response
                    except Exception as cloud_err:
                        logger.warning(f"Error fetching from Cloudinary: {str(cloud_err)}")
        else:
            logger.info(f"Cloudinary not configured properly. Storage: {cloudinary_storage}, Name: {cloudinary_name}")
    except Exception as e:
        logger.warning(f"Error checking Cloudinary: {str(e)}")
    
    # If we get here, all S3 and Cloudinary paths failed
    logger.error(f"All cloud storage paths failed for {path}. Last error: {last_error}")
    
    # Try Django's local media folder as a last resort
    try:
        from django.conf import settings
        import os
        
        # Check if the file exists in the media directory
        media_root = settings.MEDIA_ROOT
        logger.info(f"Checking local media folder: {media_root}")
        
        for local_path in possible_paths:
            local_file_path = os.path.join(media_root, local_path)
            logger.info(f"Checking if file exists: {local_file_path}")
            
            if os.path.exists(local_file_path):
                # File exists in media directory, serve it directly
                logger.info(f"Found image in local media folder: {local_file_path}")
                with open(local_file_path, 'rb') as f:
                    content = f.read()
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(local_file_path)
                # Force AVIF content type if needed
                if local_file_path.lower().endswith('.avif'):
                    content_type = 'image/avif'
                
                django_response = HttpResponse(
                    content,
                    content_type=content_type or 'application/octet-stream'
                )
                django_response['Cache-Control'] = 'max-age=86400'
                return django_response
    except Exception as e:
        logger.error(f"Error checking local media: {str(e)}")
    
    # Generate placeholder as last resort
    logger.info("Generating placeholder image")
    try:
        # Extract a name from the path to personalize the placeholder
        path_parts = path.split('/')
        filename = path_parts[-1] if path_parts else 'unknown'
        
        # Use filename in placeholder
        logger.info(f"Generating placeholder for: {filename}")
        
        # Generate a placeholder URL - use the first part of the filename
        name_part = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
        placeholder_url = f"https://placehold.co/400x400/EEE/999?text=Image:{name_part[:10]}"
        
        # Fetch the placeholder
        placeholder_response = requests.get(placeholder_url, stream=True)
        
        if placeholder_response.status_code == 200:
            logger.info("Successfully generated placeholder")
            return HttpResponse(
                placeholder_response.content,
                content_type=placeholder_response.headers.get('Content-Type', 'image/jpeg')
            )
    except Exception as e:
        logger.error(f"Error generating placeholder: {str(e)}")
        
    # If even the placeholder fails, return a simple 1x1 transparent GIF
    logger.info("Returning fallback transparent GIF")
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
    result = {
        'error': None,
        's3_objects': [],
        'local_media': [],
        'cloudinary_objects': [],
        'bucket_name': None,
        'media_root': None,
        'media_url': None,
        'cloudinary_name': None,
        'sample_urls': [],
        'test_image': None,
        'environment_vars': {}
    }
    
    try:
        # Import needed modules
        import os
        from django.conf import settings
        
        # Set basic information
        result['media_root'] = str(settings.MEDIA_ROOT)
        result['media_url'] = settings.MEDIA_URL
        result['static_url'] = settings.STATIC_URL
        result['static_root'] = str(settings.STATIC_ROOT)
        result['debug_mode'] = settings.DEBUG
        
        # Get hostname for URLs
        host = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        base_url = f"{protocol}://{host}"
        result['base_url'] = base_url
        
        # Check for environment variables (redact secrets)
        env_vars = {
            'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
            'CLOUDINARY_API_KEY': os.environ.get('CLOUDINARY_API_KEY', '')[:5] + '...' if os.environ.get('CLOUDINARY_API_KEY') else None,
            'CLOUDINARY_API_SECRET': '***REDACTED***' if os.environ.get('CLOUDINARY_API_SECRET') else None,
            'DATABASE_URL': 'present' if os.environ.get('DATABASE_URL') else None,
            'DJANGO_SETTINGS_MODULE': os.environ.get('DJANGO_SETTINGS_MODULE') 
        }
        result['environment_vars'] = env_vars
        
        # Get Cloudinary name from environment or settings
        cloudinary_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        result['cloudinary_name'] = cloudinary_name
        
        # Sample URL patterns for frontend reference
        result['sample_urls'] = [
            {
                'type': 'Direct Media URL',
                'pattern': f"{base_url}/media/filename.jpg",
                'description': 'Direct access to media files (redirects to Cloudinary)'
            },
            {
                'type': 'Media Proxy URL',
                'pattern': f"{base_url}/media-proxy/filename.jpg",
                'description': 'Proxy that tries multiple sources (S3, Cloudinary, local)'
            },
            {
                'type': 'Cloudinary Direct URL',
                'pattern': f"https://res.cloudinary.com/{cloudinary_name}/image/upload/filename.jpg",
                'description': 'Direct URL to Cloudinary (faster, but requires CORS setup)'
            },
            {
                'type': 'Cloudinary Transformation URL',
                'pattern': f"https://res.cloudinary.com/{cloudinary_name}/image/upload/c_fill,h_300,w_300/filename.jpg",
                'description': 'URL with transformations (resize, crop, etc.)'
            }
        ]
        
        # Check for Cloudinary configuration
        cloudinary_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        result['is_cloudinary_configured'] = 'cloudinary' in cloudinary_storage and bool(cloudinary_name)
        
        # Add information on how to serve AVIF images
        result['mime_types'] = {
            'avif': mimetypes.guess_type('test.avif')[0],
            'webp': mimetypes.guess_type('test.webp')[0],
            'jpg': mimetypes.guess_type('test.jpg')[0],
            'png': mimetypes.guess_type('test.png')[0]
        }
        
        # Try to get bucket name
        aws_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        result['bucket_name'] = aws_bucket
        
        # Check for AWS credentials
        aws_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        aws_secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        
        # Only try S3 if we have credentials
        if aws_key and aws_secret and aws_bucket:
            try:
                # Get a list of S3 objects
                import boto3
                
                # Use the AWS credentials from settings
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                )
                
                # Get a list of objects in the bucket
                max_objects = 100  # Limit to prevent excessive responses
                
                # Get bucket objects
                s3_result = s3.list_objects_v2(Bucket=aws_bucket, MaxKeys=max_objects)
                
                # Format the results
                if 'Contents' in s3_result:
                    for obj in s3_result['Contents']:
                        key = obj['Key']
                        # Build the full S3 URL
                        s3_url = f"https://{aws_bucket}.s3.amazonaws.com/{key}"
                        result['s3_objects'].append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'url': s3_url,
                            'proxy_url': f"/media-proxy/{key}"
                        })
            except Exception as e:
                result['s3_error'] = f"S3 error: {str(e)}"
        else:
            result['s3_error'] = "AWS credentials not configured"
        
        # Try to get Cloudinary images if configured
        if result['is_cloudinary_configured']:
            try:
                import cloudinary
                import cloudinary.api
                
                # Get API credentials from env vars or settings
                api_key = os.environ.get('CLOUDINARY_API_KEY') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY')
                api_secret = os.environ.get('CLOUDINARY_API_SECRET') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET')
                
                # Configure Cloudinary
                cloudinary.config(
                    cloud_name=cloudinary_name,
                    api_key=api_key,
                    api_secret=api_secret,
                )
                
                # List Cloudinary resources
                max_results = 100  # Limit to prevent excessive responses
                cloud_result = cloudinary.api.resources(max_results=max_results)
                
                if 'resources' in cloud_result:
                    for resource in cloud_result['resources']:
                        public_id = resource.get('public_id', '')
                        # Build the full Cloudinary URL
                        cloud_url = resource.get('secure_url', '')
                        
                        # Also get a few transformed URLs for reference
                        format = resource.get('format', '')
                        transformed_url = f"https://res.cloudinary.com/{cloudinary_name}/image/upload/c_fill,h_300,w_300/{public_id}.{format}"
                        auto_url = f"https://res.cloudinary.com/{cloudinary_name}/image/upload/f_auto,q_auto/{public_id}.{format}"
                        
                        result['cloudinary_objects'].append({
                            'public_id': public_id,
                            'resource_type': resource.get('resource_type', ''),
                            'type': resource.get('type', ''),
                            'format': format,
                            'url': cloud_url,
                            'transformed_url': transformed_url,
                            'auto_url': auto_url,
                            'proxy_url': f"/media-proxy/{public_id}.{format}"
                        })
                        
                        # Use the first image as a test image
                        if not result['test_image'] and format in ['jpg', 'jpeg', 'png', 'webp', 'avif']:
                            result['test_image'] = {
                                'original': cloud_url,
                                'transformed': transformed_url,
                                'auto': auto_url,
                                'proxy': f"{base_url}/media-proxy/{public_id}.{format}",
                                'via_frontend': f"{base_url}/media/{public_id}.{format}"
                            }
            except Exception as e:
                result['cloudinary_error'] = f"Cloudinary error: {str(e)}"
        else:
            result['cloudinary_error'] = "Cloudinary not configured"
        
        # Also list files from local media directory
        try:
            media_files = []
            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif')):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
                        media_files.append({
                            'path': rel_path,
                            'size': os.path.getsize(full_path),
                            'url': f"{settings.MEDIA_URL}{rel_path}"
                        })
                        
            # Sort by newest first (using file modification time)
            sorted_media = sorted(
                media_files,
                key=lambda x: os.path.getmtime(os.path.join(settings.MEDIA_ROOT, x['path'])),
                reverse=True
            )
            result['local_media'] = sorted_media[:50]  # Limit to 50 files
        except Exception as e:
            result['local_media_error'] = f"Local media error: {str(e)}"
        
        # Add environment info for debugging
        import platform
        import sys
        result['environment'] = {
            'python': sys.version,
            'platform': platform.platform(),
            'django': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
            'middleware': getattr(settings, 'MIDDLEWARE', []),
            'installed_apps': getattr(settings, 'INSTALLED_APPS', []),
        }
        
        # Return the results
        return JsonResponse(result)
    
    except Exception as e:
        import traceback
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
        return JsonResponse(result)

def test_image(request, format):
    """
    Generate a test image in the requested format.
    This is useful for testing the media serving infrastructure.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate format
    format = format.lower()
    if format not in ['jpg', 'jpeg', 'png', 'webp', 'avif', 'gif']:
        format = 'png'  # Default to PNG
    
    # Map formats to content types
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'avif': 'image/avif',
        'gif': 'image/gif'
    }
    
    # Use a tiny 1x1 placeholder image for each format
    try:
        # Use pre-generated tiny images
        if format in ['jpg', 'jpeg']:
            # 1x1 JPEG (red)
            image_data = (
                b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x01\x00\x48'
                b'\x00\x48\x00\x00\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08'
                b'\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12'
                b'\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20'
                b'\x22\x2c\x23\x1c\x1c\x28\x37\x29\x2c\x30\x31\x34\x34\x34\x1f\x27'
                b'\x39\x3d\x38\x32\x3c\x2e\x33\x34\x32\xff\xdb\x00\x43\x01\x09\x09'
                b'\x09\x0c\x0b\x0c\x18\x0d\x0d\x18\x32\x21\x1c\x21\x32\x32\x32\x32'
                b'\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32'
                b'\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32'
                b'\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\x32\xff\xc0\x00\x11'
                b'\x08\x00\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01\xff'
                b'\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b'
                b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04'
                b'\x04\x00\x00\x01\x7d\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41'
                b'\x06\x13\x51\x61\x07\x22\x71\x14\x32\x81\x91\xa1\x08\x23\x42\xb1'
                b'\xc1\x15\x52\xd1\xf0\x24\x33\x62\x72\x82\x09\x0a\x16\x17\x18\x19'
                b'\x1a\x25\x26\x27\x28\x29\x2a\x34\x35\x36\x37\x38\x39\x3a\x43\x44'
                b'\x45\x46\x47\x48\x49\x4a\x53\x54\x55\x56\x57\x58\x59\x5a\x63\x64'
                b'\x65\x66\x67\x68\x69\x6a\x73\x74\x75\x76\x77\x78\x79\x7a\x83\x84'
                b'\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2'
                b'\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9'
                b'\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7'
                b'\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3'
                b'\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01'
                b'\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03'
                b'\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01'
                b'\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02\x77\x00\x01\x02'
                b'\x03\x11\x04\x05\x21\x31\x06\x12\x41\x51\x07\x61\x71\x13\x22\x32'
                b'\x81\x08\x14\x42\x91\xa1\xb1\xc1\x09\x23\x33\x52\xf0\x15\x62\x72'
                b'\xd1\x0a\x16\x24\x34\xe1\x25\xf1\x17\x18\x19\x1a\x26\x27\x28\x29'
                b'\x2a\x35\x36\x37\x38\x39\x3a\x43\x44\x45\x46\x47\x48\x49\x4a\x53'
                b'\x54\x55\x56\x57\x58\x59\x5a\x63\x64\x65\x66\x67\x68\x69\x6a\x73'
                b'\x74\x75\x76\x77\x78\x79\x7a\x82\x83\x84\x85\x86\x87\x88\x89\x8a'
                b'\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8'
                b'\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6'
                b'\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4'
                b'\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff'
                b'\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xfe\xfe\x28'
                b'\xa2\x8a\x00\xff\xd9'
            )
        elif format == 'png':
            # 1x1 PNG (blue)
            image_data = (
                b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52'
                b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53'
                b'\xde\x00\x00\x00\x09\x70\x48\x59\x73\x00\x00\x0b\x13\x00\x00\x0b'
                b'\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07\x74\x49\x4d\x45\x07\xe0'
                b'\x0a\x1f\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x49\x44\x41'
                b'\x54\x08\xd7\x63\x60\x00\x00\x00\x02\x00\x01\xe2\x21\xbc\x33\x00'
                b'\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82'
            )
        elif format == 'webp':
            # 1x1 WebP (green)
            image_data = (
                b'\x52\x49\x46\x46\x24\x00\x00\x00\x57\x45\x42\x50\x56\x50\x38\x20'
                b'\x18\x00\x00\x00\x30\x01\x00\x9d\x01\x2a\x01\x00\x01\x00\x02\x00'
                b'\x34\x25\xa4\x00\x03\x70\x00\xfe\xfb\xfd\x50\x00\x00'
            )
        elif format == 'avif':
            # Since AVIF is complex, use this placeholder and set content type
            # 1x1 PNG (just reuse the PNG but set AVIF content type)
            image_data = (
                b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52'
                b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53'
                b'\xde\x00\x00\x00\x09\x70\x48\x59\x73\x00\x00\x0b\x13\x00\x00\x0b'
                b'\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07\x74\x49\x4d\x45\x07\xe0'
                b'\x0a\x1f\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x49\x44\x41'
                b'\x54\x08\xd7\x63\x60\x00\x00\x00\x02\x00\x01\xe2\x21\xbc\x33\x00'
                b'\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82'
            )
        elif format == 'gif':
            # 1x1 GIF (transparent)
            image_data = (
                b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
                b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
                b'\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
            )
        else:
            # Fallback to transparent GIF
            image_data = (
                b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
                b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
                b'\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
            )
            format = 'gif'
        
        # Return the image
        content_type = content_types.get(format, 'image/png')
        response = HttpResponse(image_data, content_type=content_type)
        response['Cache-Control'] = 'max-age=3600'  # Cache for 1 hour
        
        logger.info(f"Served test image: {format} (1x1 pixel)")
        return response
        
    except Exception as e:
        logger.error(f"Error generating test image: {str(e)}")
        # Return a fallback image on error
        transparent_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b'
        )
        return HttpResponse(transparent_gif, content_type='image/gif')

def debug_cloudinary(request):
    """
    Debug view to check Cloudinary configuration
    """
    import os
    import logging
    import sys
    import json
    from django.conf import settings
    import cloudinary
    import cloudinary.api
    
    logger = logging.getLogger(__name__)
    
    result = {
        'env_vars': {
            'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
            'CLOUDINARY_API_KEY': os.environ.get('CLOUDINARY_API_KEY', '')[:5] + '...' if os.environ.get('CLOUDINARY_API_KEY') else None,
            'CLOUDINARY_API_SECRET': '***REDACTED***' if os.environ.get('CLOUDINARY_API_SECRET') else None,
        },
        'settings': {
            'CLOUD_NAME': getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME'),
            'API_KEY': getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY', '')[:5] + '...' if getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY') else None,
            'API_SECRET': '***REDACTED***' if getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET') else None,
            'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', None),
        },
        'test_results': []
    }
    
    # Try to upload a test image to verify access
    try:
        # Get credentials in order of precedence
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET') or getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET')
        
        logger.info(f"Configuring Cloudinary with name: {cloud_name}")
        
        # Configure the SDK
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Check our config
        result['test_results'].append({
            'test': 'Check configuration',
            'time': str(datetime.datetime.now()),
            'status': 'Running...'
        })
        
        config = cloudinary.config()
        result['config'] = {
            'cloud_name': config.cloud_name,
            'api_key': config.api_key[:5] + '...' if config.api_key else None,
            'secure': config.secure
        }
        
        result['test_results'][-1]['status'] = 'Success'
        
        # Check if we can get the resources
        result['test_results'].append({
            'test': 'List resources',
            'time': str(datetime.datetime.now()),
            'status': 'Running...'
        })
        
        resources = cloudinary.api.resources(max_results=5)
        
        if 'resources' in resources:
            result['resource_count'] = len(resources['resources'])
            result['resource_sample'] = [{
                'public_id': r.get('public_id'),
                'type': r.get('type'),
                'format': r.get('format')
            } for r in resources['resources'][:3]]
            result['test_results'][-1]['status'] = 'Success'
        else:
            result['resource_count'] = 0
            result['test_results'][-1]['status'] = 'No resources found'
        
        # Try to generate a test URL
        result['test_results'].append({
            'test': 'Generate URL',
            'time': str(datetime.datetime.now()),
            'status': 'Running...'
        })
        
        if result.get('resource_count', 0) > 0:
            sample_id = result['resource_sample'][0]['public_id']
            sample_format = result['resource_sample'][0]['format']
            
            # Generate a URL for the test image
            sample_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{sample_id}.{sample_format}"
            result['sample_url'] = sample_url
            
            # Test fetching the URL
            import requests
            response = requests.head(sample_url)
            result['url_test'] = {
                'url': sample_url,
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type')
            }
            result['test_results'][-1]['status'] = f"Success ({response.status_code})"
        else:
            result['test_results'][-1]['status'] = 'Skipped - no resources'
        
        # Try to upload a tiny test image
        result['test_results'].append({
            'test': 'Upload test image',
            'time': str(datetime.datetime.now()),
            'status': 'Running...'
        })
        
        # Create a simple 1x1 transparent PNG in memory
        from django.core.files.base import ContentFile
        tiny_png = (
            b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52'
            b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4'
            b'\x89\x00\x00\x00\x0a\x49\x44\x41\x54\x78\x9c\x63\x00\x01\x00\x00'
            b'\x05\x00\x01\x0d\x0a\x2d\xb4\x00\x00\x00\x00\x49\x45\x4e\x44\xae'
            b'\x42\x60\x82'
        )
        
        try:
            test_file = ContentFile(tiny_png)
            test_file.name = 'test_upload.png'
            
            # Create a temporary file for the upload
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                tmp.write(tiny_png)
                tmp.flush()
                
                # Try the upload
                upload_result = cloudinary.uploader.upload(
                    tmp.name,
                    public_id='test_upload',
                    overwrite=True,
                    resource_type='image'
                )
                
                result['upload_result'] = {
                    'public_id': upload_result.get('public_id'),
                    'url': upload_result.get('url'),
                    'secure_url': upload_result.get('secure_url')
                }
                
                result['test_results'][-1]['status'] = 'Success'
        except Exception as e:
            result['upload_error'] = str(e)
            result['test_results'][-1]['status'] = f"Failed: {str(e)}"
            
    except Exception as e:
        import traceback
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
        if result['test_results'] and result['test_results'][-1]['status'] == 'Running...':
            result['test_results'][-1]['status'] = f"Failed: {str(e)}"
    
    return JsonResponse(result)
