# Docker Deployment Guide for FinWise-AI Backend

This guide provides comprehensive instructions for building and deploying the FinWise-AI backend using Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Building the Image](#building-the-image)
- [Running with Docker](#running-with-docker)
- [Running with Docker Compose](#running-with-docker-compose)
- [Configuration](#configuration)
- [Volume Management](#volume-management)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Image Optimization Details](#image-optimization-details)

## Quick Start

The fastest way to get started:

```bash
# 1. Create .env file with required variables
cat > .env << EOF
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
OPENAI_API_KEY=your-openrouter-api-key-here
DATABASE_URL=sqlite:///database.db
ALGORITHM=HS256
EOF

# 2. Build and run with Docker Compose
docker-compose up -d

# 3. Access the API
curl http://localhost:8000/api/v1/health/
```

## Prerequisites

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher (optional, but recommended)
- **API Keys**: OpenRouter or OpenAI API key for AI features

Install Docker:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh

# macOS (with Homebrew)
brew install docker docker-compose

# Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

## Building the Image

### Basic Build

```bash
cd backend
docker build -t finwise-backend:latest .
```

### Build with Custom Tag

```bash
docker build -t finwise-backend:v1.0.0 .
```

### Build Arguments

The Dockerfile doesn't require build arguments, but you can customize the build process:

```bash
# Use BuildKit for better caching (recommended)
DOCKER_BUILDKIT=1 docker build -t finwise-backend:latest .
```

### Build Time

- **First build**: 10-15 minutes (downloads all dependencies)
- **Subsequent builds**: 1-2 minutes (uses Docker layer caching)
- **Final image size**: ~2-3 GB (includes Tesseract, OCR models, Python packages)

## Running with Docker

### Basic Run

```bash
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your-secret-key-min-32-chars" \
  -e OPENAI_API_KEY="your-api-key" \
  -e DATABASE_URL="sqlite:///database.db" \
  -e ALGORITHM="HS256" \
  --name finwise-backend \
  finwise-backend:latest
```

### With Environment File

```bash
# Create .env file
cat > .env << EOF
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
OPENAI_API_KEY=your-openrouter-api-key-here
DATABASE_URL=sqlite:///database.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3
EOF

# Run with .env file
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name finwise-backend \
  finwise-backend:latest
```

### With Volumes for Persistence

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v finwise-uploads:/app/uploads \
  -v finwise-data:/app \
  --name finwise-backend \
  finwise-backend:latest
```

### Interactive Mode (for debugging)

```bash
docker run -it --rm \
  -p 8000:8000 \
  --env-file .env \
  finwise-backend:latest \
  /bin/bash
```

## Running with Docker Compose

Docker Compose simplifies multi-container setups and configuration management.

### Basic Usage

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View running containers
docker-compose ps
```

### With PostgreSQL (Recommended for Production)

Edit `docker-compose.yml` and uncomment the PostgreSQL service, then:

```bash
# Update .env file
echo "DATABASE_URL=postgresql://finwise:password@postgres:5432/finwise" >> .env
echo "DB_PASSWORD=your-secure-password" >> .env

# Start all services
docker-compose up -d

# Check PostgreSQL is ready
docker-compose exec postgres pg_isready -U finwise
```

### Scaling

```bash
# Run multiple backend instances (requires load balancer)
docker-compose up -d --scale backend=3
```

## Configuration

### Required Environment Variables

These **must** be set or the container will fail to start:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (32+ chars) | Generated with `secrets.token_urlsafe(32)` |
| `OPENAI_API_KEY` | OpenRouter/OpenAI API key | `sk-or-v1-...` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///database.db` | Database connection string |
| `PORT` | `8000` | Server port |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime in minutes |
| `MODELS` | `nvidia/llama-3.3-nemotron-70b-instruct` | AI model name |
| `TEMPERATURE` | `0.2` | LLM temperature (0-1) |
| `TOP_P` | `0.3` | LLM top-p sampling (0-1) |
| `FILE_STORAGE_TYPE` | `local` | Storage type (`local` or `s3`) |
| `LOCAL_STORAGE_PATH` | `uploads` | Local upload directory |

### Generating Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

## Volume Management

### Named Volumes

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect finwise-uploads

# Backup uploads
docker run --rm \
  -v finwise-uploads:/source \
  -v $(pwd):/backup \
  alpine tar czf /backup/uploads-backup.tar.gz -C /source .

# Restore uploads
docker run --rm \
  -v finwise-uploads:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/uploads-backup.tar.gz -C /target

# Remove volumes (CAUTION: data loss)
docker-compose down -v
```

### Bind Mounts (for Development)

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/database.db:/app/database.db \
  finwise-backend:latest
```

## Production Deployment

### Best Practices

1. **Use PostgreSQL instead of SQLite**
   ```bash
   DATABASE_URL=postgresql://user:password@host:5432/finwise
   ```

2. **Use External Storage (S3)**
   ```bash
   FILE_STORAGE_TYPE=s3
   S3_BUCKET=your-bucket-name
   S3_REGION=us-east-1
   S3_ACCESS_KEY=your-access-key
   S3_SECRET_KEY=your-secret-key
   ```

3. **Enable HTTPS with Reverse Proxy**
   ```yaml
   # Add nginx or traefik as reverse proxy
   # See examples in production-examples/ directory
   ```

4. **Resource Limits**
   ```yaml
   # In docker-compose.yml, add:
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
       reservations:
         cpus: '1'
         memory: 2G
   ```

5. **Health Checks**
   The Dockerfile includes a health check that runs every 30 seconds:
   ```bash
   docker inspect --format='{{.State.Health.Status}}' finwise-backend
   ```

6. **Logging**
   ```bash
   # Configure logging driver
   docker run -d \
     --log-driver json-file \
     --log-opt max-size=10m \
     --log-opt max-file=3 \
     finwise-backend:latest
   ```

### Production Deployment Options

#### Option 1: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml finwise

# Check services
docker service ls
docker service logs finwise_backend
```

#### Option 2: Kubernetes

```bash
# Create deployment
kubectl apply -f k8s/deployment.yml

# Expose service
kubectl apply -f k8s/service.yml

# Check status
kubectl get pods
kubectl logs -f deployment/finwise-backend
```

#### Option 3: Cloud Platform

**AWS ECS/Fargate:**
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
docker tag finwise-backend:latest $ECR_REGISTRY/finwise-backend:latest
docker push $ECR_REGISTRY/finwise-backend:latest

# Deploy to ECS (use AWS Console or CLI)
```

**Google Cloud Run:**
```bash
# Push to GCR
gcloud auth configure-docker
docker tag finwise-backend:latest gcr.io/$PROJECT_ID/finwise-backend:latest
docker push gcr.io/$PROJECT_ID/finwise-backend:latest

# Deploy
gcloud run deploy finwise-backend \
  --image gcr.io/$PROJECT_ID/finwise-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs finwise-backend

# Check environment variables
docker exec finwise-backend env | grep -E 'SECRET_KEY|OPENAI_API_KEY'

# Verify image
docker inspect finwise-backend:latest
```

### Cannot Connect to API

```bash
# Check if container is running
docker ps | grep finwise-backend

# Check port mapping
docker port finwise-backend

# Test from inside container
docker exec finwise-backend curl http://localhost:8000/api/v1/health/

# Check firewall
sudo ufw status
```

### Database Issues

```bash
# SQLite permissions
docker exec finwise-backend ls -la /app/database.db

# PostgreSQL connection
docker exec finwise-backend pg_isready -h postgres -U finwise

# View database logs
docker-compose logs postgres
```

### OCR Not Working

```bash
# Check Tesseract installation
docker exec finwise-backend tesseract --version
docker exec finwise-backend tesseract --list-langs

# Should show: eng, spa
```

### High Memory Usage

```bash
# Check memory usage
docker stats finwise-backend

# Reduce OCR workers or AI model size if needed
# Set resource limits in docker-compose.yml
```

### Build Failures

```bash
# Clear Docker cache and rebuild
docker builder prune
docker build --no-cache -t finwise-backend:latest .

# Check disk space
docker system df

# Clean up unused images
docker image prune -a
```

## Image Optimization Details

The Dockerfile is optimized for production with the following features:

### Multi-Stage Build
- **Stage 1 (builder)**: Compiles dependencies with build tools
- **Stage 2 (runtime)**: Minimal runtime image without build tools
- **Result**: 40-60% smaller image size

### Layer Optimization
- Dependencies installed before copying application code
- Leverages Docker layer caching for faster rebuilds
- Only changes to dependencies trigger full rebuild

### Security Features
- Non-root user (`appuser`) with UID 1001
- Minimal base image (Python 3.13 slim)
- No shell in production container
- Read-only filesystem where possible

### Performance Optimizations
- uv package manager (3-10x faster than pip)
- Frozen dependencies (no version resolution)
- Compiled Python bytecode excluded (`PYTHONDONTWRITEBYTECODE=1`)
- Unbuffered output (`PYTHONUNBUFFERED=1`)

### Size Comparison
- Base Python image: ~180 MB
- With dependencies: ~2-3 GB
- Alternative (without OCR): ~800 MB

### Build Time Optimization
- BuildKit for parallel layer building
- Dependency caching across builds
- Multi-stage builds for efficient layering

## Additional Resources

- [Main Backend README](README.md) - Comprehensive backend documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)
- [Multi-Language OCR Guide](docs/MULTILANG_OCR.md) - OCR usage guide
- [Docker Documentation](https://docs.docker.com/) - Official Docker docs
- [Docker Compose Documentation](https://docs.docker.com/compose/) - Compose reference

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/yeferson59/FinWise-AI/issues
- **Maintainers**: @yeferson59, @Windhoek-dev

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-24
