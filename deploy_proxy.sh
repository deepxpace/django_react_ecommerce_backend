#!/bin/bash

echo "Deploying S3 media proxy to Heroku..."

# Add the files to git
git add api/views.py backend/urls.py

# Commit the changes
git commit -m "Added S3 media proxy to bypass CORS issues"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "You can now use the media proxy to access S3 files without CORS issues."
echo "Update your frontend to use this URL pattern for images:"
echo ""
echo "From: https://koshimart-media.s3.amazonaws.com/products/image.jpg"
echo "To:   https://koshimart-api-6973a89b9858.herokuapp.com/media-proxy/products/image.jpg"
echo ""
echo "Example for your frontend code:"
echo ""
echo "// Add a utility function to convert S3 URLs to proxy URLs"
echo "function getProxyImageUrl(originalUrl) {"
echo "  if (!originalUrl) return ''; // Handle empty URLs"
echo "  // Extract the path after the S3 domain"
echo "  const s3Prefix = 'https://koshimart-media.s3.amazonaws.com/';"
echo "  if (originalUrl.startsWith(s3Prefix)) {"
echo "    const path = originalUrl.substring(s3Prefix.length);"
echo "    return \`https://koshimart-api-6973a89b9858.herokuapp.com/media-proxy/\${path}\`;"
echo "  }"
echo "  return originalUrl; // Return original if not S3"
echo "}" 