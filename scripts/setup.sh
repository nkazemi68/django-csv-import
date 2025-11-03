#!/usr/bin/env bash
set -euo pipefail
clear

# --------------------------------------------------------------------
# setup.sh - Interactive installer / starter for django-csv-import
# --------------------------------------------------------------------

cat <<'EOF'
******************************************************************************
 ▄▄▄▄     ▄▄▄    ▄▄▄   ▄▄▄▄  ▄    ▄ ▄▄▄▄▄  ▄    ▄ ▄▄▄▄▄   ▄▄▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄▄
 █   ▀▄     █  ▄▀   ▀ █▀   ▀ ▀▄  ▄▀   █    ██  ██ █   ▀█ ▄▀  ▀▄ █   ▀█   █
 █    █     █  █      ▀█▄▄▄   █  █    █    █ ██ █ █▄▄▄█▀ █    █ █▄▄▄▄▀   █
 █    █     █  █          ▀█  ▀▄▄▀    █    █ ▀▀ █ █      █    █ █   ▀▄   █
 █▄▄▄▀  ▀▄▄▄▀   ▀▄▄▄▀ ▀▄▄▄█▀   ██   ▄▄█▄▄  █    █ █       █▄▄█  █    ▀   █
******************************************************************************
EOF

printf "\n\n"

REPO_URL="https://github.com/nkazemi68/django-csv-import.git"
DEFAULT_DIR="djcsv"
LOGFILE="$(dirname "$0")/setup.log"
TIMESTAMP() { date "+%Y-%m-%d %H:%M:%S"; }

print_header() {
  printf "\n%s\n" "============================================================="
  printf "%s\n" "$1"
  printf "%s\n\n" "============================================================="
}

section() {
  printf "\n%s\n" "-------------------------------------------------------------"
  printf "%s\n" "$1"
  printf "%s\n" "-------------------------------------------------------------"
}

info()   { printf "[\e[34mINFO\e[0m] %s\n" "$1"; }
ok()     { printf "[\e[32m OK \e[0m] %s\n" "$1"; }
warn()   { printf "[\e[33mWARN\e[0m] %s\n" "$1"; }
err()    { printf "[\e[31mERR \e[0m] %s\n" "$1"; }

print_header "Django CSV Import - Setup"

TARGET_DIR="${1:-}"
if [ -z "$TARGET_DIR" ]; then
  read -r -p "Enter clone directory [default: $DEFAULT_DIR]: " INPUT_DIR
  TARGET_DIR="${INPUT_DIR:-$DEFAULT_DIR}"
fi

info "Target directory: $TARGET_DIR"

if [ -d "$TARGET_DIR" ]; then
  if [ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
    err "Directory '$TARGET_DIR' already exists and is not empty!"
    err "Please choose a different name or delete the directory."
    err "Example: ./setup.sh my-new-project"
    exit 1
  fi
else
  mkdir -p "$TARGET_DIR"
fi

cd "$TARGET_DIR"

section "1) Checking git"
if ! command -v git >/dev/null 2>&1; then
  err "git not found. Install git (e.g. apt install git)"
  echo "$(TIMESTAMP) git not found" >> "$LOGFILE"
  exit 1
else
  ok "$(git --version)"
fi

section "2) Checking docker"
if ! command -v docker >/dev/null 2>&1; then
  err "docker not found. Install Docker (Docker Desktop or docker-engine)"
  exit 1
else
  ok "$(docker --version 2>/dev/null)"
fi

section "3) Checking python (optional)"
if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 not found in PATH. Recommended for local dev."
else
  ok "$(python3 --version 2>/dev/null)"
fi

section "4) Clone or update repository"
if [ ! -d .git ]; then
  info "Cloning $REPO_URL ..."
  if ! git clone "$REPO_URL" . 2>>"$LOGFILE"; then
    err "git clone failed. See $LOGFILE"
    exit 1
  fi
  ok "Repository cloned."
else
  info "Repo exists. Fetching latest..."
  git fetch --all 2>>"$LOGFILE" || warn "git fetch failed"
  git pull 2>>"$LOGFILE" || warn "git pull failed"
  ok "Repository updated."
fi

section "5) Checking docker-compose configuration"
if command -v docker-compose >/dev/null 2>&1; then
  if docker-compose -f infra/docker-compose.yml config >/dev/null 2>&1; then
    ok "docker-compose config OK"
  else
    warn "docker-compose config check failed"
  fi
elif docker compose version >/dev/null 2>&1; then
  if docker compose -f infra/docker-compose.yml config >/dev/null 2>&1; then
    ok "docker compose config OK"
  else
    warn "docker compose config check failed"
  fi
else
  warn "neither docker-compose nor docker compose found"
fi

section "6) Start Services"
read -r -p "Do you want to start the project now using Docker Compose? (Y/n): " START_NOW
START_NOW=${START_NOW:-Y}
if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
  info "Starting project (docker compose up --build). This will stream logs..."
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f infra/docker-compose.yml -p djcsv up --build
  else
    docker-compose -f infra/docker-compose.yml -p djcsv up --build
  fi
else
  info "Setup finished. To start manually run:"
  printf "  cd %s && docker compose -f infra/docker-compose.yml -p djcsv up --build\n" "$TARGET_DIR"
  info "See README.md for API usage and further instructions."
fi

echo
read -n1 -r -p "Press any key to close..."
echo

exit 0