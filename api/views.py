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
        # Check if Cloudinary is configured
        cloudinary_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        cloudinary_name = getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        
        if 'cloudinary' in cloudinary_storage and cloudinary_name:
            logger.info(f"Trying Cloudinary with cloud name: {cloudinary_name}")
            
            for try_path in possible_paths:
                # Try both with and without the products/ prefix
                cloudinary_paths = [try_path]
                if not try_path.startswith('products/') and 'products/' not in try_path:
                    cloudinary_paths.append(f"products/{try_path}")
                elif try_path.startswith('products/'):
                    cloudinary_paths.append(try_path[9:])  # Remove 'products/'
                
                for cloud_path in cloudinary_paths:
                    try:
                        # Construct Cloudinary URL
                        # Format: https://res.cloudinary.com/{cloud_name}/image/upload/{path}
                        cloudinary_url = f"https://res.cloudinary.com/{cloudinary_name}/image/upload/{cloud_path}"
                        logger.info(f"Trying Cloudinary URL: {cloudinary_url}")
                        
                        cloud_response = requests.get(cloudinary_url, stream=True)
                        if cloud_response.status_code == 200:
                            logger.info(f"Found image at Cloudinary: {cloudinary_url}")
                            content_type = cloud_response.headers.get('Content-Type', 'application/octet-stream')
                            django_response = HttpResponse(
                                cloud_response.content,
                                content_type=content_type
                            )
                            django_response['Cache-Control'] = 'max-age=86400'
                            return django_response
                    except Exception as cloud_err:
                        logger.warning(f"Error fetching from Cloudinary: {str(cloud_err)}")
        else:
            logger.info("Cloudinary not configured, skipping Cloudinary check")
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
    }
    
    try:
        # Import needed modules
        import os
        from django.conf import settings
        
        # Set basic information
        result['media_root'] = str(settings.MEDIA_ROOT)
        result['media_url'] = settings.MEDIA_URL
        
        # Check for Cloudinary configuration
        cloudinary_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', '')
        cloudinary_name = getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME')
        result['cloudinary_name'] = cloudinary_name
        result['is_cloudinary_configured'] = 'cloudinary' in cloudinary_storage and bool(cloudinary_name)
        
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
                
                # Configure Cloudinary
                cloudinary.config(
                    cloud_name=cloudinary_name,
                    api_key=getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY'),
                    api_secret=getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET'),
                )
                
                # List Cloudinary resources
                max_results = 100  # Limit to prevent excessive responses
                cloud_result = cloudinary.api.resources(max_results=max_results)
                
                if 'resources' in cloud_result:
                    for resource in cloud_result['resources']:
                        public_id = resource.get('public_id', '')
                        # Build the full Cloudinary URL
                        cloud_url = resource.get('url', '')
                        secure_url = resource.get('secure_url', '')
                        
                        result['cloudinary_objects'].append({
                            'public_id': public_id,
                            'resource_type': resource.get('resource_type', ''),
                            'type': resource.get('type', ''),
                            'format': resource.get('format', ''),
                            'url': secure_url or cloud_url,
                            'proxy_url': f"/media-proxy/{public_id}.{resource.get('format', '')}"
                        })
            except Exception as e:
                result['cloudinary_error'] = f"Cloudinary error: {str(e)}"
        else:
            result['cloudinary_error'] = "Cloudinary not configured"
        
        # Also list files from local media directory
        try:
            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
                        result['local_media'].append({
                            'path': rel_path,
                            'size': os.path.getsize(full_path),
                            'url': f"{settings.MEDIA_URL}{rel_path}"
                        })
        except Exception as e:
            result['local_media_error'] = f"Local media error: {str(e)}"
        
        # Return the results
        return JsonResponse(result)
    
    except Exception as e:
        import traceback
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
        return JsonResponse(result)
