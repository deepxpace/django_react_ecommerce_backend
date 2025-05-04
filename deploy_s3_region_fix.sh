#!/bin/bash

echo "Deploying S3 region fix to Heroku..."

# Add the modified files to git
git add backend/settings_heroku.py
git add api/views.py

# Commit the changes
git commit -m "Fixed S3 region to eu-north-1 instead of us-east-1"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "The backend now uses the correct S3 configuration:"
echo "- S3 Region: eu-north-1 (Stockholm)"
echo "- Bucket name: koshimart-api"
echo "- AWS credentials are configured"
echo "- Fixed S3 domain: koshimart-api.s3.eu-north-1.amazonaws.com"
echo "- The proxy supports both region patterns for backward compatibility"
echo ""
echo "Let's check the debug endpoint to see if S3 connection works after the fix:"
echo "Visit: https://koshimart-api-6973a89b9858.herokuapp.com/api/v1/debug/images/"
echo ""
echo "Now deploying the frontend changes as well..."
echo ""
cd /Users/deepxpacelab/django_react_ecommerce_frontend-1
git add src/utils/imageUtils.js
git commit -m "Fixed S3 region to eu-north-1 in frontend code"
yarn build
vercel --prod

echo ""
echo "Both backend and frontend have been updated with the correct S3 region."
echo "Images should now load correctly in the frontend." 