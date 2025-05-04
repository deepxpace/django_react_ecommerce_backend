#!/bin/bash

echo "Deploying latest middleware and proxy changes to Heroku..."

# First, create a small change to the middleware to force a new commit
echo "// Test update $(date)" >> api/middleware.py

# Add the files to git
git add api/middleware.py api/views.py api/urls.py

# Commit the changes
git commit -m "Test deployment of middleware with improved Cloudinary and local fallback"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "The middleware has been deployed with the following features:"
echo "1. First tries serving images from Cloudinary"
echo "2. Falls back to local media when Cloudinary is unavailable"
echo "3. Forwards to media-proxy endpoint as a last resort"
echo ""
echo "You can test by accessing:"
echo "https://koshimart-api.herokuapp.com/media/any_product_image.jpg"
echo ""
echo "The debug endpoints are also available at:"
echo "https://koshimart-api.herokuapp.com/debug-cloudinary/"
echo "https://koshimart-api.herokuapp.com/debug-images/" 