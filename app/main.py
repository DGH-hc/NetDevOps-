# app/main.py

from importlib.resources import path
import shutil 
import logging
from logging.handlers import RotatingFileHandler
import os
import time
from urllib import response 
PROM_DIR = "/tmp/prometheus-shared" 

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from prometheus_client import Counter,Histogram 

from app.db.database import SessionLocal

# -----------------------------
# Routers & Config
# -----------------------------
from app.api.routers import router as api_router
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.metrics import setup_metrics

# -----------------------------
# Celery Task Import (CRITICAL)
# -----------------------------
from app.worker.celery_app import test_task


# ============================
# Logging Setup
# ============================
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "app.log")

handler = RotatingFileHandler(
    log_path,
    maxBytes=5 * 1024 * 1024,
    backupCount=3
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()]
)

logger = logging.getLogger("netdevops")
logger.info("App starting...")


# ============================
# FastAPI App
# ============================
app = FastAPI(
    title="Network DevOps Automation Platform",
    description="Production-grade Network Automation Backend",
    version="2.0.0"
)
# ----------------------------------------
# API RED METRICS (Phase 3.5)
# ----------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "api_path"]
)

http_errors_total = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "api_path", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "api_path"]
)

# ==========================================================
# 🔥 METRICS MIDDLEWARE (CRITICAL)
# ==========================================================
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    route = request.scope.get("route")

    if route: 
        path = route.path
    else:
        path = request.url.path

    method = request.method  
                  
    http_requests_total.labels(
       method=method,
       api_path=path
    ).inc()

    http_request_duration_seconds.labels(
      method=method,
      api_path=path
    ).observe(duration)

    if response.status_code >= 400:
     http_errors_total.labels(
        method=method,
        api_path=path,
        status=response.status_code
    ).inc()

    return response



# ============================
# 🚨 JOB TRIGGER ENDPOINT (TESTING)
# ============================
@app.post("/test-job")
def trigger_test_job():
    try:
        task = test_task.apply_async(queue="celery")
        return {
            "status": "submitted",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"❌ Failed to send task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fail-job")
def trigger_fail_job():
    from app.worker.celery_app import celery_app

    task = celery_app.send_task("app.worker.celery_app.fail_task")

    return {"status": "submitted", "task_id": task.id}


# ============================
# Metrics (Prometheus)
# ============================
setup_metrics(app)


# ============================
# Startup Event (NON-BLOCKING)
# ============================
@app.on_event("startup")
async def startup_event():
    logger.info("📦 FastAPI startup: basic initialization only")

    if os.path.exists(PROM_DIR):
        for filename in os.listdir(PROM_DIR):
            file_path = os.path.join(PROM_DIR, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")

    os.makedirs(PROM_DIR, exist_ok=True)

    if not settings:
        logger.error("❌ Settings not initialized")

    logger.info("✅ Startup completed successfully")

# ============================
# Routers
# ============================
# 🔒 CORRECT: all API routes go through this
app.include_router(api_router, prefix="/api")

# 🔒 Health routes
app.include_router(health_router)

# ❌ REMOVED: app.include_router(jobs_router)
# Reason:
# - Already included via api_router
# - Prevents duplicate / conflicting routes


# ============================
# Health: Liveness
# ============================
@app.get("/health")
def health():
    return {"status": "alive"}


# ============================
# Health: Readiness
# ============================
@app.get("/health/ready")
def health_ready():
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.commit()
        return {"status": "ready"}

    except Exception as e:
        logger.error(f"❌ DB readiness failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    finally:
        if db:
            db.close()


# ============================
# Root Endpoint
# ============================
@app.get("/")
def home():
    return {
        "message": "🚀 Network DevOps Automation Platform Backend is Live!",
        "docs": "/docs",
        "metrics": "/metrics",
        "test_job": "/test-job",
        "api_routes": "/api/v1"
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