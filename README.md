# django-csv-import

**Small modular-monolith app** for CSV import using Django + DRF + Celery + Redis + Postgres.
This repo is arranged for review: Quick-start instructions (manual & automated), infra, and a Service Layer skeleton.

<!-- Project badges -->
[![Python](https://img.shields.io/badge/Python-3.12-yellow.svg)]()
[![Django](https://img.shields.io/badge/Django-5.2.7-darkgreen.svg)]()
[![DRF](https://img.shields.io/badge/Django--REST--Framework-3.16.1-orange.svg)]()
[![Celery](https://img.shields.io/badge/Celery-5.5.3-green.svg)]()
[![Redis](https://img.shields.io/badge/Redis-latest_(8.2.2)-red.svg)]()
[![Postgres](https://img.shields.io/badge/Postgres-latest_(18)-blue.svg)]()

---

## Quick Start (Windows)
Prereqs: Docker Desktop running, Git, (Python optional)

1. Clone repo:
```cmd
git clone https://github.com/youruser/your-repo.git

cd your-repo
```
2. Run setup script (interactive):
```cmd
scripts\setup.bat
```
- The script checks for Git, Docker, Python.

- It can optionally run docker-compose up --build for you.

3. Manual start (if you prefer):
```cmd
docker-compose -f infra\docker-compose.yml up --build
```
Open http://127.0.0.1:8000/ for the Django app (dev server).

## Quick Start (Ubuntu)
Prereqs: docker, docker-compose (or docker compose), git, python3 (for local dev).

### Manual:
```bash
git clone https://github.com/youruser/your-repo.git

cd your-repo
docker-compose -f infra/docker-compose.yml up --build
```
## API (placeholders — implemented in skeleton)
- POST /api/imports/ — multipart/form-data "file" → returns { "task_id": "<celery-id>" } (202)
- GET /api/imports/{task_id}/ — return status & errors

### Example (curl):
```bash
curl -X POST "http://127.0.0.1:8000/api/imports/
" -F "file=@example.csv"
```

## Project layout (important files)
```
.
├── infra/ # docker compose + Dockerfile.web + Dockerfile.worker
├── scripts/ # setup scripts (setup.bat for windows and setup.sh for linux)
├── src/
│ ├── manage.py
│ └── src_package/ # django project
│ ├── settings.py
│ └── ...
├── example.csv
├── README.md
└── CONTRIBUTING.md
```
## Notes for users

- You do NOT need to install development tools (Commitizen, pre-commit) to run the project. Those are developer conveniences; instructions live in CONTRIBUTING.md.

- If you run scripts\setup.bat it will offer to start the project with Docker Compose.

- This repo uses a **Modular Monolith** with a small **Service Layer** (business logic outside views). See `architecture.md`.

---

## Next steps for contributor
After you verify scaffold is fine, follow next tasks:

- Implement models & migrations (`apps/imports` already skeletoned)

- Implement Celery tasks and results storage

- Add tests & CI workflow

---