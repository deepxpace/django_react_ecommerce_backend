#!/bin/bash

echo "Deploying improved S3 media proxy to Heroku..."

# Add the files to git
git add api/views.py

# Commit the changes
git commit -m "Improved S3 media proxy with better error handling and fallbacks"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "The improved S3 media proxy has been deployed."
echo "It now handles missing images gracefully by providing placeholders."
echo ""
echo "Let's test the proxy with a specific image:"
echo "https://koshimart-api-6973a89b9858.herokuapp.com/media-proxy/products/45-cell-alum-silver-sport-band-storm-blue-s9_3RQV0XO.jpeg"
echo ""
echo "If the image doesn't exist in S3, you'll now get a placeholder instead of a 500 error." 