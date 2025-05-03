#!/bin/bash

set -e

# Configuration
BACKEND_SRC="/Users/deepxpacelab/django_react_ecommerce_backend-1"
FRONTEND_SRC="/Users/deepxpacelab/django_react_ecommerce_frontend-1"
PROD_SERVER="your_server_ip_or_hostname"
PROD_USER="ubuntu"  # or your server username
PROD_BACKEND_DIR="/var/www/koshimart/backend"
PROD_FRONTEND_DIR="/var/www/koshimart/frontend"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment process...${NC}"

# Build React frontend
echo -e "${YELLOW}Building React frontend...${NC}"
cd $FRONTEND_SRC
yarn build || { echo -e "${RED}Frontend build failed${NC}"; exit 1; }
echo -e "${GREEN}Frontend build successful${NC}"

# Collect Django static files
echo -e "${YELLOW}Collecting Django static files...${NC}"
cd $BACKEND_SRC
source venv/bin/activate
DJANGO_SETTINGS_MODULE=backend.settings_prod python manage.py collectstatic --noinput || { echo -e "${RED}Static file collection failed${NC}"; exit 1; }
echo -e "${GREEN}Static files collected successfully${NC}"

# Create a deployment package
echo -e "${YELLOW}Creating deployment package...${NC}"
DEPLOY_DIR=$(mktemp -d)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKEND_PACKAGE="koshimart_backend_$TIMESTAMP.tar.gz"
FRONTEND_PACKAGE="koshimart_frontend_$TIMESTAMP.tar.gz"

# Copy backend files
mkdir -p $DEPLOY_DIR/backend
cp -r $BACKEND_SRC/* $DEPLOY_DIR/backend/
# Exclude unnecessary directories
rm -rf $DEPLOY_DIR/backend/venv
rm -rf $DEPLOY_DIR/backend/.git
rm -rf $DEPLOY_DIR/backend/__pycache__
find $DEPLOY_DIR/backend -name "*.pyc" -delete
find $DEPLOY_DIR/backend -name "__pycache__" -delete

# Create backend archive
cd $DEPLOY_DIR
tar -czf $BACKEND_PACKAGE backend/
echo -e "${GREEN}Backend package created: $BACKEND_PACKAGE${NC}"

# Copy frontend files
mkdir -p $DEPLOY_DIR/frontend
cp -r $FRONTEND_SRC/dist/* $DEPLOY_DIR/frontend/

# Create frontend archive
cd $DEPLOY_DIR
tar -czf $FRONTEND_PACKAGE frontend/
echo -e "${GREEN}Frontend package created: $FRONTEND_PACKAGE${NC}"

# Upload to server
echo -e "${YELLOW}Uploading packages to server...${NC}"
scp $DEPLOY_DIR/$BACKEND_PACKAGE $PROD_USER@$PROD_SERVER:/tmp/
scp $DEPLOY_DIR/$FRONTEND_PACKAGE $PROD_USER@$PROD_SERVER:/tmp/

# Deploy on server
echo -e "${YELLOW}Deploying on server...${NC}"
ssh $PROD_USER@$PROD_SERVER << EOF
    set -e
    echo "Creating backup..."
    sudo mkdir -p /var/www/backups
    if [ -d "$PROD_BACKEND_DIR" ]; then
        sudo tar -czf /var/www/backups/backend_backup_$TIMESTAMP.tar.gz $PROD_BACKEND_DIR
    fi
    if [ -d "$PROD_FRONTEND_DIR" ]; then
        sudo tar -czf /var/www/backups/frontend_backup_$TIMESTAMP.tar.gz $PROD_FRONTEND_DIR
    fi
    
    echo "Extracting backend package..."
    sudo mkdir -p $PROD_BACKEND_DIR
    sudo tar -xzf /tmp/$BACKEND_PACKAGE -C /tmp
    sudo rsync -a --delete /tmp/backend/ $PROD_BACKEND_DIR/
    sudo mkdir -p $PROD_BACKEND_DIR/logs
    
    echo "Setting up virtual environment..."
    cd $PROD_BACKEND_DIR
    sudo python3 -m venv venv
    sudo venv/bin/pip install --upgrade pip
    sudo venv/bin/pip install -r requirements.txt
    sudo venv/bin/pip install gunicorn psycopg2-binary redis
    
    echo "Running migrations..."
    sudo DJANGO_SETTINGS_MODULE=backend.settings_prod venv/bin/python manage.py migrate
    
    echo "Extracting frontend package..."
    sudo mkdir -p $PROD_FRONTEND_DIR
    sudo tar -xzf /tmp/$FRONTEND_PACKAGE -C /tmp
    sudo rsync -a --delete /tmp/frontend/ $PROD_FRONTEND_DIR/
    
    echo "Setting permissions..."
    sudo chown -R www-data:www-data $PROD_BACKEND_DIR
    sudo chown -R www-data:www-data $PROD_FRONTEND_DIR
    
    echo "Restarting services..."
    sudo systemctl restart koshimart.service
    sudo systemctl restart nginx
    
    echo "Cleaning up..."
    sudo rm /tmp/$BACKEND_PACKAGE
    sudo rm /tmp/$FRONTEND_PACKAGE
    sudo rm -rf /tmp/backend
    sudo rm -rf /tmp/frontend
    
    echo "Deployment completed successfully!"
EOF

# Clean up local deployment files
rm -rf $DEPLOY_DIR

echo -e "${GREEN}Deployment process completed!${NC}" 