from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import Base, sync_engine, init_db
from app.api import mentions, analytics, alerts, summaries, websocket
from sqlalchemy.exc import OperationalError
import logging
import uvicorn
from datetime import datetime, timezone
import time
from typing import Any

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    try:
        init_db()
        logger.info("Database initialized successfully")
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    logger.info(f"Application started in {settings.ENVIRONMENT} mode")
    
    yield
    
    logger.info("Application shutting down")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=settings.CORS_EXPOSE_HEADERS,
    max_age=settings.CORS_MAX_AGE,
)


@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"
    
    logger.info(f"Request started: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Request completed: {response.status_code} in {process_time:.2f}ms")
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Request failed: {str(e)} in {process_time:.2f}ms")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


app.include_router(mentions.router, prefix='/api/v1/mentions', tags=["mentions"])
app.include_router(analytics.router, prefix='/api/v1/analytics', tags=["analytics"])
app.include_router(alerts.router, prefix='/api/v1/alerts', tags=["alerts"])
app.include_router(summaries.router, prefix='/api/v1/summaries', tags=["summaries"])
app.include_router(websocket.router, prefix='/api/v1/websocket', tags=["websocket"])


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "message": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    from app.core.database import database_health_check
    db_healthy = database_health_check()
    status = "healthy" if db_healthy else "unhealthy"
    return {
        "status": status,
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/health")
async def api_health_check() -> dict[str, Any]:
    from app.core.database import database_health_check
    db_healthy = database_health_check()
    status = "healthy" if db_healthy else "unhealthy"
    return {
        "status": status,
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "brand-reputation-api"
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=False
    )