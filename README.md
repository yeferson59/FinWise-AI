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
**Última actualización:** Noviembre 16, 2025

### Backend

**Stack:** FastAPI, Python 3.13+, SQLModel, Pydantic AI, Tesseract OCR  
**Versión:** 0.2.x  
**Estado:** Núcleo estable, mejoras avanzadas en OCR y agentes IA en progreso

#### ✅ Funcionalidades Completadas
- Gestión de usuarios y autenticación (JWT, Argon2id)
- Asistente virtual IA (OpenAI/OpenRouter, ReAct agent, tool-calling)
- OCR multilenguaje (inglés, español, recibos, facturas, formularios)
- Gestión de transacciones (CRUD, categorías, estados)
- Gestión de categorías (globales y personalizadas, integración con transacciones)
- Despliegue con Docker y Docker Compose
- Documentación técnica y ejemplos de API

#### 🚧 Mejoras en Progreso
- Filtros avanzados y reportes de transacciones
- Categorización automática con IA
- Generación de reportes PDF
- Sistema de notificaciones y recordatorios
- Optimización y mejoras en OCR (ver docs/ y archivos de cambios)

#### 📋 Funcionalidades Planeadas
- Análisis de salud financiera
- Integración bancaria y multi-moneda
- Seguimiento de inversiones
- Insights y recomendaciones inteligentes

### Frontend

**Mobile:** React Native + Expo  
**Web:** React + Vite  
**Estado:** Estructura básica, desarrollo inicial de pantallas y componentes

#### ✅ Funcionalidades Completadas
- Estructura de proyecto Expo y Vite
- Navegación por pestañas (mobile)
- Soporte multiplataforma (iOS, Android, Web)

#### 🚧 Mejoras en Progreso
- Diseño UI/UX y librería de componentes
- Integración con API backend
- Flujo de autenticación
- Pantallas de gestión de transacciones

#### 📋 Funcionalidades Planeadas
- Dashboard financiero
- Escaneo de recibos y OCR
- Seguimiento de presupuestos y alertas
- Insights y recomendaciones
- Soporte multilenguaje

### Shared

- Código compartido para integración API (ej: api.js)
- Facilita la comunicación entre frontend y backend

## 🏗️ Estructura del Proyecto

```
FinWise-AI/
├── backend/              # API REST FastAPI, OCR, agentes IA, docs, tests
├── frontend/
│   ├── mobile/           # App móvil Expo/React Native
│   └── web/              # App web React/Vite
├── shared/               # Código compartido (API, utilidades)
├── Makefile              # Comandos de desarrollo
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
make run-backend      # Inicia backend
make run-frontend     # Inicia frontend web
make sync-backend     # Instala dependencias backend
make run-test-backend # Ejecuta tests backend
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
- **Backend:** Tests en `backend/tests/` (pytest)
- **Frontend:** Linter y pruebas básicas (`npm run lint` en mobile/web)

## 🛠️ Flujo de Desarrollo
1. Linting: Ruff (Python), ESLint (JS/TS)
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
**Última actualización:** Noviembre 16, 2025
