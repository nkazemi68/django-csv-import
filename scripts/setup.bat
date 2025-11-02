@echo off
chcp 65001 >nul
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: ------------------------------------------------------------------
:: setup.bat  - Interactive installer / starter for django-csv-import
:: ------------------------------------------------------------------

echo.
echo. ******************************************************************************
echo.  ▄▄▄▄     ▄▄▄    ▄▄▄   ▄▄▄▄  ▄    ▄ ▄▄▄▄▄  ▄    ▄ ▄▄▄▄▄   ▄▄▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄▄
echo.  █   ▀▄     █  ▄▀   ▀ █▀   ▀ ▀▄  ▄▀   █    ██  ██ █   ▀█ ▄▀  ▀▄ █   ▀█   █
echo.  █    █     █  █      ▀█▄▄▄   █  █    █    █ ██ █ █▄▄▄█▀ █    █ █▄▄▄▄▀   █
echo.  █    █     █  █          ▀█  ▀▄▄▀    █    █ ▀▀ █ █      █    █ █   ▀▄   █
echo.  █▄▄▄▀  ▀▄▄▄▀   ▀▄▄▄▀ ▀▄▄▄█▀   ██   ▄▄█▄▄  █    █ █       █▄▄█  █    ▀   █
echo. ******************************************************************************
echo.


:: === Repo URL and Local address - edit if needed ===
SET "REPO_URL=https://github.com/nkazemi68/django-csv-import.git"
IF "%~1"=="" (
  SET "TARGET_DIR=%USERPROFILE%\Desktop\django-csv-import"
) ELSE (
  SET "TARGET_DIR=%~1"
)
SET "LOGFILE=%~dp0setup.log"
SET "TS=%DATE% %TIME%"

CALL :print_header "Django CSV Import - Setup"
CALL :info "Target directory: %TARGET_DIR%"

IF NOT EXIST "%TARGET_DIR%" (
  md "%TARGET_DIR%" 2>>"%LOGFILE%" || (
    CALL :err "Failed to create target dir: %TARGET_DIR%"
    exit /b 1
  )
)

PUSHD "%TARGET_DIR%"

CALL :section "1) Checking Git"
where git >nul 2>&1
IF ERRORLEVEL 1 (
  CALL :err "git not found. Install Git: https://git-scm.com/download/win"
  echo %TS% - git not found >> "%LOGFILE%"
  POPD
  exit /b 1
) ELSE (
  for /f "tokens=2 delims= " %%a in ('git --version') do CALL :ok "git %%a"
)

CALL :section "2) Checking Docker"
where docker >nul 2>&1
IF ERRORLEVEL 1 (
  CALL :err "docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
  echo %TS% - docker not found >> "%LOGFILE%"
  POPD
  exit /b 1
) ELSE (
  docker --version 2>>"%LOGFILE%"
  IF ERRORLEVEL 1 (
    CALL :warn "docker present but 'docker --version' failed. Check installation."
  ) ELSE (
    FOR /F "tokens=3 delims= " %%v IN ('docker --version') DO CALL :ok "docker %%v"
  )
)

CALL :section "3) Checking Python (optional)"
where python >nul 2>&1
IF ERRORLEVEL 1 (
  CALL :warn "python not found in PATH. Recommended for local dev: https://www.python.org/downloads/windows/"
  echo %TS% - python not found >> "%LOGFILE%"
) ELSE (
  for /f "tokens=2 delims= " %%p in ('python --version 2^>^&1') do CALL :ok "python %%p"
)

CALL :section "4) Clone or update repository"
IF NOT EXIST ".git" (
  CALL :info "Cloning %REPO_URL% ..."
  git clone "%REPO_URL%" . 2>>"%LOGFILE%" || (
    CALL :err "git clone failed. See %LOGFILE%"
    POPD
    exit /b 1
  )
  CALL :ok "Repository cloned."
) ELSE (
  CALL :info "Repo exists. Fetching latest..."
  git fetch --all 2>>"%LOGFILE%" || CALL :warn "git fetch failed (see %LOGFILE%)"
  git pull 2>>"%LOGFILE%" || CALL :warn "git pull failed (see %LOGFILE%)"
  CALL :ok "Repository updated."
)

CALL :section "5) Checking docker-compose configuration"
docker compose -f infra/docker-compose.yml config >nul 2>&1
IF ERRORLEVEL 1 (
  docker-compose -f infra\docker-compose.yml config >nul 2>&1
  IF ERRORLEVEL 1 (
    CALL :warn "docker compose config failed. Ensure Docker Compose is available and infra/docker-compose.yml is valid."
    echo %TS% - docker-compose config failed >> "%LOGFILE%"
  ) ELSE (
    CALL :ok "docker-compose config OK"
  )
) ELSE (
  CALL :ok "docker compose config OK"
)

CALL :section "6) Start Services"
set /p START_NOW="Do you want to start the project now using Docker Compose? (Y/n): "
if /I "%START_NOW%"=="Y" (
  CALL :info "Starting project (docker compose up --build). This will stream logs..."
  docker compose -f infra\docker-compose.yml up --build
) ELSE (
  CALL :info "Setup finished. To start the project manually run:"
  CALL :info "  docker compose -f infra\docker-compose.yml up --build"
  CALL :info "See README.md for API usage and further instructions."
)

POPD
pause
exit /b 0

:print_header
echo.
echo =============================================================
echo %~1
echo =============================================================
goto :eof

:section
echo.
echo -------------------------------------------------------------
echo %~1
echo -------------------------------------------------------------
goto :eof

:info
echo [INFO] %~1
goto :eof

:ok
echo [OK] %~1
goto :eof

:warn
echo [WARN] %~1
goto :eof

:err
echo [ERROR] %~1
goto :eof
