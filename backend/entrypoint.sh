#!/bin/bash
set -e

echo "=========================================="
echo "FinWise-AI Backend - Starting..."
echo "=========================================="

# Check if running as root (needed to fix volume permissions)
RUNNING_AS_ROOT=false
if [ "$(id -u)" -eq 0 ]; then
    RUNNING_AS_ROOT=true
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Function to check and create directory
check_and_create_dir() {
    local dir=$1
    local description=$2

    if [ ! -d "$dir" ]; then
        print_warning "$description directory does not exist: $dir"
        echo "  Attempting to create..."
        if mkdir -p "$dir" 2>/dev/null; then
            print_success "Created $description directory: $dir"
        else
            print_error "Failed to create $description directory: $dir"
            return 1
        fi
    else
        print_success "$description directory exists: $dir"
    fi

    # Check write permissions
    if [ -w "$dir" ]; then
        print_success "$description directory is writable"
    else
        print_error "$description directory is NOT writable!"
        ls -ld "$dir"
        return 1
    fi

    return 0
}

echo ""
echo "1. Checking User and Permissions..."
echo "----------------------------------------"
print_info "Current user: $(whoami)"
print_info "User ID: $(id -u)"
print_info "Group ID: $(id -g)"
print_info "Groups: $(groups)"

echo ""
echo "2. Checking Required Directories..."
echo "----------------------------------------"

# Check application directory
check_and_create_dir "/app" "Application root"

# Check data directory (for SQLite)
check_and_create_dir "/app/data" "Database"

# Check uploads directory
check_and_create_dir "/app/uploads" "Uploads" || true

# Check cache directories
check_and_create_dir "/tmp/numba_cache" "Numba cache" || true
check_and_create_dir "$HOME/.cache" "User cache" || true
check_and_create_dir "$HOME/.cache/huggingface" "Hugging Face cache" || true
check_and_create_dir "$HOME/.cache/torch" "PyTorch cache" || true

echo ""
echo "3. Fixing Permissions (if running as root)..."
echo "----------------------------------------"

# If running as root, fix permissions for volumes that might be mounted
if [ "$RUNNING_AS_ROOT" = true ]; then
    print_info "Running as root - fixing permissions for appuser..."

    # Fix ownership of critical directories
    chown -R appuser:appuser /app/data 2>/dev/null || print_warning "Could not change ownership of /app/data"
    chown -R appuser:appuser /app/uploads 2>/dev/null || print_warning "Could not change ownership of /app/uploads"
    chown -R appuser:appuser /tmp/numba_cache 2>/dev/null || print_warning "Could not change ownership of /tmp/numba_cache"
    chown -R appuser:appuser /home/appuser 2>/dev/null || print_warning "Could not change ownership of /home/appuser"

    print_success "Permissions fixed for appuser"
else
    print_info "Not running as root - skipping permission fixes"
fi

echo ""
echo "4. Checking Environment Variables..."
echo "----------------------------------------"

# Check required environment variables
if [ -z "$SECRET_KEY" ]; then
    print_error "SECRET_KEY is not set!"
    exit 1
else
    print_success "SECRET_KEY is set (${#SECRET_KEY} characters)"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    print_error "OPENAI_API_KEY is not set!"
    exit 1
else
    print_success "OPENAI_API_KEY is set"
fi

if [ -z "$DATABASE_URL" ]; then
    print_warning "DATABASE_URL is not set, using default"
else
    print_success "DATABASE_URL is set: $DATABASE_URL"

    # Check if SQLite and warn about path format
    if [[ "$DATABASE_URL" == sqlite:* ]]; then
        if [[ "$DATABASE_URL" == sqlite:////* ]]; then
            print_success "SQLite URL uses absolute path (4 slashes) ✓"
        else
            print_warning "SQLite URL uses relative path (3 slashes)"
            print_warning "Consider using absolute path: sqlite:////app/data/database.db"
        fi
    fi
fi

echo ""
echo "5. Cache Configuration..."
echo "----------------------------------------"
print_info "NUMBA_CACHE_DIR: ${NUMBA_CACHE_DIR:-not set}"
print_info "HF_HOME: ${HF_HOME:-not set}"
print_info "TRANSFORMERS_CACHE: ${TRANSFORMERS_CACHE:-not set}"
print_info "TORCH_HOME: ${TORCH_HOME:-not set}"

echo ""
echo "6. Application Configuration..."
echo "----------------------------------------"
print_info "APP_NAME: ${APP_NAME:-FinWise API}"
print_info "PORT: ${PORT:-8000}"
print_info "ENVIRONMENT: ${ENVIRONMENT:-production}"
print_info "VERSION: ${VERSION:-1.0.0}"
print_info "PREFIX_API: ${PREFIX_API:-/api/v1}"

echo ""
echo "7. Storage Configuration..."
echo "----------------------------------------"
print_info "FILE_STORAGE_TYPE: ${FILE_STORAGE_TYPE:-local}"
print_info "LOCAL_STORAGE_PATH: ${LOCAL_STORAGE_PATH:-uploads}"

echo ""
echo "8. Directory Permissions Summary..."
echo "----------------------------------------"
ls -la /app/ | head -10
echo ""
ls -ld /app/data /app/uploads 2>/dev/null || true
echo ""

echo ""
echo "=========================================="
echo "All checks passed! Starting application..."
echo "=========================================="
echo ""

# Start the application
# If running as root, switch to appuser before starting
if [ "$RUNNING_AS_ROOT" = true ]; then
    print_info "Switching to appuser and starting application..."
    # Use su to run as appuser, with proper environment
    exec su appuser -c "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} $*"
else
    print_info "Starting application as current user..."
    # Already running as appuser (or another non-root user)
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
fi
