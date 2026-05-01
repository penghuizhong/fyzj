# AGENTS.md - 方圆智版 (Fangyuan AI Platform)

Multi-service AI garment pattern-making platform with FastAPI backend, Next.js frontend, and Streamlit admin.

## Architecture Overview

```
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│   Next.js Web   │  │   Casdoor    │  │ Streamlit Admin │
│   (port 3000)   │  │  (port 8000) │  │  (port 8501)    │
└────────┬────────┘  └──────┬───────┘  └────────┬────────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │   Agent API (port 8001)   │
              │  FastAPI + LangGraph      │
              └─────────────┬─────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │PostgreSQL│      │  Redis   │      │  Celery  │
   │(pgvector)│      │(3 dbs)   │      │  Worker  │
   └──────────┘      └──────────┘      └──────────┘
```

## Quick Start

```bash
# 1. Start infrastructure (PostgreSQL, Redis, Casdoor)
docker compose up -d

# 2. Copy environment templates
cp agent_api/.env.example agent_api/.env
# Edit agent_api/.env with your API keys (DEEPSEEK_API_KEY, DASHSCOPE_API_KEY)

# 3. Start services
cd agent_api && docker compose up -d   # API + Celery worker
cd streamlit_web && docker compose up -d  # Admin dashboard
cd web && pnpm install && pnpm dev     # Frontend
```

## Service Breakdown

### 1. Infrastructure (`compose.yaml`)
- **PostgreSQL** (`pgvector/pgvector:pg16`): Core database + vector store
  - Databases: `fyzj` (app), `casdoor` (auth)
  - Extension: `pgvector` for embeddings
  - Port: 5432
- **Redis**: Shared cache
  - DB 0: Business cache
  - DB 1: Agent cache + Celery broker
  - DB 2: Celery results
  - Port: 6379
- **Casdoor**: Authentication service (RS256 JWT)
  - Port: 8000

### 2. Agent API (`agent_api/`)
- **Port**: 8001
- **Stack**: FastAPI + LangGraph + LlamaIndex + Celery
- **Python**: 3.12 (managed with `uv`)
- **Entry**: `src/main.py`
- **Config**: `config.yaml` (LLM routing, category rules)
- **Key Components**:
  - `src/api/`: HTTP routes and service layer
  - `src/agents/`: LangGraph agent definitions
  - `src/core/`: Config, database, cache, rate limiting
  - `src/tasks/`: Celery background tasks
- **LLM Providers**: DeepSeek, DashScope (Qwen), OpenAI
- **Default Model**: `deepseek-v4-flash`

**Important Environment Variables**:
```bash
# Required
DEEPSEEK_API_KEY=...
DASHSCOPE_API_KEY=...
POSTGRES_PASSWORD=...

# JWT (RS256 - verification only, issued by Casdoor)
JWT_ALGORITHM=RS256
CASDOOR_JWKS_URL=http://casdoor:8000/.well-known/jwks

# Redis (strict DB isolation)
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# CORS (Next.js frontend)
CORS_ORIGINS=http://localhost:3000
```

### 3. Web Frontend (`web/`)
- **Port**: 3000
- **Stack**: Next.js 16 + React 19 + TypeScript
- **Styling**: Tailwind CSS v4 + Geist font
- **State**: Zustand
- **Auth**: Next-Auth 5 (beta) + Casdoor
- **Testing**: Vitest + React Testing Library + jsdom
- **Package Manager**: pnpm
- **Key Files**:
  - `app/page.tsx`: Main page
  - `app/layout.tsx`: Root layout with providers
  - `components/`: UI components
  - `auth.ts`: Next-Auth configuration with Casdoor
  - `vitest.config.ts`: Test config with `@` alias
  - `vitest.setup.ts`: Test setup (jest-dom matchers)

