# FinWise-AI Backend

A FastAPI-based backend for a personal finance management application with AI-powered assistance. This backend provides RESTful APIs for user management, authentication, and AI-driven financial insights.

## Current Status

This backend is under active development. The core infrastructure and authentication system are operational, while transaction management, reporting, and notification features are in the planning phase.

### Project Requirements

Based on [Issue #1 - Phase Requirements](https://github.com/yeferson59/FinWise-AI/issues/1), the application aims to provide the following features for end users:

#### ✅ Completed Requirements

1. **Registrar usuario** (User Registration)
   - ✅ User registration with email and password
   - ✅ Secure password hashing using Argon2
   - ✅ User authentication with JWT tokens
   - ✅ Session management with token expiration
   - ✅ Login and logout endpoints
   - ✅ Full CRUD operations for user management
   - ✅ User listing with pagination support
   - ✅ Email-based user lookup

2. **Conversar con asistente virtual** (Virtual Assistant Conversation)
   - ✅ AI-powered chat agent using OpenAI/OpenRouter
   - ✅ ReAct (Reasoning + Acting) agent pattern implementation
   - ✅ Tool-based capabilities for querying database information
   - ✅ Configurable temperature and top_p parameters for response generation
   - ✅ Database query tools (e.g., retrieve users from database)

#### 🚧 Pending Requirements

3. **Registrar transacciones** (Transaction Registration)
   - *Status:* Endpoint structure created, implementation pending
   - *Planned:* CRUD operations for income and expense transactions

4. **Clasificar Gastos/Ingresos** (Expense/Income Classification)
   - *Status:* Model structure created, implementation pending
   - *Planned:* Category management and automatic classification

5. **Generar Reportes** (Report Generation)
   - *Status:* Endpoint structure created, implementation pending
   - *Planned:* Financial summaries, PDF exports, data visualization

6. **Generar notificaciones/recordatorios** (Notifications/Reminders)
   - *Status:* Endpoint structure created, implementation pending
   - *Planned:* Budget alerts, bill reminders, spending notifications

7. **Obtener salud financiera** (Financial Health Assessment)
   - *Status:* Not yet implemented
   - *Planned:* AI-based financial health scoring and recommendations

## Technical Stack

- **Framework:** FastAPI 0.118.3+
- **Database:** SQLite with SQLModel ORM
- **Authentication:** JWT tokens with session management
- **Password Security:** Argon2 hashing via pwdlib
- **AI/ML:** Pydantic AI with OpenAI/OpenRouter integration
- **Language:** Python 3.13+
- **Package Manager:** uv

## Architecture

The backend follows a clean architecture pattern with clear separation of concerns:

- **API Layer** (`app/api/`): REST endpoints and request/response handling
- **Services Layer** (`app/services/`): Business logic implementation
- **Models Layer** (`app/models/`): Database models using SQLModel
- **Schemas Layer** (`app/schemas/`): Pydantic models for validation
- **Core Layer** (`app/core/`): Security, LLM integration, and core utilities
- **Database Layer** (`app/db/`): Database connection and session management

## Prerequisites

- Python 3.13 or higher
- uv package manager
- OpenAI API key (for AI assistant features)

## Installation

1. Install dependencies using uv:
```bash
uv sync
```

2. Create a `.env` file in the backend directory with the following variables:
```env
OPENAI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///database.db
```

## Running the Application

Start the development server:
```bash
uv run fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Available Endpoints

#### Authentication (`/api/v1/auth`)
- `POST /login` - User login
- `POST /register` - User registration
- `POST /logout` - User logout

#### Users (`/api/v1/users`)
- `GET /` - List all users (with pagination)
- `POST /` - Create a new user
- `GET /{user_id}` - Get user by ID
- `PATCH /{user_id}` - Update user information
- `DELETE /{user_id}` - Delete a user
- `GET /email/{email}` - Get user by email

#### AI Agents (`/api/v1/agents`)
- `POST /` - Chat with basic AI agent
- `POST /react` - Chat with ReAct agent (can query database)

#### Health (`/api/v1/health`)
- `GET /` - Health check endpoint

#### Transactions (`/api/v1/transactions`)
- *Coming soon*

#### Reports (`/api/v1/reports`)
- *Coming soon*

#### Notifications (`/api/v1/notifications`)
- *Coming soon*

## Development

### Code Quality

The project uses Ruff for linting and code formatting:
```bash
uv run ruff check .
uv run ruff format .
```

### Database

The application uses SQLite for data persistence. The database is automatically created on application startup with all necessary tables.

## Technical Decisions and Limitations

1. **Database:** Currently using SQLite for simplicity. Consider migrating to PostgreSQL for production deployments with multiple concurrent users.

2. **AI Model:** Using NVIDIA's Llama 3.3 Nemotron via OpenRouter for AI capabilities. Model selection can be configured in `app/core/llm.py`.

3. **Authentication:** Session-based JWT authentication. Tokens expire after 30 minutes (configurable).

4. **Password Security:** Argon2 hashing algorithm for secure password storage.

5. **API Versioning:** All endpoints are versioned under `/api/v1/` prefix for future compatibility.

## Project Structure

```
.
├── README.md
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── endpoints
│   │       │   ├── __init__.py
│   │       │   ├── agents.py
│   │       │   ├── ai_assistant.py
│   │       │   ├── auth.py
│   │       │   ├── health.py
│   │       │   ├── notifications.py
│   │       │   ├── reports.py
│   │       │   ├── transactions.py
│   │       │   └── users.py
│   │       └── router.py
│   ├── config.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── event_handlers.py
│   │   ├── expections.py
│   │   ├── llm.py
│   │   ├── security.py
│   │   └── tasks.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── category.py
│   │   ├── notification.py
│   │   ├── report.py
│   │   ├── transaction.py
│   │   └── user.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── auth.py
│   │   ├── notification.py
│   │   ├── report.py
│   │   ├── transaction.py
│   │   └── user.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── auth.py
│   │   ├── health.py
│   │   ├── notification.py
│   │   ├── report.py
│   │   └── user.py
│   └── utils
│       ├── __init__.py
│       ├── ai_parsers.py
│       ├── db.py
│       └── pdf_generator.py
├── database.db
├── pyproject.toml
├── tests
└── uv.lock
```

## Contributing

When contributing to this repository, please ensure:

1. All code follows the existing architecture patterns
2. New features align with requirements from [Issue #1](https://github.com/yeferson59/FinWise-AI/issues/1)
3. Code is properly formatted using Ruff
4. API endpoints follow RESTful conventions
5. Changes are documented in this README

## References

- [Issue #1 - Phase Requirements](https://github.com/yeferson59/FinWise-AI/issues/1)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
