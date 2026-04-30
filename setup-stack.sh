#!/bin/bash
set -e

echo "Updating system packages..."
sudo apt-get update

echo "Installing Docker, Redis, and FFmpeg..."
sudo apt-get install -y docker.io redis-server ffmpeg

echo "Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

echo "Starting Redis service..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

echo "Creating Maya assets directory..."
mkdir -p /var/www/html/maya-assets

echo "Creating .env file with placeholders..."
cat > .env << 'EOF'
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here

# Deepgram Configuration
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
EOF

echo ".env file created! Please edit .env and add your actual API keys."
echo ""

echo "Cloning Vocode voice agent engine..."
GITHUB_USER="your_github_username"  # Update if needed for authentication
cd /tmp
git clone https://github.com/vocodehq/vocode-python.git
if [ ! -d vocode-python ]; then
    echo "Error: Failed to clone Vocode repository"
    exit 1
fi

echo "Setting up Vocode..."
cd vocode-python
python3 -m venv venv
source venv/bin/activate
pip install -e .
echo "Vocode voice agent engine setup complete!"

echo "Pulling and running n8n..."
docker pull n8nio/n8n
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n

echo "Pulling and running Nginx asset server..."
docker pull nginx:alpine
docker run -d --name asset-server -p 80:80 -v /var/www/html/maya-assets:/usr/share/nginx/html:ro nginx:alpine

echo ""
echo "Setup complete!"
echo "n8n is available at: http://localhost:5678"
echo "Nginx asset server is available at: http://localhost"
echo "Vocode cloned to /tmp/vocode-python"
echo "Please configure your API keys in .env file"
