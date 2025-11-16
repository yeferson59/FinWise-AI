# FinWise-AI Backend

Backend moderno y robusto para la gestión financiera personal, construido con FastAPI, OCR multilenguaje avanzado y agentes IA. Proporciona APIs REST para usuarios, transacciones, categorías, OCR, reportes y asistentes inteligentes.

## 📋 Resumen

- **Framework:** FastAPI + SQLModel + Pydantic AI
- **OCR:** Tesseract, EasyOCR, PaddleOCR, DocTR
- **Agentes IA:** OpenAI/OpenRouter, ReAct, tool-calling
- **Base de datos:** SQLite (dev), PostgreSQL (prod recomendado)
- **Despliegue:** Docker, Makefile, uv
- **Documentación:** Toda la documentación técnica, reportes y explicaciones se encuentra en la carpeta `docs/`.

## 🚀 Estado Actual

**Versión:** 0.2.x  
**Última actualización:** Noviembre 16, 2025  
**Estado:** Núcleo estable, mejoras avanzadas en OCR y agentes IA en progreso

### Funcionalidades Completadas
- Gestión de usuarios y autenticación (JWT, Argon2id)
- Asistente virtual IA (OpenAI/OpenRouter, ReAct, tool-calling)
- OCR multilenguaje (inglés, español, recibos, facturas, formularios)
- Gestión de transacciones (CRUD, filtros avanzados, estados)
- Gestión de categorías (globales y personalizadas, integración con transacciones)
- Despliegue con Docker y Docker Compose
- Documentación técnica y ejemplos de API

### Mejoras en Progreso
- Filtros y reportes avanzados de transacciones
- Categorización automática con IA
- Generación de reportes PDF
- Sistema de notificaciones y recordatorios
- Optimización y mejoras en OCR (ver docs/)

### Funcionalidades Planeadas
- Análisis de salud financiera
- Integración bancaria y multi-moneda
- Seguimiento de inversiones
- Insights y recomendaciones inteligentes

## 🏗️ Arquitectura y Estructura

```
backend/
├── app/
│   ├── api/              # Endpoints REST (versionados)
│   ├── services/         # Lógica de negocio (OCR, agentes, reportes, etc.)
│   ├── models/           # Modelos SQLModel
│   ├── schemas/          # Esquemas Pydantic
│   ├── core/             # Seguridad, LLM, utilidades
│   ├── db/               # Sesión y conexión BD
│   ├── ocr_config/       # Configuración avanzada de OCR
│   └── utils/            # Utilidades compartidas
├── docs/                 # Documentación técnica, reportes y explicaciones
├── examples/             # Ejemplos de uso
├── tests/                # Pruebas unitarias e integración
├── uploads/              # Almacenamiento local (dev)
├── Dockerfile, docker-compose.yml
├── Makefile, requirements.txt, pyproject.toml
```

## 📚 Documentación
Toda la documentación técnica, reportes, changelogs y explicaciones detalladas se encuentra en la carpeta `docs/`.

---
**Estado del Backend:** Núcleo estable, mejoras avanzadas en progreso  
**Última actualización:** Noviembre 16, 2025  
**Mantenedores:** @yeferson59, @Windhoek-dev
