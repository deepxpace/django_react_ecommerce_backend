#!/bin/bash

echo "Deploying CORS changes to Heroku..."

# Add the changes to git
git add backend/settings_heroku.py

# Commit the changes
git commit -m "Updated CORS settings for Vercel frontend"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "CORS settings have been updated to allow access from koshimart.vercel.app."
echo ""
echo "For AWS S3 bucket configuration (must be done separately with AWS permissions):"
echo "Run this command to update your S3 bucket CORS settings:"
echo "aws s3api put-bucket-cors --bucket koshimart-media --cors-configuration file://s3_cors_config.json"
echo ""
echo "If you don't have AWS CLI access, please ask your DevOps team to configure the S3 bucket with the CORS settings in s3_cors_config.json." 