# FinWise-AI

A comprehensive personal finance management application with AI-powered assistance. FinWise-AI combines intelligent financial insights with user-friendly mobile and web interfaces to help users track expenses, manage budgets, and make informed financial decisions.

## 📋 Project Overview

FinWise-AI is a full-stack personal finance application consisting of:

- **Backend API**: FastAPI-based REST API with AI capabilities
- **Frontend**: Cross-platform mobile app built with React Native and Expo
- **AI Integration**: Intelligent financial assistant powered by large language models
- **OCR Processing**: Multi-language document text extraction for receipts and invoices

## 🚀 Project Status

**Overall Status**: Active Development  
**Last Updated**: October 27, 2024

### Backend Status

**Technology Stack**: FastAPI, Python 3.13+, SQLModel, Pydantic AI  
**Current Version**: 0.1.0  
**Status**: Core features stable, advanced features in progress

#### ✅ Completed Features

- **User Management & Authentication**
  - JWT-based authentication with Argon2id password hashing
  - Full user CRUD operations with pagination
  - Secure session management

- **AI Virtual Assistant**
  - OpenAI/OpenRouter integration with ReAct agent pattern
  - Tool-calling capabilities for database queries
  - Support for multiple AI models (NVIDIA Llama 3.3 Nemotron by default)

- **Multi-Language OCR**
  - English and Spanish document text extraction
  - Support for receipts, invoices, forms, and other financial documents
  - Intelligent extraction with fallback strategies and confidence scoring

- **Transaction Management**
  - Full CRUD operations for financial transactions
  - Category and source tracking
  - Transaction state management (pending, completed, etc.)

- **Category Management**
  - 56 default global categories organized by type (Income, Expenses, Savings, Investments, Debt, Other)
  - Custom user-specific category creation
  - Idempotent category initialization (safe to run multiple times)
  - Support for both global (default) and user-specific categories
  - Full CRUD operations for category management
  - Integration with transaction system

- **Docker Deployment**
  - Production-ready Dockerfile with multi-stage builds
  - Docker Compose configuration
  - Comprehensive deployment documentation

#### 🚧 In Progress

- Advanced transaction filtering and reporting
- Automated AI-based expense categorization
- PDF report generation
- Notifications and reminders system

#### 📋 Planned Features

- Financial health assessment and scoring
- Spending pattern analysis
- Bank account integration
- Investment tracking
- Multi-currency support

For detailed backend documentation, see [Backend README](backend/README.md).

### Frontend Status

**Technology Stack**: React Native, Expo, TypeScript  
**Current Version**: 1.0.0  
**Status**: Initial development phase

#### ✅ Completed Features

- Basic Expo project structure with file-based routing
- Cross-platform support (iOS, Android, Web)
- Tab-based navigation setup

#### 🚧 In Progress

- UI/UX design and component library
- API integration with backend services
- Authentication flow implementation
- Transaction management screens

#### 📋 Planned Features

- Dashboard with financial overview
- Transaction entry and editing
- Receipt scanning and OCR integration
- Budget tracking and alerts
- Financial insights and recommendations
- Multi-language support

For detailed frontend documentation, see [Frontend README](frontend/README.md).

## 🏗️ Architecture

```
FinWise-AI/
├── backend/              # FastAPI REST API
│   ├── app/
│   │   ├── api/         # API endpoints (versioned)
│   │   ├── services/    # Business logic
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── core/        # Security, LLM, utilities
│   │   └── db/          # Database session management
│   ├── tests/           # Backend tests
│   └── docs/            # Additional documentation
│
├── frontend/            # React Native/Expo mobile app
│   ├── app/            # Application screens (file-based routing)
│   ├── components/     # Reusable UI components
│   ├── assets/         # Images, fonts, icons
│   └── hooks/          # Custom React hooks
│
└── Makefile            # Development commands
```

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.13+, uv package manager, Tesseract OCR
- **Frontend**: Node.js 18+, npm or yarn
- **Optional**: Docker and Docker Compose for containerized deployment

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
uv run fastapi dev app/main.py
```

The API will be available at http://localhost:8000 with interactive documentation at http://localhost:8000/docs.

For detailed backend setup, see [Backend README](backend/README.md).

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Or run on specific platform
npm run web      # Web browser
npm run android  # Android emulator
npm run ios      # iOS simulator
```

