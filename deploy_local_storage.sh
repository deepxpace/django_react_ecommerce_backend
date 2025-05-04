#!/bin/bash

echo "Deploying local storage configuration to Heroku..."

# Add the modified files to git
git add backend/settings_heroku.py

# Commit the changes
git commit -m "Switch to local storage instead of S3"

# Push to Heroku
git push heroku main

echo "Deployment completed!"
echo ""
echo "Now using local storage for media files instead of S3."
echo "You'll need to create a /media directory in Heroku and ensure it persists between deployments."
echo ""
echo "Let's create a media directory and collect static files:"
heroku run "mkdir -p /app/media" -a koshimart-api
heroku run "python manage.py collectstatic --noinput" -a koshimart-api

echo ""
echo "For image uploads to work with the admin panel, the /media directory needs to persist between deployments."
echo "Consider adding an add-on like 'bucketeer' later for permanent storage."
echo "" 