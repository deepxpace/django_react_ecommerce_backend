#!/bin/bash

echo "Deploying AWS S3 configuration update to Heroku..."

# Add the modified files to git
git add backend/settings_heroku.py
git add api/views.py

# Commit the changes
git commit -m "Updated S3 storage with new AWS credentials and bucket name"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "The backend now uses the following S3 configuration:"
echo "- Bucket name: koshimart-api"
echo "- AWS credentials are now configured correctly"
echo "- Media files are served from S3 with fallback to local storage"
echo "- The proxy supports both old and new bucket names for backward compatibility"
echo ""
echo "Let's verify the configuration:"
heroku config -a koshimart-api | grep AWS

echo ""
echo "Let's check the debug endpoint to see if S3 connection works:"
echo "Visit: https://koshimart-api-6973a89b9858.herokuapp.com/api/v1/debug/images/"
echo ""
echo "For frontend, don't forget to deploy the updated imageUtils.js to Vercel."
echo "" 