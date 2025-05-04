#!/bin/bash

echo "========================================="
echo "Deploying to Heroku with Cloudinary setup"
echo "========================================="

# Make sure Cloudinary environment variables are set
echo "Setting Cloudinary environment variables..."
heroku config:set CLOUDINARY_CLOUD_NAME="deepsimage" \
                 CLOUDINARY_API_KEY="855942689195483" \
                 CLOUDINARY_API_SECRET="pRzA_eY3dPJeiFiQn88LUa1gGA4" \
                 -a koshimart-api

# Ensure DEBUG is off
heroku config:set DEBUG="False" -a koshimart-api

# Make sure CORS is properly configured for Cloudinary
heroku config:set CORS_ALLOW_ALL_ORIGINS="False" -a koshimart-api

# Add and commit changes
echo "Adding files to git..."
git add api/middleware.py api/views.py api/urls.py backend/settings_heroku.py

# Commit changes
echo "Committing changes..."
git commit -m "Deploy with enhanced Cloudinary and local media fallback"

# Push to Heroku
echo "Pushing to Heroku..."
git push heroku main

# Clear cache
echo "Clearing Heroku build cache..."
heroku builds:cache:purge -a koshimart-api --confirm koshimart-api

# Run collectstatic
echo "Running collectstatic..."
heroku run "python manage.py collectstatic --noinput" -a koshimart-api

# Restart the application
echo "Restarting the application..."
heroku restart -a koshimart-api

echo "========================================="
echo "Deployment completed!"
echo "========================================="
echo ""
echo "Cloudinary configuration:"
echo "- Cloud name: deepsimage"
echo "- Middleware is configured to use Cloudinary first, then local files"
echo ""
echo "Test image serving with:"
echo "- https://koshimart-api-6973a89b9858.herokuapp.com/media/any_image.jpg"
echo "- https://koshimart-api-6973a89b9858.herokuapp.com/media-proxy/any_image.jpg"
echo ""
echo "Checking logs for any issues..."
heroku logs --tail -a koshimart-api 