# Configuración de Variables de Entorno para FinWise-AI Backend

Este documento describe todas las variables de entorno necesarias para ejecutar el backend de FinWise-AI con Docker.

## 🚀 Inicio Rápido

Crea un archivo `.env` en el directorio `backend/` con el siguiente contenido:

```bash
# =============================================================================
# VARIABLES REQUERIDAS (OBLIGATORIAS)
# =============================================================================

# Clave secreta para JWT (mínimo 32 caracteres)
# Genera una con: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=tu-clave-super-secreta-de-minimo-32-caracteres-aqui

# API Key de OpenRouter o OpenAI para funciones de IA
# Obtén una en: https://openrouter.ai/keys o https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-or-v1-tu-api-key-aqui

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================================================

# Para SQLite (desarrollo/testing) - USA 4 BARRAS PARA DOCKER
DATABASE_URL=sqlite:////app/data/database.db

# Para PostgreSQL (producción recomendada) - Descomenta la siguiente línea
# DATABASE_URL=postgresql://finwise:password@postgres:5432/finwise

# =============================================================================
# VARIABLES OPCIONALES
# =============================================================================

# Configuración de la Aplicación
APP_NAME=FinWise API
PORT=8000
ENVIRONMENT=production
VERSION=1.0.0
PREFIX_API=/api/v1

# Configuración de Seguridad y Autenticación
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de IA/LLM
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3

# Almacenamiento de Archivos
FILE_STORAGE_TYPE=local
LOCAL_STORAGE_PATH=uploads

# Configuración de Cachés (YA CONFIGURADAS EN DOCKERFILE)
# Estas variables están preconfiguradas en el Dockerfile
# Solo necesitas modificarlas si quieres cambiar las rutas por defecto
NUMBA_CACHE_DIR=/tmp/numba_cache
HF_HOME=/home/appuser/.cache/huggingface
TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers
TORCH_HOME=/home/appuser/.cache/torch
XDG_CACHE_HOME=/home/appuser/.cache
HOME=/home/appuser
```

---

## 📋 Variables de Entorno Detalladas

### Variables Requeridas (OBLIGATORIAS)

| Variable | Tipo | Descripción | Ejemplo |
|----------|------|-------------|---------|
| `SECRET_KEY` | string | Clave secreta para firmar tokens JWT. Debe tener al menos 32 caracteres. | `your-super-secret-key-min-32-chars` |
| `OPENAI_API_KEY` | string | API key de OpenRouter o OpenAI para funciones de IA. | `sk-or-v1-...` o `sk-...` |
| `DATABASE_URL` | string | URL de conexión a la base de datos (SQLite o PostgreSQL). | `sqlite:////app/data/database.db` |

### Configuración de Aplicación

| Variable | Tipo | Por Defecto | Descripción |
|----------|------|-------------|-------------|
| `APP_NAME` | string | `FinWise API` | Nombre de la aplicación. |
| `PORT` | integer | `8000` | Puerto en el que el servidor escuchará. |
| `ENVIRONMENT` | string | `production` | Entorno de ejecución (development, staging, production). |
| `VERSION` | string | `1.0.0` | Versión de la API. |
| `PREFIX_API` | string | `/api/v1` | Prefijo para todas las rutas de la API. |

### Seguridad y Autenticación

| Variable | Tipo | Por Defecto | Descripción |
|----------|------|-------------|-------------|
| `ALGORITHM` | string | `HS256` | Algoritmo para firmar tokens JWT (HS256, RS256, etc.). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `30` | Tiempo de expiración de tokens de acceso en minutos. |

### Configuración de IA/LLM

| Variable | Tipo | Por Defecto | Descripción |
|----------|------|-------------|-------------|
| `MODELS` | string | `nvidia/llama-3.3-nemotron-70b-instruct` | Modelo de lenguaje a utilizar. |
| `TEMPERATURE` | float | `0.2` | Temperatura para la generación de texto (0.0-2.0). |
| `TOP_P` | float | `0.3` | Top-p sampling para la generación de texto (0.0-1.0). |

### Almacenamiento de Archivos