For detailed frontend setup, see [Frontend README](frontend/README.md).

### Using Makefile (Recommended)

The project includes convenient Makefile commands:

```bash
# Backend
make run-backend              # Start backend dev server
make sync-backend             # Install backend dependencies
make lint-backend             # Lint backend code
make format-backend           # Format backend code
make run-test-backend         # Run backend tests

# Frontend
make run-frontend             # Start frontend dev server
```

## 🐳 Docker Deployment

```bash
# Backend with Docker
cd backend
docker build -t finwise-backend .
docker run -p 8000:8000 finwise-backend

# Or use Docker Compose (recommended)
docker-compose up -d
```

See [Backend Docker Documentation](backend/DOCKER.md) for complete deployment instructions.

## 📚 Documentation

### Backend Documentation

- [Backend README](backend/README.md) - Complete backend documentation
- [API Examples](backend/docs/API_EXAMPLES.md) - cURL, Python, JavaScript examples
- [Multi-Language OCR Guide](backend/docs/MULTILANG_OCR.md) - OCR usage and configuration
- [File Storage Configuration](backend/docs/FILE_STORAGE.md) - Local and S3 storage setup
- [Docker Deployment Guide](backend/DOCKER.md) - Container deployment instructions

### Frontend Documentation

- [Frontend README](frontend/README.md) - Frontend setup and development

## 🧪 Testing

### Backend Tests

```bash
cd backend
make run-test-backend         # Run all tests
make run-test-backend-info    # Run with verbose output
```

### Frontend Tests

```bash
cd frontend
npm run lint                  # Run linter
```

## 🛠️ Development Workflow

1. **Code Quality**: The project uses Ruff for Python linting/formatting and ESLint for JavaScript/TypeScript
2. **Testing**: Write tests for new features (pytest for backend)
3. **Documentation**: Update relevant documentation when adding features
4. **Commits**: Use conventional commit messages (feat:, fix:, docs:, etc.)

## 🔑 Environment Configuration

### Backend Environment Variables

Key configuration variables (see backend/.env.example):

```env
# Required
SECRET_KEY=your-secret-key-min-32-chars
OPENAI_API_KEY=your-openrouter-api-key
DATABASE_URL=sqlite:///database.db

# Optional
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3
FILE_STORAGE_TYPE=local
```

### Frontend Environment Variables

Frontend configuration (if needed) should be placed in frontend/.env.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes following the project's code style
4. Write tests for new features
5. Update documentation as needed
6. Run linters and tests before committing
7. Create a pull request with a clear description

### Code Standards

- **Backend**: Follow PEP 8, use Ruff for formatting (88 char line length)
- **Frontend**: Follow React/TypeScript best practices, use ESLint
- **Commits**: Use conventional commit format
- **Documentation**: Keep documentation up-to-date with code changes

## 📖 Resources

### Project Links

- **Repository**: https://github.com/yeferson59/FinWise-AI
- **Issue Tracker**: https://github.com/yeferson59/FinWise-AI/issues
- **Phase Requirements**: [Issue #1](https://github.com/yeferson59/FinWise-AI/issues/1)

### Technology Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [React Native Documentation](https://reactnative.dev/)

## 📄 License

This project's license information is not yet specified. Please contact the maintainers for details.

## 👥 Maintainers

- @yeferson59
- @Windhoek-dev

## 🙏 Acknowledgments

Built with:
- FastAPI for the backend framework
- Pydantic AI for AI integration
- Tesseract OCR for document processing
- Expo and React Native for cross-platform mobile development
- OpenRouter for AI model access

---

**Project Status**: Active Development  
**Last Updated**: October 27, 2024  
**Version**: Backend 0.1.0, Frontend 1.0.0
