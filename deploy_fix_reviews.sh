#!/bin/bash

echo "Deploying API helper fix to prevent undefined product ID errors..."

# Add the files to git
git add src/utils/apiHelpers.js

# Commit the changes
git commit -m "Added safe API helpers to prevent undefined ID errors"

# Deploy to Vercel production
vercel --prod

echo "Deployment completed!"
echo ""
echo "The safe API helpers have been deployed to Vercel."
echo "This fix prevents 500 errors when dealing with undefined product IDs." 