| Variable | Tipo | Por Defecto | Descripción |
|----------|------|-------------|-------------|
| `FILE_STORAGE_TYPE` | string | `local` | Tipo de almacenamiento: 'local' o 's3'. |
| `LOCAL_STORAGE_PATH` | string | `uploads` | Ruta local para almacenar archivos subidos. |

### Configuración de Cachés (Preconfiguradas)

Estas variables están preconfiguradas en el Dockerfile y generalmente no necesitas modificarlas:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `NUMBA_CACHE_DIR` | `/tmp/numba_cache` | Directorio para caché de compilación JIT de Numba. |
| `HF_HOME` | `/home/appuser/.cache/huggingface` | Directorio raíz para modelos de Hugging Face. |
| `TRANSFORMERS_CACHE` | `/home/appuser/.cache/huggingface/transformers` | Caché de modelos Transformers. |
| `TORCH_HOME` | `/home/appuser/.cache/torch` | Caché de modelos PyTorch. |
| `XDG_CACHE_HOME` | `/home/appuser/.cache` | Directorio de caché estándar Linux. |
| `HOME` | `/home/appuser` | Directorio home del usuario. |

---

## 🔐 Generación de SECRET_KEY

### Opción 1: Python
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Opción 2: OpenSSL
```bash
openssl rand -base64 32
```

### Opción 3: Online (no recomendado para producción)
```bash
# Usa un generador online solo para desarrollo
# Para producción, siempre genera localmente
```

---

## 🗄️ Configuración de Base de Datos

### SQLite (Desarrollo/Testing)

**⚠️ IMPORTANTE**: Para Docker, debes usar 4 barras en la URL de SQLite:

```bash
# ✅ CORRECTO para Docker (ruta absoluta con 4 barras)
DATABASE_URL=sqlite:////app/data/database.db

# ❌ INCORRECTO para Docker (ruta relativa con 3 barras)
DATABASE_URL=sqlite:///database.db
```

**Ventajas de SQLite:**
- Sin configuración adicional
- Ideal para desarrollo y testing
- Archivo único y portátil

**Desventajas de SQLite:**
- No recomendado para producción con alta concurrencia
- Rendimiento limitado en escrituras concurrentes
- Sin replicación nativa

### PostgreSQL (Producción Recomendada)

```bash
DATABASE_URL=postgresql://username:password@hostname:5432/database_name

# Ejemplo con Docker Compose:
DATABASE_URL=postgresql://finwise:changeme@postgres:5432/finwise

# Ejemplo con servicio externo:
DATABASE_URL=postgresql://user:pass@db.example.com:5432/finwise
```

**Ventajas de PostgreSQL:**
- ✅ Alto rendimiento con concurrencia
- ✅ Replicación y alta disponibilidad
- ✅ Funciones avanzadas (JSON, full-text search, etc.)
- ✅ Recomendado para producción

**Para usar PostgreSQL con Docker Compose:**
1. Descomenta el servicio `postgres` en `docker-compose.yml`
2. Actualiza `DATABASE_URL` en tu archivo `.env`
3. Configura `DB_PASSWORD` con una contraseña segura

---

## 🤖 Configuración de OpenAI/OpenRouter

### OpenRouter (Recomendado)

OpenRouter permite acceder a múltiples modelos LLM con una sola API key:

1. Regístrate en [https://openrouter.ai](https://openrouter.ai)
2. Obtén tu API key en [https://openrouter.ai/keys](https://openrouter.ai/keys)
3. Configura:
   ```bash
   OPENAI_API_KEY=sk-or-v1-tu-api-key-aqui
   MODELS=nvidia/llama-3.3-nemotron-70b-instruct
   ```

**Modelos recomendados en OpenRouter:**
- `nvidia/llama-3.3-nemotron-70b-instruct` (recomendado)
- `anthropic/claude-3.5-sonnet`
- `google/gemini-pro-1.5`
- `openai/gpt-4o`

### OpenAI Direct

Si prefieres usar OpenAI directamente:

1. Obtén tu API key en [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Configura:
   ```bash
   OPENAI_API_KEY=sk-tu-api-key-aqui
   MODELS=gpt-4o
   ```

---

## 🚀 Ejemplo de Archivo .env Completo

### Para Desarrollo (SQLite)

```bash
# Requeridas
SECRET_KEY=dev-secret-key-for-testing-only-change-in-production
OPENAI_API_KEY=sk-or-v1-your-api-key-here
DATABASE_URL=sqlite:////app/data/database.db

# Opcionales
APP_NAME=FinWise API Dev
PORT=8000
ENVIRONMENT=development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3
FILE_STORAGE_TYPE=local
LOCAL_STORAGE_PATH=uploads
```

### Para Producción (PostgreSQL)

```bash
# Requeridas
SECRET_KEY=your-super-secure-production-secret-key-32-chars-minimum
OPENAI_API_KEY=sk-or-v1-your-production-api-key-here
DATABASE_URL=postgresql://finwise:secure_password_here@postgres:5432/finwise

# Opcionales
APP_NAME=FinWise API
PORT=8000
ENVIRONMENT=production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MODELS=nvidia/llama-3.3-nemotron-70b-instruct
TEMPERATURE=0.2
TOP_P=0.3
FILE_STORAGE_TYPE=s3
# AWS_ACCESS_KEY_ID=your-aws-access-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key
# AWS_BUCKET_NAME=finwise-uploads
# AWS_REGION=us-east-1
```

---

## 🔍 Verificación de Configuración

### Verificar que todas las variables están configuradas:

```bash
# Con docker-compose
docker-compose config

# En el contenedor en ejecución
docker exec finwise-backend env
```

### Verificar variables específicas:

```bash
# Verificar SECRET_KEY
docker exec finwise-backend env | grep SECRET_KEY

# Verificar DATABASE_URL
docker exec finwise-backend env | grep DATABASE_URL

# Verificar cachés
docker exec finwise-backend env | grep -E "(NUMBA|HF_HOME|TORCH_HOME)"
```

---

## ⚠️ Seguridad en Producción

### ✅ HACER:
- ✅ Generar SECRET_KEY fuerte y único
- ✅ Usar PostgreSQL en lugar de SQLite
- ✅ Almacenar secrets en un gestor de secrets (AWS Secrets Manager, HashiCorp Vault, etc.)
- ✅ Usar variables de entorno, nunca hardcodear secrets
- ✅ Rotar API keys regularmente
- ✅ Usar HTTPS con certificados válidos
- ✅ Configurar backups automáticos de la base de datos

### ❌ NO HACER:
- ❌ Commitear archivos `.env` al repositorio
- ❌ Usar SECRET_KEY de ejemplo en producción
- ❌ Compartir API keys públicamente
- ❌ Usar SQLite en producción con alto tráfico
- ❌ Usar contraseñas por defecto (`changeme`, `password`, etc.)
- ❌ Exponer el puerto de la base de datos públicamente

---

## 📚 Referencias

- [FastAPI Settings Management](https://fastapi.tiangolo.com/advanced/settings/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [12-Factor App - Config](https://12factor.net/config)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [OpenRouter Documentation](https://openrouter.ai/docs)

---

## 🆘 Solución de Problemas

### Error: "SECRET_KEY environment variable is required"
**Solución**: Asegúrate de que el archivo `.env` existe y contiene `SECRET_KEY=...`

### Error: "OPENAI_API_KEY environment variable is required"
**Solución**: Configura `OPENAI_API_KEY` con una API key válida de OpenRouter o OpenAI.

### Error: "unable to open database file"
**Solución**:
1. Verifica que `DATABASE_URL` use 4 barras: `sqlite:////app/data/database.db`
2. Asegúrate de que el volumen `finwise-data:/app/data` está configurado en `docker-compose.yml`

### La base de datos se pierde al reiniciar el contenedor
**Solución**: Verifica que los volúmenes estén correctamente configurados:
```yaml
volumes:
  - finwise-data:/app/data
```

### Los modelos de IA se descargan cada vez que reinicio
**Solución**: Descomenta los volúmenes de caché en `docker-compose.yml`:
```yaml
volumes:
  - huggingface-cache:/home/appuser/.cache/huggingface
  - torch-cache:/home/appuser/.cache/torch
```

---

**Última actualización**: 2024
**Versión**: 1.0.0
