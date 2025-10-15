set -e

# Configuration
DOCKER_IMAGE_NAME="mcrag-backend"
DOCKER_HUB_USERNAME=""  # Set your Docker Hub username here

# check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo " Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# check for required environment variable
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo " OPENROUTER_API_KEY environment variable is not set."
    echo "   Please set it before running this script:"
    echo "   export OPENROUTER_API_KEY=your_api_key_here"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to build and start services
deploy() {
    echo "📦 Building Docker images..."
    docker-compose build --no-cache
    
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check service health
    echo "🔍 Checking service health..."
    
    # Check Redis
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis is healthy"
    else
        echo "❌ Redis health check failed"
    fi
    
    # Check Backend API
    if curl -f http://localhost:8001/api/health &> /dev/null; then
        echo "✅ Backend API is healthy"
    else
        echo "❌ Backend API health check failed"
        echo "📋 Checking logs..."
        docker-compose logs mcrag-backend
    fi
}

# Function to show status
status() {
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "📋 Recent Logs:"
    docker-compose logs --tail=20
}

# Function to stop services
stop() {
    echo "🛑 Stopping services..."
    docker-compose down
}

# Function to clean up (remove containers and images)
cleanup() {
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down -v --rmi all
    docker system prune -f
}

# Function to build and push to Docker Hub
push_to_dockerhub() {
    if [ -z "$DOCKER_HUB_USERNAME" ]; then
        echo "❌ DOCKER_HUB_USERNAME not set in deploy.sh"
        echo "   Please edit deploy.sh and set your Docker Hub username"
        exit 1
    fi
    
    echo "🐳 Building and pushing to Docker Hub..."
    
    # Get version tag (use git tag or default to 'latest')
    if git describe --tags --exact-match 2>/dev/null; then
        VERSION=$(git describe --tags --exact-match)
    else
        VERSION="latest"
    fi
    
    IMAGE_TAG="$DOCKER_HUB_USERNAME/$DOCKER_IMAGE_NAME:$VERSION"
    IMAGE_LATEST="$DOCKER_HUB_USERNAME/$DOCKER_IMAGE_NAME:latest"
    
    echo "📦 Building image: $IMAGE_TAG"
    docker build -t $IMAGE_TAG .
    
    # Also tag as latest
    if [ "$VERSION" != "latest" ]; then
        docker tag $IMAGE_TAG $IMAGE_LATEST
    fi
    
    # Check if logged into Docker Hub
    if ! docker info | grep -q "Username:"; then
        echo "🔐 Please log in to Docker Hub:"
        docker login
    fi
    
    echo "📤 Pushing $IMAGE_TAG to Docker Hub..."
    docker push $IMAGE_TAG
    
    if [ "$VERSION" != "latest" ]; then
        echo "📤 Pushing $IMAGE_LATEST to Docker Hub..."
        docker push $IMAGE_LATEST
    fi
    
    echo "✅ Successfully pushed to Docker Hub!"
    echo "📍 Image: https://hub.docker.com/r/$DOCKER_HUB_USERNAME/$DOCKER_IMAGE_NAME"
    echo "🐳 Pull command: docker pull $IMAGE_TAG"
}

# Function to deploy from Docker Hub
deploy_from_hub() {
    if [ -z "$DOCKER_HUB_USERNAME" ]; then
        echo "❌ DOCKER_HUB_USERNAME not set in deploy.sh"
        exit 1
    fi
    
    VERSION="${1:-latest}"
    IMAGE_TAG="$DOCKER_HUB_USERNAME/$DOCKER_IMAGE_NAME:$VERSION"
    
    echo "🐳 Deploying from Docker Hub: $IMAGE_TAG"
    
    # Create a temporary docker-compose file for Hub deployment
    cat > docker-compose.hub.yml << EOF
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: mcrag-redis
    restart: unless-stopped
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcrag-backend:
    image: $IMAGE_TAG
    container_name: mcrag-backend
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      REDIS_URL: redis://redis:6379
      BACKEND_HOST: 0.0.0.0
      BACKEND_PORT: 8001
      OPENROUTER_API_KEY: \${OPENROUTER_API_KEY}
      OPENROUTER_URL: https://openrouter.ai/api/v1
      MODEL_GENERATOR: google/gemini-flash-1.5
      MODEL_CRITIC1: openai/gpt-4o-mini
      MODEL_CRITIC2: deepseek/deepseek-r1
      DEBUG: "false"
      LOG_LEVEL: INFO
      PYTHONUNBUFFERED: "1"
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  redis_data:
    driver: local

networks:
  default:
    name: mcrag-network
EOF

    echo "🚀 Starting services from Docker Hub..."
    docker-compose -f docker-compose.hub.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check health using the same logic as deploy()
    echo "🔍 Checking service health..."
    if docker-compose -f docker-compose.hub.yml exec redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis is healthy"
    else
        echo "❌ Redis health check failed"
    fi
    
    if curl -f http://localhost:8001/api/health &> /dev/null; then
        echo "✅ Backend API is healthy"
    else
        echo "❌ Backend API health check failed"
    fi
    
    echo "🎉 Deployment from Docker Hub complete!"
    echo "📍 Backend API: http://localhost:8001"
}

# Function to clean up (remove containers and images)
cleanup() {
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down -v --rmi all
    # Also clean up hub deployment if exists
    if [ -f docker-compose.hub.yml ]; then
        docker-compose -f docker-compose.hub.yml down -v 2>/dev/null || true
        rm -f docker-compose.hub.yml
    fi
    docker system prune -f
}

# Main menu
case "${1:-deploy}" in
    "deploy")
        deploy
        echo ""
        echo "🎉 Deployment complete!"
        echo "📍 Backend API: http://localhost:8001"
        echo "📍 API Docs: http://localhost:8001/docs"
        echo "📍 Health Check: http://localhost:8001/api/health"
        echo ""
        echo "💡 Useful commands:"
        echo "   ./deploy.sh status  - Check service status"
        echo "   ./deploy.sh stop    - Stop services"
        echo "   ./deploy.sh logs    - View logs"
        echo "   ./deploy.sh cleanup - Remove all containers and images"
        ;;
    "status")
        status
        ;;
    "stop")
        stop
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "cleanup")
        cleanup
        ;;
    "push")
        push_to_dockerhub
        ;;
    "deploy-hub")
        deploy_from_hub "${2:-latest}"
        ;;
    *)
        echo "Usage: $0 {deploy|status|stop|logs|cleanup|push|deploy-hub}"
        echo ""
        echo "Commands:"
        echo "  deploy     - Build and start services locally (default)"
        echo "  status     - Show service status and recent logs"
        echo "  stop       - Stop all services"
        echo "  logs       - Follow live logs"
        echo "  cleanup    - Remove all containers, volumes, and images"
        echo "  push       - Build and push image to Docker Hub"
        echo "  deploy-hub - Deploy from Docker Hub (usage: deploy-hub [version])"
        exit 1
        ;;
esac