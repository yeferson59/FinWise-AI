# FinWise-AI

Una aplicación integral de gestión financiera personal con asistencia impulsada por IA. FinWise-AI combina análisis inteligentes, OCR multilenguaje y una interfaz web y móvil para ayudar a los usuarios a gestionar sus finanzas de forma eficiente.

## 📋 Resumen del Proyecto

FinWise-AI es una solución full-stack compuesta por:

- **Backend API:** API REST con FastAPI, OCR avanzado y agente IA
- **Frontend Mobile:** App móvil multiplataforma con React Native y Expo
- **Frontend Web:** Aplicación web con React y Vite
- **Shared:** Código compartido para integración frontend-backend

## 🚀 Estado Actual del Proyecto

**Estado General:** Desarrollo activo  
**Última actualización:** Noviembre 30, 2025

### Backend

**Stack:** FastAPI, Python 3.13+, SQLModel, Pydantic AI, Tesseract OCR  
**Versión:** 0.2.x  
**Estado:** Núcleo estable, funcionalidades avanzadas implementadas
**Tests:** 218 tests unitarios e integración

#### ✅ Funcionalidades Completadas
- Gestión de usuarios y autenticación (JWT, Argon2id)
- Asistente virtual IA (OpenAI/OpenRouter, ReAct agent, tool-calling)
- OCR multilenguaje (inglés, español, recibos, facturas, formularios)
- Gestión de transacciones (CRUD, categorías, estados, filtros avanzados)
- Gestión de categorías (globales y personalizadas, integración con transacciones)
- Gestión de fuentes de ingresos/gastos (sources)
- Sistema de notificaciones y recordatorios
- Generación de reportes financieros con resúmenes IA
- Análisis de salud financiera con IA
- Procesamiento de archivos (imágenes, PDFs, audio)
- Almacenamiento de archivos (local y S3)
- Despliegue con Docker y Docker Compose
- Documentación técnica y ejemplos de API
- Suite completa de tests (218 tests)

#### 🚧 Mejoras en Progreso
- Generación de reportes PDF
- Optimización y mejoras en OCR
- Integración bancaria

#### 📋 Funcionalidades Planeadas
- Multi-moneda
- Seguimiento de inversiones
- Presupuestos con alertas automáticas

### Frontend Mobile

**Stack:** React Native + Expo  
**Estado:** Funcionalidades principales implementadas

#### ✅ Funcionalidades Completadas
- Estructura de proyecto Expo con navegación
- Autenticación (login/registro)
- Dashboard principal (home)
- Gestión de transacciones (lista, detalle, crear)
- Escaneo OCR de recibos y documentos
- Grabación de audio para transacciones
- Asistente IA conversacional
- Sistema de notificaciones
- Generación y visualización de reportes
- Gestión de categorías
- Pantalla de presupuestos
- Configuración y perfil de usuario
- Soporte multiplataforma (iOS, Android, Web)

#### 🚧 Mejoras en Progreso
- Mejoras UI/UX
- Gráficos y visualizaciones de datos

#### 📋 Funcionalidades Planeadas
- Soporte offline
- Widgets para iOS/Android
- Soporte multilenguaje (i18n)

### Frontend Web

**Stack:** React + Vite  
**Estado:** Estructura básica

### Shared

**Stack:** TypeScript, Axios, Zod  
**Estado:** Completo

#### ✅ Funcionalidades Completadas
- Cliente API tipado con validación Zod
- Manejo de errores y reintentos automáticos
- Autenticación (login, register, logout)
- Gestión de transacciones
- Gestión de categorías y fuentes
- Procesamiento de texto y archivos (OCR)
- Agente IA conversacional
- Análisis de salud financiera
- Notificaciones y recordatorios
- Reportes financieros

## 🏗️ Estructura del Proyecto

```
FinWise-AI/
├── backend/              # API REST FastAPI
│   ├── app/
│   │   ├── api/v1/       # Endpoints REST
│   │   ├── core/         # Lógica de negocio, agentes IA
│   │   ├── models/       # Modelos SQLModel
│   │   ├── schemas/      # Schemas Pydantic
│   │   └── services/     # Servicios (OCR, auth, etc.)
│   ├── tests/            # 218 tests
│   └── docs/             # Documentación técnica
├── frontend/
│   ├── mobile/           # App móvil Expo/React Native
│   │   ├── app/          # 19 pantallas
│   │   ├── components/   # Componentes reutilizables
│   │   ├── contexts/     # Context providers
│   │   ├── hooks/        # Custom hooks
│   │   └── services/     # Servicios cliente
│   └── web/              # App web React/Vite
├── shared/               # Código compartido (API client)
└── Makefile              # Comandos de desarrollo
```

## 🚀 Guía Rápida de Inicio

### Requisitos
- **Backend:** Python 3.13+, uv, Tesseract OCR
- **Frontend:** Node.js 18+, npm o yarn
- **Opcional:** Docker y Docker Compose

### Backend
```bash
cd backend
uv sync
cp .env.example .env  # Configura tus variables
uv run fastapi dev app/main.py
```
API disponible en http://localhost:8000 (docs en /docs)

### Frontend Mobile
```bash
cd frontend/mobile
npm install
npx expo start
```

### Frontend Web
```bash
cd frontend/web
npm install
npm run dev
```

### Makefile (Recomendado)
```bash
make run-backend        # Inicia backend
make run-frontend       # Inicia frontend web
make sync-backend       # Instala dependencias backend
make lint-backend       # Ejecuta linter backend
make run-test-backend   # Ejecuta tests backend
```

### Docker
```bash
cd backend
docker build -t finwise-backend .
docker run -p 8000:8000 finwise-backend
# O usa Docker Compose
cd ..
docker-compose up -d
```

## 📚 Documentación
- **Backend:** Documentación técnica y ejemplos en `backend/docs/`
- **Frontend:** README en cada subproyecto
- **Docker:** Guía en `backend/DOCKER.md`

## 🧪 Testing
- **Backend:** 218 tests en `backend/tests/` (pytest)
  - Tests de API endpoints
  - Tests de servicios
  - Tests de OCR y procesamiento
  - Tests de agentes IA
- **Frontend:** Linter (`npm run lint` en mobile)

## 🛠️ Flujo de Desarrollo
1. Linting: Ruff + Mypy (Python), ESLint (JS/TS)
2. Tests: pytest (backend)
3. Documentación: Mantener docs actualizadas
4. Commits: Formato convencional

## 🔑 Configuración de Entorno
- Variables en `backend/.env.example` y `frontend/mobile/.env` si aplica

## 🤝 Contribuciones
¡Bienvenido a contribuir! Sigue las buenas prácticas de código, tests y documentación.

## 📖 Recursos
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Pydantic AI](https://ai.pydantic.dev/)
- [Expo](https://docs.expo.dev/)
- [React Native](https://reactnative.dev/)
- [Vite](https://vitejs.dev/)

## 👥 Mantenedores
- @yeferson59
- @Windhoek-dev

---
**Estado del Proyecto:** Desarrollo activo  
**Última actualización:** Noviembre 30, 2025
