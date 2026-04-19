from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import models  # noqa: F401
from app.config import SERVER_DIR, get_settings
from app.db import Base, SessionLocal, engine, ensure_runtime_schema
from app.routers import api_auth, api_knowledge, api_package, api_prompt, api_report, api_result, api_settings, api_system, api_tasks, web
from app.services.seed_service import initialize_seed_data


settings = get_settings()


def configure_logging() -> None:
    log_path = settings.logs_root / "app.log"
    if logging.getLogger().handlers:
        return
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


configure_logging()

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()
    db = SessionLocal()
    try:
        initialize_seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, session_cookie=settings.session_cookie_name)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.mount("/static", StaticFiles(directory=str((SERVER_DIR / "app" / "static").resolve())), name="static")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = perf_counter()
    logger = logging.getLogger("photography.request")
    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001
        elapsed_ms = (perf_counter() - start) * 1000
        logger.exception("request failed method=%s path=%s duration_ms=%.2f", request.method, request.url.path, elapsed_ms)
        raise
    elapsed_ms = (perf_counter() - start) * 1000
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    logging.getLogger("photography.error").warning("value error: %s", exc)
    return JSONResponse(status_code=422, content={"success": False, "message": str(exc), "error_code": "VALUE_ERROR", "data": None})


app.include_router(api_auth.router)
app.include_router(api_tasks.router)
app.include_router(api_package.router)
app.include_router(api_prompt.router)
app.include_router(api_result.router)
app.include_router(api_report.router)
app.include_router(api_knowledge.router)
app.include_router(api_settings.router)
app.include_router(api_system.router)
app.include_router(web.router)
