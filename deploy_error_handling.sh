#!/bin/bash

echo "Deploying improved error handling and debugging for media proxy..."

# Add the files to git
git add api/views.py

# Commit the changes
git commit -m "Improved error handling and logging for media proxy"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "The improved media proxy with better error handling has been deployed."
echo "Check the Heroku logs to see the detailed logging information:"
echo "heroku logs --tail -a koshimart-api"
echo ""
echo "This will help identify exactly why some images aren't loading properly." 