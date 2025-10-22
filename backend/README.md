# FinWise-AI Backend

A FastAPI-based backend for a personal finance management application with AI-powered assistance. This backend provides RESTful APIs for user management, authentication, transaction tracking, category management, and AI-driven financial insights with advanced OCR capabilities.

## Table of Contents

- [Overview](#overview)
- [Current Status](#current-status)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

## Overview

FinWise-AI Backend is a modern, production-ready API service built with FastAPI that serves as the core backend for a personal finance management system. It combines traditional CRUD operations with cutting-edge AI capabilities to provide intelligent financial insights and automated document processing.

### Key Responsibilities

- **User Management**: Registration, authentication, and profile management with secure JWT tokens
- **Transaction Management**: Track income and expenses with categorization
- **Category Management**: Organize financial transactions by custom categories
- **AI Assistant**: Interactive chat-based financial advisor powered by LLMs
- **OCR Processing**: Extract text from receipts, invoices, and financial documents in multiple languages
- **API Gateway**: RESTful API with versioning, OpenAPI documentation, and standardized error handling

## Current Status

**Version**: 0.1.0  
**Environment**: Active Development  
**Stability**: Core features stable, advanced features in progress

### Feature Status

Based on [Issue #1 - Phase Requirements](https://github.com/yeferson59/FinWise-AI/issues/1):

#### ✅ Fully Implemented Features

**1. User Management & Authentication**
- ✅ User registration with email and password validation
- ✅ Secure password hashing using Argon2id (via pwdlib)
- ✅ JWT-based authentication with configurable expiration
- ✅ Session management (login/logout)
- ✅ Full CRUD operations for users
- ✅ Pagination support for user listing
- ✅ Email-based user lookup

**2. AI Virtual Assistant**
- ✅ OpenAI/OpenRouter integration via Pydantic AI
- ✅ ReAct (Reasoning + Acting) agent pattern
- ✅ Tool-calling capabilities for database queries
- ✅ Configurable model parameters (temperature, top_p)
- ✅ Context-aware conversation handling
- ✅ Multiple model support (NVIDIA Llama 3.3 Nemotron by default)

**3. Multi-Language OCR (Document Text Extraction)**
- ✅ Support for English and Spanish (eng+spa)
- ✅ Intelligent extraction with multiple fallback strategies
- ✅ Automatic language detection
- ✅ Document type optimization (receipts, invoices, forms, etc.)
- ✅ Quality validation with actionable recommendations
- ✅ Text cleaning and normalization
- ✅ Confidence scoring for extraction accuracy
- ✅ Support for PDFs and images (JPG, PNG, TIFF, etc.)

**4. Transaction Management (Basic CRUD)**
- ✅ Transaction model with user, category, and source relations
- ✅ CRUD endpoints for transactions
- ✅ Date tracking and amount validation
- ✅ Transaction state management (pending, completed, etc.)

**5. Category Management**
- ✅ Category CRUD operations
- ✅ Unique category names with descriptions
- ✅ Full integration with transaction system

#### 🚧 Partially Implemented Features

**Transaction Classification & Reporting**
- ⚠️ Category structure ready, automatic classification pending
- ⚠️ Transaction endpoints functional, advanced filtering not yet implemented
- ⚠️ No automated expense/income categorization via AI yet

**Reports Generation**
- ⚠️ Router structure created, no endpoints implemented
- ⚠️ No PDF export capability yet
- ⚠️ No data visualization endpoints

**Notifications/Reminders**
- ⚠️ Router structure created, no endpoints implemented
- ⚠️ No notification model or service logic
- ⚠️ No email/push notification integration

#### ❌ Not Yet Implemented

**Financial Health Assessment**
- ❌ No scoring algorithm
- ❌ No AI-based recommendations for financial health
- ❌ No spending pattern analysis

## Technical Stack

- **Language**: Python 3.13+ (minimum 3.13 required)
- **Framework**: FastAPI 0.118.3+ with async/await support
- **Database**: SQLite (development) with SQLModel ORM
- **Authentication**: JWT tokens with HS256 algorithm
- **Password Security**: Argon2id hashing via pwdlib
- **AI/ML**: 
  - Pydantic AI 1.0.17+ with OpenAI/OpenRouter providers
  - NVIDIA Llama 3.3 Nemotron (default model via OpenRouter)
- **OCR Libraries**: 
  - Tesseract 5.3+ (primary engine)
  - EasyOCR (fallback)
  - PaddleOCR (fallback)
  - DocTR (experimental)
- **Image Processing**: OpenCV, Pillow, PyMuPDF
- **Package Management**: uv (astral.sh)
- **Code Quality**: Ruff (linter + formatter), Zuban
- **Testing**: pytest with httpx for API testing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│                        (app/main.py)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼──────────┐            ┌────────▼────────┐
│   API Routes     │            │   Middleware    │
│   (/api/v1/)     │            │   & CORS        │
└───────┬──────────┘            └─────────────────┘
        │
        ├─── /auth          (Login, Register, Logout)
        ├─── /users         (User CRUD)
        ├─── /agents        (AI Chat - Basic & ReAct)
        ├─── /files         (OCR & Document Processing)
        ├─── /transactions  (Transaction CRUD)
        ├─── /categories    (Category CRUD)
        ├─── /reports       (Placeholder)
        ├─── /notifications (Placeholder)
        └─── /health        (Health Check)
                │
        ┌───────┴──────────────────────────────┐
        │                                      │
┌───────▼────────┐                  ┌─────────▼────────┐
│   Services     │                  │   Core Modules   │
│   (Business    │                  │   (Security,     │
│    Logic)      │                  │    LLM, Tasks)   │
└───────┬────────┘                  └─────────┬────────┘
        │                                     │
        │  ┌──────────────────────────────────┘
        │  │
┌───────▼──▼─────────┐
│   Database Layer   │
│   (SQLModel/       │
│    SQLite)         │
└────────────────────┘

External Services:
  - OpenRouter (AI Models)
  - Tesseract OCR (Local)
```

### Directory Structure

The backend follows a **clean architecture** pattern with clear separation of concerns:

- **`app/api/`**: REST endpoints and request/response handling
  - `v1/endpoints/`: Versioned API endpoints
  - `deps.py`: Shared dependencies (auth, session)
  
- **`app/services/`**: Business logic implementation
  - `user.py`, `auth.py`, `transaction.py`, `category.py`
  - `extraction.py`, `intelligent_extraction.py` (OCR)
  - `agent.py` (AI agent orchestration)
  
- **`app/models/`**: Database models using SQLModel
  - `user.py`, `transaction.py`, `category.py`, `auth.py`
  
- **`app/schemas/`**: Pydantic models for API validation
  - Request/response DTOs for each domain
  
- **`app/core/`**: Core utilities and configurations
  - `security.py`: JWT, password hashing, session management
  - `llm.py`: LLM model initialization
  - `event_handlers.py`: Application lifecycle events
  
- **`app/db/`**: Database connection and session management
  - `session.py`: SQLModel engine and session factory
  - `base.py`: Base models and utilities

- **`app/ocr_config/`**: OCR configuration profiles
  - Document-specific OCR settings

- **`app/utils/`**: Shared utilities
  - `db.py`: Database helper functions
  - `ai_parsers.py`: AI response parsing
  - `pdf_generator.py`: PDF utilities

## Prerequisites

### System Requirements

- **Python**: 3.13 or higher (required for compatibility)
- **Operating System**: Linux, macOS, or Windows (with WSL recommended)
- **Memory**: 4GB RAM minimum, 8GB recommended (for OCR processing)
- **Disk Space**: 2GB minimum (includes dependencies and OCR language packs)

### Required Software

1. **uv Package Manager**
   ```bash
   # Install uv (https://docs.astral.sh/uv/)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or using pip
   pip install uv
   ```

2. **Tesseract OCR with Language Packs**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
   
   # macOS
   brew install tesseract tesseract-lang
   
   # Windows (via Chocolatey)
   choco install tesseract
   # Then download language packs from: https://github.com/tesseract-ocr/tessdata
   ```

3. **API Keys**
   - OpenRouter API key (for AI features): https://openrouter.ai/
   - Alternative: OpenAI API key (requires code modification)

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yeferson59/FinWise-AI.git
cd FinWise-AI/backend
```

### 2. Install Dependencies

```bash
# Sync all dependencies (production + dev)
uv sync

# Or install only production dependencies
uv sync --no-dev
```

This will:
- Create a virtual environment automatically
- Install all required Python packages
- Lock dependency versions in `uv.lock`

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env  # If example exists, or create manually
```

**Required `.env` Configuration:**

```env
# Application
APP_NAME=FinWise API
PORT=8000
ENVIRONMENT=development
VERSION=1.0.0
PREFIX_API=/api/v1

# Database
DATABASE_URL=sqlite:///database.db

# Security (JWT)
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI/LLM Configuration
OPENAI_API_KEY=your-openrouter-api-key-here
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3

# File Storage
FILE_STORAGE_TYPE=local
LOCAL_STORAGE_PATH=uploads

# Optional: S3 Storage (for production)
# S3_BUCKET=your-bucket-name
# S3_REGION=us-east-1
# S3_ACCESS_KEY=your-access-key
# S3_SECRET_KEY=your-secret-key
# S3_ENDPOINT=https://s3.amazonaws.com
```

**Environment Variable Details:**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT token signing key (min 32 chars) | - | ✅ |
| `OPENAI_API_KEY` | OpenRouter/OpenAI API key | - | ✅ (for AI) |
| `DATABASE_URL` | Database connection string | `sqlite:///database.db` | ✅ |
| `ALGORITHM` | JWT algorithm | `HS256` | ✅ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` | ❌ |
| `MODELS` | Comma-separated model names | `nvidia/llama-3.3-nemotron-70b-instruct` | ❌ |
| `TEMPERATURE` | LLM temperature (0-1) | `0.2` | ❌ |
| `TOP_P` | LLM top-p sampling (0-1) | `0.3` | ❌ |
| `FILE_STORAGE_TYPE` | Storage backend (`local` or `s3`) | `local` | ❌ |

### 4. Initialize Database

The database is automatically created on first run. Tables are initialized via SQLModel's `create_all()` in the application startup event.

**Manual migration (if needed):**
```bash
# The app handles this automatically, but for reference:
uv run python -c "from app.db.session import init_db; init_db()"
```

### 5. Verify Installation

```bash
# Check dependencies
uv tree

# Verify Tesseract
tesseract --version
tesseract --list-langs  # Should show 'eng' and 'spa'

# Test Python version
python --version  # Should be 3.13+
```

## Running the Application

### Development Server

Start the development server with auto-reload:

```bash
# Using uv (recommended)
uv run fastapi dev app/main.py

# Using Makefile
make run-backend

# Direct with uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **API Prefix**: http://localhost:8000/api/v1/
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

### Production Server

For production, use a production-grade ASGI server:

```bash
# Using uvicorn with workers
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn with uvicorn workers (recommended for production)
uv run gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Development Commands

The project uses a `Makefile` for common tasks:

```bash
# Run backend server
make run-backend

# Install dependencies
make sync-backend

# Add new dependencies
make add-backend-deps DEPS="package-name"

# Add dev dependencies
make add-backend-dev-deps DEPS="pytest"

# Code quality
make lint-backend        # Run linting checks
make format-backend      # Auto-format code

# Testing
make run-test-backend       # Run all tests
make run-test-backend-info  # Run tests with verbose output

# Cleanup
make clean-backend       # Remove cache directories
```

## API Documentation

### Interactive Documentation

Once the server is running, access the auto-generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer
  - Test endpoints directly from browser
  - View request/response schemas
  
- **ReDoc**: http://localhost:8000/redoc
  - Clean, readable documentation
  - Better for reference and sharing

### API Endpoints Overview

All endpoints are versioned under `/api/v1/` prefix.

#### Authentication & Users

**Base Path**: `/api/v1/auth` and `/api/v1/users`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | ❌ |
| POST | `/auth/login` | User login (returns JWT) | ❌ |
| POST | `/auth/logout` | User logout | ✅ |
| GET | `/users/` | List all users (paginated) | ✅ |
| POST | `/users/` | Create new user | ✅ |
| GET | `/users/{user_id}` | Get user by ID | ✅ |
| PATCH | `/users/{user_id}` | Update user | ✅ |
| DELETE | `/users/{user_id}` | Delete user | ✅ |
| GET | `/users/email/{email}` | Get user by email | ✅ |

**Example: Login Request**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Transactions

**Base Path**: `/api/v1/transactions`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/transactions/` | List all transactions | ✅ |
| POST | `/transactions/` | Create transaction | ✅ |
| GET | `/transactions/{id}` | Get transaction by ID | ✅ |
| PUT | `/transactions/{id}` | Update transaction | ✅ |
| DELETE | `/transactions/{id}` | Delete transaction | ✅ |

**Example: Create Transaction**
```bash
curl -X POST "http://localhost:8000/api/v1/transactions/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "category_id": 1,
    "source_id": 1,
    "description": "Grocery shopping",
    "amount": 50.75,
    "date": "2024-01-15T10:30:00Z",
    "state": "completed"
  }'
```

#### Categories

**Base Path**: `/api/v1/categories`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/categories/` | List all categories | ✅ |
| POST | `/categories/` | Create category | ✅ |
| GET | `/categories/{id}` | Get category by ID | ✅ |
| PATCH | `/categories/{id}` | Update category | ✅ |
| DELETE | `/categories/{id}` | Delete category | ✅ |

#### AI Agents

**Base Path**: `/api/v1/agents`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/agents/` | Basic AI chat | ✅ |
| POST | `/agents/react` | ReAct agent (with tools) | ✅ |

**Example: AI Chat**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/react" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many users are in the system?",
    "top_p": 0.3,
    "temperature": 0.2
  }'
```

#### Files & OCR

**Base Path**: `/api/v1/files`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/files/extract-text` | Basic text extraction | ✅ |
| POST | `/files/extract-text-with-confidence` | Extraction with confidence scores | ✅ |
| POST | `/files/extract-text-intelligent` | Advanced extraction with fallbacks ⭐ | ✅ |
| GET | `/files/document-types` | List supported document types | ❌ |
| GET | `/files/supported-languages` | List OCR languages (eng, spa, eng+spa) | ❌ |

**Example: Intelligent OCR**
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text-intelligent" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@receipt.jpg" \
  -F "document_type=receipt" \
  -F "language=eng+spa"
```

**Supported Document Types:**
- `receipt` - Retail receipts
- `invoice` - Business invoices
- `form` - Forms and applications
- `contract` - Legal contracts
- `id` - ID cards and documents
- `bank_statement` - Bank statements
- `general` - Generic documents

#### Health Check

**Base Path**: `/api/v1/health`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health/` | Service health status | ❌ |

#### Placeholder Endpoints (Not Yet Implemented)

- **Reports**: `/api/v1/reports` - No endpoints yet
- **Notifications**: `/api/v1/notifications` - No endpoints yet

### Authentication

Most endpoints require JWT authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Additional Documentation

For detailed OCR usage and examples:
- [Multi-Language OCR Guide](docs/MULTILANG_OCR.md) - Complete OCR documentation
- [API Examples](docs/API_EXAMPLES.md) - cURL, Python, JavaScript examples
- [OCR Improvements](MEJORAS_OCR.md) - Technical improvements (Spanish)

## Testing

### Test Structure

Tests are organized in the `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_main.py                   # Application startup tests
├── test_multilang_ocr_api.py      # OCR API integration tests
└── test_api/
    └── test_agent.py              # AI agent tests
```

### Running Tests

**Run all tests:**
```bash
# Using Makefile
make run-test-backend

# Using pytest directly
uv run pytest

# With verbose output
make run-test-backend-info
uv run pytest -v
```

**Run specific test file:**
```bash
uv run pytest tests/test_multilang_ocr_api.py -v
```

**Run with coverage:**
```bash
uv run pytest --cov=app --cov-report=html
```

**Test environment:**
Tests use `.env.test` if present, otherwise fall back to `.env`. Create `.env.test` for isolated test configuration:

```env
DATABASE_URL=sqlite:///test_database.db
ENVIRONMENT=testing
SECRET_KEY=test-secret-key-for-testing-only
OPENAI_API_KEY=test-key-or-real-key-for-integration-tests
```

### Test Coverage Status

| Module | Coverage | Status |
|--------|----------|--------|
| User Management | ✅ High | Stable |
| Authentication | ✅ High | Stable |
| AI Agents | ⚠️ Partial | Needs mocking |
| OCR Services | ✅ Good | Integration tests exist |
| Transactions | ❌ Low | Needs tests |
| Categories | ❌ Low | Needs tests |

### OCR Testing

**Unit Tests:**
```bash
# Run standalone OCR tests (doesn't require server)
uv run python test_multilang_ocr.py
```

**Demonstration:**
```bash
# Interactive OCR demonstration
uv run python demo_multilang_ocr.py
```

**Verification:**
```bash
# Verify OCR implementation status
uv run python verify_ocr_implementation.py
```

### Writing Tests

Example test structure using pytest:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_create_user(test_session):
    # Test with database session
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123!"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
```

### Test Dependencies

Test dependencies are managed separately in `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "httpx>=0.28.1",     # For TestClient
    "pytest>=8.4.2",     # Test framework
    "pytest-asyncio",    # Async test support
]
```

## Configuration

### Environment Files

- **`.env`**: Main configuration (not committed to git)
- **`.env.test`**: Test environment configuration
- **`.env.example`**: Template for new developers (should be committed)

### Configuration Management

Settings are managed via `app/config.py` using Pydantic Settings:

```python
from app.config import get_settings

settings = get_settings()  # Cached singleton
print(settings.database_url)
print(settings.openai_api_key)
```

### Database Configuration

**SQLite (Development - Default):**
```env
DATABASE_URL=sqlite:///database.db
```

**PostgreSQL (Production - Recommended):**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/finwise
```

**Note**: While SQLite works for development, PostgreSQL is recommended for production due to better concurrency, performance, and data integrity features.

### AI Model Configuration

The application uses OpenRouter by default but can be configured for direct OpenAI:

**OpenRouter (Default):**
```env
OPENAI_API_KEY=sk-or-v1-xxxxx  # OpenRouter API key
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
```

**Alternative models:**
- `meta-llama/llama-3.3-70b-instruct`
- `openai/gpt-4-turbo`
- `anthropic/claude-3-opus`

**Direct OpenAI** (requires code modification in `app/core/llm.py`):
```python
# Change from OpenRouterProvider to direct OpenAI
from pydantic_ai.models.openai import OpenAIChatModel

return OpenAIChatModel("gpt-4-turbo", api_key=settings.openai_api_key)
```

## Deployment

### Deployment Options

#### 1. Docker Deployment (Recommended)

**Note**: Dockerfile not yet created. When implementing:

```dockerfile
FROM python:3.13-slim

# Install Tesseract and system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install uv and dependencies
RUN pip install uv
RUN uv sync --no-dev

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Traditional Server Deployment

**Using systemd service:**

```ini
# /etc/systemd/system/finwise-backend.service
[Unit]
Description=FinWise Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/finwise-backend
Environment="PATH=/opt/finwise-backend/.venv/bin"
ExecStart=/opt/finwise-backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable finwise-backend
sudo systemctl start finwise-backend
sudo systemctl status finwise-backend
```

#### 3. Cloud Platform Deployment

**Render / Railway / Fly.io:**
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Configure build command: `uv sync`
4. Configure start command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**AWS / GCP / Azure:**
- Deploy with managed container services (ECS, Cloud Run, App Service)
- Use managed PostgreSQL for database
- Configure environment variables via platform secrets manager

### CI/CD Pipeline

#### Current Setup

**Dependabot** (`.github/dependabot.yml`):
- Automated dependency updates
- Weekly schedule (Monday 9 AM Colombia time)
- Separate configurations for backend (uv) and frontend (npm)
- Auto-assigns PRs to maintainers

#### Recommended GitHub Actions Workflow

**Not yet implemented**. Suggested `.github/workflows/backend-ci.yml`:

```yaml
name: Backend CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: cd backend && uv sync
      
      - name: Lint
        run: cd backend && uv run ruff check .
      
      - name: Run tests
        run: cd backend && uv run pytest
        env:
          ENVIRONMENT: testing
          SECRET_KEY: test-secret-key
```

### Environment-Specific Configuration

| Environment | Database | AI Model | Storage | Logging |
|-------------|----------|----------|---------|---------|
| Development | SQLite | Any | Local | DEBUG |
| Staging | PostgreSQL | GPT-4 Turbo | S3 | INFO |
| Production | PostgreSQL | Production model | S3/CloudStorage | WARNING |

**Production Checklist:**
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong `SECRET_KEY` (32+ random characters)
- [ ] Configure HTTPS/TLS termination
- [ ] Set up S3 or cloud storage for file uploads
- [ ] Enable production logging (not DEBUG)
- [ ] Configure CORS for frontend domain only
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure database backups
- [ ] Set resource limits (memory, CPU)
- [ ] Use environment variables, never commit secrets

## Roadmap

### Short-Term Priorities (Next 1-2 Sprints)

#### High Priority
- [ ] **Complete Transaction Management**
  - Owner: TBD
  - Add filtering by date range, category, user
  - Implement pagination for transaction listing
  - Add transaction statistics endpoints

- [ ] **Implement Reports System**
  - Owner: TBD
  - Monthly/weekly spending reports
  - Income vs expense analysis
  - Category breakdown charts
  - PDF export functionality

- [ ] **Add Test Coverage**
  - Owner: TBD
  - Transaction endpoint tests
  - Category endpoint tests
  - Integration tests for OCR
  - Authentication flow tests

#### Medium Priority
- [ ] **Notifications/Reminders**
  - Owner: TBD
  - Budget threshold alerts
  - Bill payment reminders
  - Email notification service

- [ ] **Database Migration**
  - Owner: TBD
  - Add Alembic for migrations
  - Support PostgreSQL
  - Migration scripts for schema changes

- [ ] **API Improvements**
  - Owner: TBD
  - Add rate limiting (slowapi)
  - Implement request caching
  - Better error messages and error codes

### Medium-Term Goals (Next Quarter)

- [ ] **Financial Health Scoring**
  - AI-powered financial health assessment
  - Spending pattern analysis
  - Personalized recommendations
  - Budget optimization suggestions

- [ ] **Enhanced AI Capabilities**
  - Natural language transaction queries
  - Automatic transaction categorization via AI
  - Financial advice chatbot improvements
  - Receipt parsing and auto-entry

- [ ] **Security Enhancements**
  - Email verification on registration
  - Two-factor authentication (2FA)
  - Password reset functionality
  - Session management and revocation
  - API key rotation

- [ ] **Production Readiness**
  - Dockerization (Dockerfile + docker-compose)
  - CI/CD pipeline (GitHub Actions)
  - Monitoring and alerting (Sentry, Prometheus)
  - Load testing and performance optimization
  - S3/Cloud storage integration

### Long-Term Vision

- [ ] Multi-currency support
- [ ] Bank account integration (Plaid, Yodlee)
- [ ] Investment tracking
- [ ] Tax reporting and export
- [ ] Mobile app backend support
- [ ] Multi-tenancy for teams/families
- [ ] GraphQL API option
- [ ] Real-time notifications (WebSockets)

### Completed Milestones

- [x] Core authentication system (JWT)
- [x] User management CRUD
- [x] AI agent integration (ReAct pattern)
- [x] Multi-language OCR (English + Spanish)
- [x] Transaction and Category basic CRUD
- [x] API documentation (OpenAPI)
- [x] Development environment setup (uv)
- [x] Code quality tools (Ruff, Zuban)

## Code Quality and Development Practices

### Linting and Formatting

The project uses **Ruff** for both linting and formatting:

```bash
# Check code quality
make lint-backend
# Or directly:
uv run zuban check   # Architecture checks
uv run ruff check .  # Linting

# Auto-format code
make format-backend
# Or directly:
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

**Ruff Configuration** (`.ruff.toml`):
- Line length: 88 characters (Black-compatible)
- Target Python version: 3.13
- Enabled rules: pycodestyle, pyflakes, isort
- Disabled rules: None enforced yet

### Project Structure Best Practices

```
backend/
├── app/
│   ├── api/              # API layer (routers, endpoints)
│   ├── services/         # Business logic
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas (DTOs)
│   ├── core/             # Security, LLM, utilities
│   ├── db/               # Database session management
│   ├── ocr_config/       # OCR configurations
│   └── utils/            # Shared utilities
├── tests/                # Test suite
├── docs/                 # Additional documentation
├── uploads/              # Local file storage (dev only)
└── pyproject.toml        # Dependencies and project config
```

### Database

**Current**: SQLite with SQLModel ORM
- Automatic table creation on startup
- Schema defined via SQLModel classes
- Type-safe queries with SQLModel

**Migration Path**:
```python
# app/db/session.py - Easy to switch databases
DATABASE_URL = "postgresql://user:pass@localhost/finwise"  # Change here
```

### Technical Decisions and Rationale

1. **FastAPI**: Chosen for async support, automatic OpenAPI docs, and modern Python features
2. **SQLModel**: Combines SQLAlchemy + Pydantic for type safety across layers
3. **Pydantic AI**: Type-safe AI framework with tool calling and validation
4. **uv**: Fast, reliable Python package manager (Rust-based)
5. **Argon2**: Industry-standard password hashing (PHC winner)
6. **JWT**: Stateless authentication, easy to scale horizontally
7. **Tesseract**: Mature, accurate OCR with multi-language support

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors or Module Not Found

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in the backend directory
cd backend

# Reinstall dependencies
uv sync

# Run with uv prefix
uv run fastapi dev app/main.py
```

#### 2. Tesseract Not Found

**Problem**: `TesseractNotFoundError` or OCR endpoints failing

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa

# Verify installation
tesseract --version
tesseract --list-langs  # Should show 'eng' and 'spa'

# If installed but not found, set path in code or environment
export TESSERACT_CMD=/usr/bin/tesseract
```

#### 3. Database Locked Errors

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
- SQLite doesn't handle concurrent writes well
- Use PostgreSQL for production
- For development, ensure only one server instance is running
- Delete `database.db` and restart (only if safe to reset)

#### 4. JWT Token Errors

**Problem**: `Could not validate credentials` or `Invalid token`

**Solution**:
```bash
# Ensure SECRET_KEY is set and consistent
echo $SECRET_KEY  # Should be 32+ characters

# Don't change SECRET_KEY after issuing tokens
# If changed, all users need to re-login

# Verify token expiration time
# Default is 30 minutes (ACCESS_TOKEN_EXPIRE_MINUTES)
```

#### 5. OpenRouter API Errors

**Problem**: `401 Unauthorized` or `API key invalid`

**Solution**:
```bash
# Verify API key format (should start with sk-or-v1-)
echo $OPENAI_API_KEY

# Check API key is valid at https://openrouter.ai/keys
# Ensure sufficient credits in OpenRouter account
# Check model name is correct in MODELS env var
```

#### 6. File Upload Errors

**Problem**: `413 Request Entity Too Large` or file upload fails

**Solution**:
```python
# Increase max file size in FastAPI (app/main.py)
from fastapi import FastAPI
app = FastAPI()
app.add_middleware(
    ...,
    max_upload_size=10 * 1024 * 1024  # 10MB
)
```

#### 7. CORS Errors (Frontend Integration)

**Problem**: Browser blocks API requests with CORS error

**Solution**:
```python
# Configure CORS in app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 8. Slow OCR Performance

**Problem**: OCR takes too long or times out

**Solutions**:
- Use smaller images (resize before upload)
- Preprocess images to improve quality
- Use `extract-text-intelligent` endpoint (has optimizations)
- Consider limiting to specific document types
- Reduce DPI in OCR config if accuracy allows

### Known Issues and Limitations

#### Current Limitations

1. **SQLite Concurrency**
   - Limited concurrent write operations
   - Not suitable for production with multiple users
   - **Workaround**: Migrate to PostgreSQL for production

2. **File Storage**
   - Files stored locally by default
   - No automatic cleanup of old files
   - **Workaround**: Implement S3 storage for production

3. **No Email Verification**
   - User registration doesn't verify email addresses
   - **Status**: Planned feature

4. **Limited Error Messages**
   - Some errors return generic messages
   - **Status**: Improving error handling incrementally

5. **No Rate Limiting**
   - API can be abused without rate limits
   - **Status**: Should implement before public deployment

6. **Session Management**
   - No session revocation mechanism
   - **Status**: Planned improvement

7. **Incomplete Features**
   - Reports and Notifications endpoints exist but have no implementation
   - **Status**: See [Roadmap](#roadmap)

### Debug Mode

Enable detailed logging for troubleshooting:

```python
# In app/main.py or via environment
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set via environment variable
export LOG_LEVEL=DEBUG
```

### Getting Help

If you encounter issues not covered here:

1. Check existing [GitHub Issues](https://github.com/yeferson59/FinWise-AI/issues)
2. Review API documentation at `/docs`
3. Check logs: `uv run fastapi dev app/main.py` (shows detailed errors)
4. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version)
   - Relevant configuration (redact secrets)

## Contributing

When contributing to this repository, please follow these guidelines:

### Code Contribution Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/FinWise-AI.git
   cd FinWise-AI/backend
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   uv sync
   cp .env.example .env  # Configure your environment
   ```

4. **Make Changes**
   - Follow existing architecture patterns
   - Write tests for new features
   - Update documentation as needed

5. **Code Quality Checks**
   ```bash
   make lint-backend       # Check code quality
   make format-backend     # Format code
   make run-test-backend   # Run tests
   ```

6. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Link to related issue (if applicable)
   - Describe changes and rationale
   - Ensure all CI checks pass

### Code Standards

1. **Architecture Patterns**
   - Follow clean architecture (API → Service → Model)
   - Keep business logic in `services/`
   - Keep routing logic thin in `api/v1/endpoints/`

2. **Feature Alignment**
   - New features should align with [Issue #1 Phase Requirements](https://github.com/yeferson59/FinWise-AI/issues/1)
   - Discuss major changes in issues before implementing

3. **Code Formatting**
   - All code must be formatted with Ruff
   - Run `make format-backend` before committing
   - Line length: 88 characters

4. **API Conventions**
   - Follow RESTful principles
   - Use proper HTTP methods and status codes
   - Version all endpoints under `/api/v1/`
   - Document with docstrings and OpenAPI schemas

5. **Testing Requirements**
   - Write tests for new features
   - Maintain or improve test coverage
   - All tests must pass before merging

6. **Documentation**
   - Update README for major changes
   - Document new API endpoints
   - Add docstrings to functions/classes
   - Update examples in `docs/` if needed

### Commit Message Convention

Use conventional commits format:

```
feat: add user profile endpoint
fix: resolve JWT token expiration bug
docs: update installation instructions
test: add tests for transaction service
refactor: simplify authentication logic
chore: update dependencies
```

### Review Process

- All PRs require review before merging
- Address review feedback promptly
- Keep PRs focused and reasonably sized
- Link to related issues/discussions

### Questions?

- Open an issue for bugs or feature requests
- Tag `@yeferson59` or `@Windhoek-dev` for maintainer input

## Additional Resources

### Documentation Files

- **[Multi-Language OCR Guide](docs/MULTILANG_OCR.md)** - Comprehensive OCR documentation
- **[API Examples](docs/API_EXAMPLES.md)** - Code examples for API usage
- **[OCR Improvements](MEJORAS_OCR.md)** - Technical OCR improvements (Spanish)
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Development progress summary

### External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [OpenRouter API](https://openrouter.ai/docs)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [uv Package Manager](https://docs.astral.sh/uv/)

### Project Links

- **GitHub Repository**: https://github.com/yeferson59/FinWise-AI
- **Issue Tracker**: https://github.com/yeferson59/FinWise-AI/issues
- **Phase Requirements**: [Issue #1](https://github.com/yeferson59/FinWise-AI/issues/1)

---

## Quick Reference

### Most Common Commands

```bash
# Development
make run-backend              # Start dev server
make lint-backend             # Check code quality
make format-backend           # Format code
make run-test-backend         # Run tests

# Dependencies
make sync-backend                        # Install dependencies
make add-backend-deps DEPS="package"     # Add dependency
make add-backend-dev-deps DEPS="pytest"  # Add dev dependency

# Cleanup
make clean-backend            # Remove cache files
```

### Environment Variables Quick Reference

```env
# Required
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-api-key
DATABASE_URL=sqlite:///database.db

# Optional
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3
```

### API Quick Test

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'
```

---

**Last Updated**: 2024-10  
**Version**: 0.1.0  
**Maintainers**: @yeferson59, @Windhoek-dev
