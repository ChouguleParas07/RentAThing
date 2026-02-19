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

- Copy `.env.example` to `.env` and set `SECRET_KEY` (and adjust DB/Redis if needed).
- Install dependencies: `pip install .[dev]`
- Run API: `uvicorn app.main:app --reload`
- Open the simple frontend: **http://localhost:8000/app/**
- Or run full stack: `docker-compose up`

### Frontend

A minimal frontend lives in `frontend/` (vanilla HTML/CSS/JS, no build). It is served by the API at `/app` so you can use the app at **http://localhost:8000/app/** without CORS. See `frontend/README.md` for details.

