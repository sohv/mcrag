# Docker Deployment Guide for MCRAG Backend API

This guide explains how to deploy the MCRAG backend API using Docker and Docker Compose.

## Prerequisites

- **Docker** installed and running
- **Docker Compose** (v2.0+ recommended)
- **OpenRouter API key** for LLM access

## Quick Start

1. **Set your OpenRouter API key:**
   ```bash
   export OPENROUTER_API_KEY=your_api_key_here
   ```

2. **Deploy with one command:**
   ```bash
   ./deploy.sh
   ```

3. **Access the API:**
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs
   - Health Check: http://localhost:8001/api/health

## Deployment Commands

```bash
# Deploy (build and start)
./deploy.sh deploy

# Check status
./deploy.sh status

# View live logs
./deploy.sh logs

# Stop services
./deploy.sh stop

# Clean up everything
./deploy.sh cleanup
```

## Architecture

The Docker deployment includes:

- **mcrag-backend**: Main FastAPI application
- **redis**: Redis database for session storage
- **Persistent volumes**: For Redis data and application logs

## Configuration

### Environment Variables

Key environment variables (set in `docker-compose.yml`):

```yaml
REDIS_URL: redis://redis:6379
OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
MODEL_GENERATOR: google/gemini-flash-1.5
MODEL_CRITIC1: openai/gpt-4o-mini
MODEL_CRITIC2: deepseek/deepseek-r1
```

### Port Mapping

- **8001**: Backend API (FastAPI)
- **6379**: Redis (internal access only)

## Production Considerations

### Security

1. **Non-root user**: Container runs as `mcrag` user
2. **Minimal base image**: Uses `python:3.12-slim`
3. **Health checks**: Automatic service monitoring
4. **Environment isolation**: Containerized services

### Performance

1. **Multi-stage build**: Optimized image size
2. **UV package manager**: Fast dependency installation
3. **Layer caching**: Efficient rebuilds
4. **Resource limits**: Add to `docker-compose.yml` if needed:

```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

### Monitoring

```bash
# Check service health
curl http://localhost:8001/api/health

# Monitor logs
docker-compose logs -f mcrag-backend

# Check resource usage
docker stats
```

## Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using ports
   lsof -i :8001
   lsof -i :6379
   ```

2. **API key issues:**
   ```bash
   # Verify environment variable
   echo $OPENROUTER_API_KEY
   
   # Check container environment
   docker-compose exec mcrag-backend env | grep OPENROUTER
   ```

3. **Build failures:**
   ```bash
   # Clean build
   docker-compose build --no-cache
   
   # Check disk space
   df -h
   docker system df
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f mcrag-backend
docker-compose logs -f redis

# Execute commands in container
docker-compose exec mcrag-backend bash
docker-compose exec redis redis-cli
```

## Scaling and Production Deployment

### Multiple Workers

For production, consider using multiple Uvicorn workers:

```dockerfile
CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### Reverse Proxy

Add nginx for SSL and load balancing:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - mcrag-backend
```

### Persistent Storage

Ensure data persistence:

```yaml
volumes:
  redis_data:
    driver: local
  app_logs:
    driver: local
```

## Development vs Production

### Development
- Uses `.env` file
- Debug mode enabled
- Hot reload with `--reload`

### Production
- Environment variables in `docker-compose.yml`
- Debug mode disabled
- Multiple workers
- Health checks enabled
- Resource limits set

## Backup and Recovery

### Redis Data Backup

```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/

# Restore Redis data
docker cp ./backup/dump.rdb $(docker-compose ps -q redis):/data/
docker-compose restart redis
```

### Application Logs

Logs are stored in `./logs` directory (mounted volume).

## Updates and Maintenance

```bash
# Update application
git pull
./deploy.sh stop
./deploy.sh deploy

# Update base images
docker-compose pull
./deploy.sh deploy

# Clean up old images
docker image prune -f
```