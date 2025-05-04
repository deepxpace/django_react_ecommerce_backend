#!/bin/bash

echo "Deploying enhanced S3 media proxy with multi-path support to Heroku..."

# Add the files to git
git add api/views.py backend/urls.py

# Commit the changes
git commit -m "Enhanced S3 media proxy with multi-path support to find real images"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "The enhanced S3 media proxy has been deployed."
echo "It now tries multiple possible image paths to find your real product images."
echo ""
echo "You can use the debug endpoint to see what images are available in your S3 bucket:"
echo "https://koshimart-api-6973a89b9858.herokuapp.com/api/v1/debug/images/"
echo ""
echo "This will help identify where your actual product images are stored and what paths to use." 