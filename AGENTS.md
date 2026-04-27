# AGENTS.md

方圆智版 (FangYuanZhiBan) - Multi-service AI education platform

## Architecture Overview

Multi-service architecture with 4 distinct services:

| Service         | Tech                              | Port | Purpose                                        |
| --------------- | --------------------------------- | ---- | ---------------------------------------------- |
| `agent_api/`    | Python 3.12 + FastAPI + LangGraph | 8001 | AI agent engine (RAG, chatbot, Celery workers) |
| `user_api/`     | Python 3.12 + FastAPI             | 8000 | User/course management API                     |
| `steamlit_web/` | Python 3.12 + Streamlit           | N/A  | Admin UI for content ingestion                 |
| `web/`          | Next.js 16 + React 19             | 3000 | Frontend web application                       |

Infrastructure (Docker Compose):
- PostgreSQL 16 + pgvector (port 5432) - Shared database with logical separation
- Redis 7 (port 6379) - Cache and message broker

## Getting Started

```bash
# 1. Start infrastructure first (required before any service)
docker compose -f compose.infra.yaml up -d

# 2. Configure environment
cp agent_api/.env.example agent_api/.env
# Edit agent_api/.env with your API keys

# 3. Start services (each has its own compose.yaml)
cd agent_api && docker compose up -d
cd user_api && docker compose up -d
cd steamlit_web && docker compose up -d
cd web && pnpm install && pnpm dev
```

## Service Details

### agent_api (AI Engine)

**Key directories:**
- `src/agents/` - LangGraph agents (rag_assistant, chatbot, safeguard)
- `src/api/` - FastAPI routes
- `src/core/` - Config, LLM, cache, rate limiting
- `src/tasks/` - Celery background tasks

**Agent patterns** (see `src/agents/AGENTS.md` for detailed conventions):
- Agent registry in `agents.py` with lazy loading support
- Always call `await load_agent(id)` before `get_agent(id)` for lazy agents
- Safeguard check required before model invocation (prompt injection protection)
- Use `get_model()` with config override, never hardcode model names

**Development:**
```bash
cd agent_api
# Install deps (uses uv)
uv sync --frozen
# Run with hot reload
MODE=dev python src/main.py
# Or with Docker
docker compose up -d
```

**Testing:**
```bash
uv run pytest
uv run ruff check .
uv run mypy src/
```

**Configuration:**
- `config.yaml` - Model providers and defaults
- `.env` - Secrets and runtime config (see `.env.example`)
- Models: DeepSeek, Qwen (DashScope), OpenAI supported
- Database: Dedicated `db_agent` logical database
- Redis: DB 1 for cache/rate limiting, DB 2 for Celery results

### user_api (Business API)

**Key directories:**
- `src/api/` - FastAPI service
- `src/models/` - SQLAlchemy models (User, Course, Role)
- `src/core/` - Database, security
- `alembic/` - Database migrations

**Database migrations:**
```bash
cd user_api
alembic upgrade head
# or from container
```

**Seeding data:**
```bash
python src/scripts/seed_runner.py
```

### web (Next.js Frontend)

**Tech stack:**
- Next.js 16.2.1 + React 19.2.4
- TypeScript 5
- Tailwind CSS 4
- shadcn/ui (radix-nova style)
- Vitest for testing

**Development:**
```bash
cd web
pnpm install
pnpm dev          # Dev server on :3000
pnpm test         # Run tests once
pnpm test:watch   # Watch mode
pnpm lint         # ESLint
```

**Project structure:**
- `app/` - App router pages
- `components/` - React components (shadcn/ui + custom)
- `lib/` - Utilities, API clients
- `hooks/` - Custom React hooks

**Conventions:**
- Uses `@/` path alias for project root
- shadcn components in `components/ui/`
- Tailwind v4 with CSS variables in `app/globals.css`

### steamlit_web (Admin Tools)

**Purpose:** Document ingestion and chunk viewing for RAG

**Pages:**
- `streamlit_admin.py` - Main entry
- `pages/ingest_ui.py` - Document upload/ingestion
- `pages/chunk_viewer.py` - View document chunks

**Run locally:**
```bash
cd steamlit_web
streamlit run streamlit_admin.py
```

## Docker Patterns

All Python services use `uv` for dependency management:
- `pyproject.toml` + `uv.lock` for dependencies
- Multi-stage builds with cache mounts
- System-level Python (no venv in containers)
- External network `network` shared across services

**Build args:**
```dockerfile
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-install-project --no-dev
```

## Database Conventions

- **PostgreSQL** with pgvector extension for embeddings
- **Logical separation:** Different databases per service (`db_agent`, business DB)
- **Redis DB isolation:**
  - DB 0: Reserved for business cache
  - DB 1: Agent cache + Celery broker
  - DB 2: Celery results

## Environment Variables

Critical env vars for `agent_api/.env`:
```bash
# Core
HOST=0.0.0.0
PORT=8001
MODE=production  # or 'dev' for hot reload

# APIs
DEEPSEEK_API_KEY=...
OPENAI_API_KEY=...

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=db_agent

# Redis
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/1

# Security
JWT_PUBLIC_KEY="..."  # RS256 public key (single line with \n)
ENABLE_SAFEGUARD=true
RATE_LIMIT_ENABLED=true
```

## Common Commands

```bash
# View logs
docker logs -f server
docker logs -f celery_worker

# Restart services
docker compose -f agent_api/compose.yaml restart

# Database shell
docker exec -it postgres psql -U postgres -d db_agent

# Redis CLI
docker exec -it redis redis-cli -n 1

# Check Celery workers
docker exec celery_worker celery -A core.celery_app inspect active
```

## Code Quality

**Python (agent_api, user_api):**
- Ruff for linting/formatting (line length 100)
- MyPy for type checking
- Pytest for testing

**TypeScript (web):**
- ESLint (Next.js config)
- TypeScript strict mode
- Vitest for unit tests

## Important Notes

- **Infrastructure first:** Always start `compose.infra.yaml` before application services
- **Network sharing:** Services communicate via `network` (external Docker network)
- **Agent loading:** Lazy agents require explicit `load_agent()` call before use
- **Safeguard:** All user-facing agents must route through prompt injection check
- **Windows compatibility:** `main.py` includes `WindowsSelectorEventLoopPolicy` patch for asyncio
