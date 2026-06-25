from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_docker_compose_defines_one_command_radar_dev_stack() -> None:
    compose = read("docker-compose.yml")

    for service in ["redis", "backend-init", "api", "worker", "frontend"]:
        assert f"  {service}:" in compose

    assert "redis:7-alpine" in compose
    assert "${POWER_WEB_OS_API_HOST_PORT:-8001}:8000" in compose
    assert '"5173:5173"' in compose
    assert "${POWER_WEB_OS_REDIS_HOST_PORT:-6380}:6379" in compose
    assert "python -m alembic upgrade head" in compose
    assert "python -m power_web_os.demo seed-radar-db" in compose
    assert "uvicorn" in compose
    assert "celery" in compose
    assert "power_web_os.jobs.radar_jobs.radar_celery_app" in compose


def test_docker_compose_uses_shared_sqlite_and_redis_contract() -> None:
    compose = read("docker-compose.yml")

    assert "POWER_WEB_OS_DATABASE_URL: sqlite:////app/demo/output/power_web_os.sqlite3" in compose
    assert "POWER_WEB_OS_CELERY_BROKER_URL: redis://redis:6379/0" in compose
    assert "POWER_WEB_OS_CELERY_RESULT_BACKEND: redis://redis:6379/1" in compose
    assert compose.count("./demo/output:/app/demo/output") >= 3
    assert compose.count("./.env:/app/.env:ro") >= 3
    assert compose.count("env_file:") >= 3
    assert compose.count("- .env") >= 3
    assert (
        "VITE_POWER_WEB_OS_API_BASE_URL: "
        "${VITE_POWER_WEB_OS_API_BASE_URL:-http://127.0.0.1:8001}"
    ) in compose
    assert (
        "POWER_WEB_OS_CORS_ORIGINS: "
        "${POWER_WEB_OS_CORS_ORIGINS:-http://127.0.0.1:5173,http://localhost:5173}"
    ) in compose


def test_docker_build_context_does_not_include_local_secrets_or_artifacts() -> None:
    dockerignore = read(".dockerignore")

    for ignored in [
        ".env",
        ".env.*",
        ".external/",
        "demo/output/",
        "frontend/node_modules/",
        "frontend/dist/",
    ]:
        assert ignored in dockerignore


def test_backend_and_frontend_dockerfiles_install_expected_runtime_dependencies() -> None:
    backend = read("Dockerfile.backend")
    frontend = read("frontend/Dockerfile")

    assert "python:3.12-slim" in backend
    assert "git" in backend
    assert 'python -m pip install -e ".[api,agent,dev]"' in backend
    assert "COPY config ./config" in backend
    assert "uvicorn" in backend
    assert "node:22-slim" in frontend
    assert "npm install" in frontend
    assert "COPY ui-design-system /app/ui-design-system" in frontend
    assert "vite" in frontend


def test_frontend_dockerfile_includes_design_system_import_target() -> None:
    main_tsx = read("frontend/src/main.tsx")
    frontend = read("frontend/Dockerfile")

    assert "../../ui-design-system/colors_and_type.css" in main_tsx
    assert "COPY ui-design-system /app/ui-design-system" in frontend
