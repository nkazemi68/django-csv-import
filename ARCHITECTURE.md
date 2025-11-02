# Architecture & Design Decisions

## Chosen style: Modular Monolith + Service Layer
- Single repo and deployment (monolith) but code organized into modules/apps (`src_package.apps.*`).
- Each app contains a `services/` directory — business logic lives in services, views are thin.
- Celery is used for async CSV processing; Redis as broker.

## Why not Microservices?
- Overhead and infra complexity for a small interview task.
- Harder to deliver reliably in a short time.

## Why Service Layer?
- Easier unit testing of business rules.
- Cleaner separation: views handle transport (HTTP), services handle business logic.

## Structure highlights
- `src/src_package/importer/services/import_service.py` — orchestrates validation, batching, db ops.
- `tasks.py` — Celery tasks call services.
- `ImportTask` model holds status & granular errors.

## Runtime
- Docker Compose runs 4 services: web, worker, postgres, redis.