# Docker Hub Deployment Guide for MCRAG

This guide explains how to push the MCRAG backend to Docker Hub and deploy it anywhere.

## 🔐 API Key Security

**IMPORTANT: Your API keys are SAFE!** 

✅ **What gets pushed to Docker Hub:**
- Application code
- Dependencies 
- Runtime environment
- Configuration structure

❌ **What does NOT get pushed:**
- Environment variables (including `OPENROUTER_API_KEY`)
- Local `.env` files
- Runtime secrets

Your API keys are injected at **runtime** via environment variables, never baked into the image.

## 🏗️ Setup for Docker Hub

### 1. Edit deploy.sh Configuration

```bash
# Edit deploy.sh and set your Docker Hub username
nano deploy.sh

# Find this line and update:
DOCKER_HUB_USERNAME="your-dockerhub-username"  # Replace with your username
```

### 2. Create Docker Hub Account

1. Go to [hub.docker.com](https://hub.docker.com)
2. Create an account if you don't have one
3. Note your username for the configuration above

## 🚀 Pushing to Docker Hub

### Method 1: Using the deploy script (Recommended)

```bash
# Build and push to Docker Hub
./deploy.sh push
```

This will:
- Build the image with proper tags
- Tag with version (from git) or 'latest'
- Push to Docker Hub
- Provide pull instructions

### Method 2: Manual Docker commands

```bash
# Set your Docker Hub username
DOCKER_HUB_USERNAME="your-username"

# Build and tag the image
docker build -t $DOCKER_HUB_USERNAME/mcrag-backend:latest .

# Login to Docker Hub
docker login

# Push the image
docker push $DOCKER_HUB_USERNAME/mcrag-backend:latest
```

## 📦 Deploying from Docker Hub

### On Any Server

1. **Install Docker and Docker Compose**
2. **Set environment variables:**
   ```bash
   export OPENROUTER_API_KEY=your_actual_api_key_here
   ```

3. **Deploy using the script:**
   ```bash
   # Download just the deploy script
   curl -O https://raw.githubusercontent.com/your-username/mcrag/main/deploy.sh
   chmod +x deploy.sh
   
   # Edit to set your Docker Hub username
   nano deploy.sh
   
   # Deploy from Docker Hub
   ./deploy.sh deploy-hub
   ```

### Manual Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  mcrag-backend:
    image: your-username/mcrag-backend:latest  # Replace with your image
    ports:
      - "8001:8001"
    environment:
      REDIS_URL: redis://redis:6379
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      OPENROUTER_URL: https://openrouter.ai/api/v1
      MODEL_GENERATOR: google/gemini-flash-1.5
      MODEL_CRITIC1: openai/gpt-4o-mini
      MODEL_CRITIC2: deepseek/deepseek-r1
    depends_on:
      - redis

volumes:
  redis_data:
```

Then run:
```bash
export OPENROUTER_API_KEY=your_key_here
docker-compose up -d
```

## 🏷️ Versioning

### Using Git Tags

```bash
# Create a version tag
git tag v1.0.0
git push origin v1.0.0

# Push will automatically use the tag as version
./deploy.sh push
```

### Deploying Specific Versions

```bash
# Deploy latest
./deploy.sh deploy-hub

# Deploy specific version
./deploy.sh deploy-hub v1.0.0
```

## 🛡️ Security Best Practices

### 1. Environment Variables
```bash
# On production server, set in shell profile or systemd service
export OPENROUTER_API_KEY=sk-or-v1-xxxxx
export MODEL_GENERATOR=google/gemini-flash-1.5
```

### 2. Docker Secrets (Advanced)
```yaml
services:
  mcrag-backend:
    secrets:
      - openrouter_key
    environment:
      OPENROUTER_API_KEY_FILE: /run/secrets/openrouter_key

secrets:
  openrouter_key:
    file: ./secrets/openrouter_key.txt
```

### 3. Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcrag-secrets
type: Opaque
stringData:
  openrouter-api-key: sk-or-v1-xxxxx
```

## 🌍 Deployment Examples

### AWS ECS/Fargate
```json
{
  "family": "mcrag-backend",
  "environment": [
    {
      "name": "OPENROUTER_API_KEY",
      "value": "${OPENROUTER_API_KEY}"
    }
  ],
  "image": "your-username/mcrag-backend:latest"
}
```

### Google Cloud Run
```bash
gcloud run deploy mcrag-backend \
  --image your-username/mcrag-backend:latest \
  --set-env-vars OPENROUTER_API_KEY=your-key \
  --port 8001
```

### DigitalOcean App Platform
```yaml
name: mcrag-backend
services:
- name: api
  image:
    registry_type: DOCKER_HUB
    repository: your-username/mcrag-backend
    tag: latest
  environment_slug: python
  envs:
  - key: OPENROUTER_API_KEY
    value: your-key-here
    type: SECRET
```

## 📋 Deployment Checklist

- [ ] Set `DOCKER_HUB_USERNAME` in deploy.sh
- [ ] Build and push image: `./deploy.sh push`
- [ ] Verify image on [Docker Hub](https://hub.docker.com)
- [ ] Set `OPENROUTER_API_KEY` on target server
- [ ] Deploy: `./deploy.sh deploy-hub`
- [ ] Test: `curl http://localhost:8001/api/health`
- [ ] Access API docs: `http://localhost:8001/docs`

## 🔧 Troubleshooting

### Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

### Push Rate Limits
```bash
# Wait or upgrade to Docker Hub Pro
# Use multi-stage builds to reduce pushes
```

### API Key Not Working
```bash
# Verify environment variable
echo $OPENROUTER_API_KEY

# Check container environment
docker exec mcrag-backend env | grep OPENROUTER
```

## 🎯 Production Tips

1. **Use specific version tags**, not 'latest' in production
2. **Set resource limits** in docker-compose.yml
3. **Enable monitoring** and logging
4. **Use secrets management** for API keys
5. **Set up health checks** and restart policies
6. **Configure reverse proxy** (nginx) for SSL

Your MCRAG backend is now ready for global deployment! 🚀