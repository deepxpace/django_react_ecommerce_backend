#!/bin/bash

echo "Setting up Cloudinary on Heroku..."

# Set Cloudinary environment variables on Heroku
heroku config:set CLOUDINARY_CLOUD_NAME="Deepsimage" \
                  CLOUDINARY_API_KEY="855942689195483" \
                  CLOUDINARY_API_SECRET="pRzA_eY3dPJeiFiQn88LUa1gGA4" \
                  -a koshimart-api

# Add the modified files to git
git add backend/settings_heroku.py requirements.txt

# Commit the changes
git commit -m "Switched from AWS S3 to Cloudinary for image storage"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "Now using Cloudinary for image storage."
echo "Images will be served directly from Cloudinary CDN."
echo ""
echo "Visit Django admin to test image uploads: https://koshimart-api-6973a89b9858.herokuapp.com/admin/"
echo ""
echo "Your existing S3 images will need to be manually uploaded to Cloudinary."
echo "You can use the Django admin interface to re-upload important images."
echo ""
echo "Frontend URLs for images will continue to work through the proxy at /media-proxy/{path}" 