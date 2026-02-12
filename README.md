## Rent-a-Thing — Hyperlocal Rental Marketplace (Backend)

Backend service for a hyperlocal rental marketplace built with FastAPI, PostgreSQL, Redis, and Celery using a clean, layered architecture.

### Tech stack

- FastAPI (async)
- PostgreSQL + SQLAlchemy 2.0 async
- Redis
- Celery
- Pydantic v2
- Docker / docker-compose

### High-level layout

- `app/` — application code (API, services, repositories, models, etc.)
- `app/api/` — FastAPI routers and dependencies
- `app/core/` — configuration, security, middleware, logging
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic request/response models
- `app/repositories/` — data access layer
- `app/services/` — business logic
- `app/db/` — DB session handling and migrations wiring
- `app/tasks/` — Celery tasks
- `app/utils/` — helpers and shared utilities

### Running locally (overview)

- Copy `.env.example` to `.env` and adjust values.
- Install dependencies using `pip` with `pyproject.toml` or `requirements.txt`.
- Run services via `docker-compose up`.

Detailed commands will be added as we progress through the phases.