### 4. Streamlit Admin (`streamlit_web/`)
- **Port**: 8501
- **Stack**: Streamlit + pandas
- **Python**: 3.11 (managed with `uv`)
- **Entry**: `src/admin_dashboard.py`
- **Purpose**: Internal admin tools and dashboards

## Development Commands

### Python Services (uv)
```bash
# agent_api/
uv sync                              # Install dependencies
uv run pytest                        # Run tests
uv run ruff check .                  # Lint
uv run ruff check --fix .            # Fix linting
uv run mypy src/                     # Type check

# Local development (without Docker)
uv run python src/main.py

# Celery worker
uv run celery -A core.celery_app worker --loglevel=info
```

### Web Frontend (pnpm)
```bash
# web/
pnpm install
pnpm dev          # Development server
pnpm build        # Production build
pnpm lint         # ESLint
pnpm test         # Vitest run
pnpm test:watch   # Vitest watch mode
```

### Database
```bash
# Initialize (runs postgres-init/01-init-dbs.sql on first start)
docker compose up -d postgres

# Connect
psql -h localhost -U postgres -d fyzj
```

## Project Conventions

### Code Style
- **Python**: Ruff (line-length 100), target Python 3.11+
  - Import sorting enabled (`extend-select = ["I", "U"]`)
- **TypeScript/JavaScript**: ESLint (Next.js config)

### Docker Network
All services connect to an external Docker network named `network`:
```yaml
networks:
  network:
    external: true
```
Create it once: `docker network create network`

### Database Isolation
- **fyzj**: Application data + vector embeddings
- **casdoor**: Authentication data (managed by Casdoor)
- **Redis DB 0**: Reserved for business service
- **Redis DB 1**: Agent cache + rate limiting + Celery broker
- **Redis DB 2**: Celery results only

### Authentication
- **Method**: RS256 JWT (public key verification only)
- **Issuer**: Casdoor (port 8000)
- **Agent API**: Only validates tokens via JWKS endpoint, never issues them
- JWKS URL: `http://casdoor:8000/.well-known/jwks`
- Frontend: Next-Auth 5 with Casdoor provider

## Important File Locations

```
agent_api/
├── src/main.py           # FastAPI entry point
├── src/core/config.py    # Pydantic settings (reads .env + config.yaml)
├── src/api/service.py    # FastAPI app factory
├── src/api/routers/      # API route handlers
├── config.yaml           # LLM provider routing rules
└── .env.example          # Required environment variables

web/
├── app/                  # Next.js App Router
├── components/           # React components
├── vitest.config.ts      # Test configuration
└── package.json          # pnpm scripts

streamlit_web/
└── src/admin_dashboard.py    # Streamlit entry point

postgres-init/
└── 01-init-dbs.sql       # DB initialization (runs once)
```

## Troubleshooting

**Service can't connect to database**:
- Ensure `docker compose up -d` (root level) is running first
- Check that `POSTGRES_HOST=postgres` (container name, not localhost)
- Verify the external network exists: `docker network ls | grep network`

**Celery worker not processing tasks**:
- Check Redis URL uses DB 1 (not DB 0)
- Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` use different DBs

**JWT verification fails**:
- Ensure `JWT_ALGORITHM=RS256` (not HS256)
- Check `CASDOOR_JWKS_URL` is reachable from the API container
- Verify token was issued by Casdoor (port 8000)

**Module import errors in Docker**:
- `PYTHONPATH` is set to `/app/src:/app` in Dockerfile
- All imports should be absolute from `src/` (e.g., `from core import settings`)

**Frontend auth errors**:
- Copy `web/.env.example` to `web/.env` and update Casdoor client credentials
- Ensure `NEXTAUTH_URL` matches the frontend port (3000)

## Testing

- **agent_api**: `uv run pytest` (pytest with asyncio support)
- **web**: `pnpm test` (Vitest with jsdom)
  - Tests use `@testing-library/react` patterns
  - Aliases resolved via `vitest.config.ts` (`@/` maps to root)
