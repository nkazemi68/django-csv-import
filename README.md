# django-csv-import

**Small modular-monolith app** for CSV import using Django + DRF + Celery +
Redis + Postgres. This repo is arranged for review: Quick-start instructions
(manual & automated), infra, and a Service Layer skeleton.

<!-- Project badges -->

[![Python](https://img.shields.io/badge/Python-3.12-yellow.svg)]()
[![Django](https://img.shields.io/badge/Django-5.2.7-darkgreen.svg)]()
[![DRF](https://img.shields.io/badge/Django--REST--Framework-3.16.1-orange.svg)]()
[![Celery](https://img.shields.io/badge/Celery-5.5.3-green.svg)]()
[![Redis](<https://img.shields.io/badge/Redis-latest_(8.2.2)-red.svg>)]()
[![Postgres](<https://img.shields.io/badge/Postgres-latest_(18)-blue.svg>)]()

---

## Quick Start

Prereqs: Docker Desktop running, Git, Python (for local dev).

**Ubuntu**: docker, docker-compose (or docker compose), git, python3 (for local
dev).

1. Clone repo:

   create a directory then:

   ```cmd
   cd to\your\path

   git clone https://github.com/nkazemi68/django-csv-import.git

   cd django-csv-import
   ```
2. Build .env file from example (see `.env.example`), in repo root.
3. Run command to start:
   ```cmd
   docker-compose -f infra\docker-compose.yml -p djcsv up --build
   ```
4. Open http://127.0.0.1:8000/ for the Django app (dev server).

## API (placeholders — implemented in skeleton)

- POST /api/import — multipart/form-data "file" → returns { "task_id":
  "<celery-id>" } (202)
- GET /api/import/{task_id} — return status & paginated errors as json
- http://127.0.0.1:8000/ will show you swagger OpenAPI redoc

### Example (curl):

```bash
curl -X POST "http://127.0.0.1:8000/api/import/
" -F "file=@example.csv"
```

```bash
curl -X POST "http://127.0.0.1:8000/api/import/{task_id}"
```

## Project layout (important files)

```
django-csv-import/
├── infra/ # docker compose + Dockerfile.web + Dockerfile.worker
├── src/ # django project
│ ├── manage.py
│ └── src_package/ # django config and apps
│ ├── settings.py
│ └── ...
├── example.csv
├── README.md
├── ARCHITECTURE.md
└── CONTRIBUTING.md
```

## Notes for users

- You do NOT need to install development tools (Commitizen, pre-commit) to run
  the project. Those are developer conveniences; instructions live in
  `CONTRIBUTING.md`.

- If you run scripts\setup.bat it will offer to start the project with Docker
  Compose.

- This repo uses a **Modular Monolith** with a small **Service Layer** (business
  logic outside views). See `ARCHITECTURE.md`.

---

## Next steps for contributor

After you verify scaffold is fine, you can follow next tasks:

- Implement models & migrations (`src/src_package/apps/importer` already
  skeletoned)

- Implement Celery tasks and results storage

- Add tests & CI workflow

---
