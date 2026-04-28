#!/bin/bash
set -e

echo "Updating system packages..."
sudo apt-get update

echo "Installing Docker..."
sudo apt-get install -y docker.io

echo "Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

echo "Creating Maya assets directory..."
mkdir -p /var/www/html/maya-assets

echo "Pulling and running n8n..."
docker pull n8nio/n8n
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n

echo "Pulling and running Nginx asset server..."
docker pull nginx:alpine
docker run -d --name asset-server -p 80:80 -v /var/www/html/maya-assets:/usr/share/nginx/html:ro nginx:alpine

echo "Setup complete!"
echo "n8n is available at: http://localhost:5678"
echo "Nginx asset server is available at: http://localhost"