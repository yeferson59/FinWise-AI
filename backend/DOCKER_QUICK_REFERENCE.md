# Quick Reference: Docker Commands for FinWise-AI Backend

This is a quick reference for the most commonly used Docker commands for the FinWise-AI backend.

## Quick Start (30 seconds)

```bash
cd backend
cp .env.docker.example .env
# Edit .env with your SECRET_KEY and OPENAI_API_KEY
docker-compose up -d
```

## Building

```bash
# Build the image
docker build -t finwise-backend:latest .

# Build with no cache (clean build)
docker build --no-cache -t finwise-backend:latest .

# Build with BuildKit (faster)
DOCKER_BUILDKIT=1 docker build -t finwise-backend:latest .
```

## Running

```bash
# Run with docker-compose (recommended)
docker-compose up -d

# Run standalone
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v finwise-uploads:/app/uploads \
  --name finwise-backend \
  finwise-backend:latest

# Run with PostgreSQL
docker-compose --profile postgres up -d
```

## Viewing Logs

```bash
# View logs (docker-compose)
docker-compose logs -f backend

# View logs (standalone)
docker logs -f finwise-backend

# View last 100 lines
docker logs --tail 100 finwise-backend
```

## Stopping & Starting

```bash
# Stop services
docker-compose stop
# Or
docker stop finwise-backend

# Start services
docker-compose start
# Or
docker start finwise-backend

# Restart services
docker-compose restart
# Or
docker restart finwise-backend

# Stop and remove
docker-compose down
# Or
docker stop finwise-backend && docker rm finwise-backend
```

## Debugging

```bash
# Shell into running container
docker exec -it finwise-backend /bin/bash

# Check container status
docker ps
docker inspect finwise-backend

# Check health status
docker inspect --format='{{.State.Health.Status}}' finwise-backend

# Check environment variables
docker exec finwise-backend env
```

## Database

```bash
# SQLite: Copy database out
docker cp finwise-backend:/app/database.db ./database-backup.db

# PostgreSQL: Backup
docker-compose exec postgres pg_dump -U finwise finwise > backup.sql

# PostgreSQL: Restore
docker-compose exec -T postgres psql -U finwise finwise < backup.sql

# PostgreSQL: Shell
docker-compose exec postgres psql -U finwise
```

## Volumes

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

## Cleaning Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything (CAUTION)
docker system prune -a --volumes

# Check disk usage
docker system df
```

## Health & Monitoring

```bash
# Check health
curl http://localhost:8000/api/v1/health/

# View resource usage
docker stats finwise-backend

# View container events
docker events --filter container=finwise-backend
```

## Common Issues

### Container won't start
```bash
# Check logs
docker logs finwise-backend

# Check environment
docker exec finwise-backend env | grep SECRET_KEY
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Change port in docker-compose.yml or use different port
docker run -p 8080:8000 ...
```

### Out of disk space
```bash
# Check usage
docker system df

# Clean up
docker system prune -a --volumes
```

## Production Deployment

```bash
# Build with version tag
docker build -t finwise-backend:v1.0.0 .

# Tag for registry
docker tag finwise-backend:v1.0.0 your-registry/finwise-backend:v1.0.0

# Push to registry
docker push your-registry/finwise-backend:v1.0.0

# Pull on production server
docker pull your-registry/finwise-backend:v1.0.0

# Run in production
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  --name finwise-backend \
  your-registry/finwise-backend:v1.0.0
```

## Docker Compose Shortcuts

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose stop

# Remove services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Scale service
docker-compose up -d --scale backend=3

# Run command in service
docker-compose exec backend python -c "print('hello')"
```

## Testing in Docker

```bash
# Run tests in container
docker-compose exec backend pytest

# Run tests with coverage
docker-compose exec backend pytest --cov=app

# Run specific test
docker-compose exec backend pytest tests/test_main.py
```

## Environment Management

```bash
# Copy example env
cp .env.docker.example .env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Validate env file
docker-compose config

# Use different env file
docker-compose --env-file .env.production up -d
```

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Docker
alias d='docker'
alias dc='docker-compose'
alias dps='docker ps'
alias dl='docker logs'
alias dex='docker exec -it'

# FinWise-specific
alias fw-up='cd ~/FinWise-AI/backend && docker-compose up -d'
alias fw-down='cd ~/FinWise-AI/backend && docker-compose down'
alias fw-logs='cd ~/FinWise-AI/backend && docker-compose logs -f backend'
alias fw-shell='docker exec -it finwise-backend /bin/bash'
alias fw-test='docker-compose exec backend pytest'
```

## More Information

- Full deployment guide: [DOCKER.md](DOCKER.md)
- Optimization details: [DOCKERFILE_OPTIMIZATION.md](DOCKERFILE_OPTIMIZATION.md)
- Backend README: [README.md](README.md)

---

**Tip**: Bookmark this file for quick access to common commands!
