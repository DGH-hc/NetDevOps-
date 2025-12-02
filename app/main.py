# app/main.py

import logging
from logging.handlers import RotatingFileHandler
import os
import time

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# -----------------------------
# Correct absolute imports
# -----------------------------
from app.api.routers import router as api_router      # PHASE-0 FIX
from app.core.config import settings, load_vault_into_settings
from app.metrics import request_latency_seconds
from app.logger import logger 

# ============================
# Logging Setup
# ============================
LOG_DIR = "/app/logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "app.log")
handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()]
)

logger = logging.getLogger("netdevops")
logger.info("App starting...")


# ============================
# Metrics Middleware
# ============================
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time

        request_latency_seconds.labels(
            endpoint=request.url.path,
            method=request.method
        ).observe(elapsed)

        return response


# ============================
# FastAPI App
# ============================
app = FastAPI(
    title="Network DevOps Automation Platform",
    description="Production-grade Network Automation Backend",
    version="2.0.0"
)

app.add_middleware(MetricsMiddleware)


# ============================
# Startup Event
# ============================
@app.on_event("startup")
def startup_event():
    logger.info("📦 FastAPI startup: loading Vault secrets...")

    try:
        load_vault_into_settings()
        logger.info("🔐 Vault secrets loaded successfully")
    except Exception as e:
        logger.error(f"⚠ Vault secret load failed: {e}")


# ============================
# Routers (PHASE-0 FIX)
# ============================
# All routes from app/api/v1/* automatically mounted under /api
app.include_router(api_router, prefix="/api")


# ============================
# Metrics Endpoint
# ============================
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================
# Root Endpoint
# ============================
@app.get("/")
def home():
    return {
        "message": "🚀 Network DevOps Automation Platform Backend is Live!",
        "docs": "/docs",
        "metrics": "/metrics",
        "api_routes": "/api/v1",
    }


# ============================
# Static Dashboard
# ============================
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/dashboard")
def get_dashboard():
    dashboard_path = os.path.join(static_dir, "dashboard.html")
    return FileResponse(dashboard_path)
