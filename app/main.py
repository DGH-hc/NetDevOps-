# app/main.py

import logging
from logging.handlers import RotatingFileHandler
import os
import time
import redis 

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware


# -----------------------------
# Correct absolute imports
# -----------------------------
from app.api.routers import router as api_router      # PHASE-0 FIX
from app.core.config import settings, load_vault_into_settings
from app.db.database import engine
from app.metrics import setup_metrics 
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
app = FastAPI(
    title="Network DevOps Automation Platform",
    description="Production-grade Network Automation Backend",
    version="2.0.0"
)

setup_metrics(app)

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



#=============================
# Health: Liveness
#=============================
@app.get("/health/live")
def health_live():
    return {"status": "alive"}

#=============================
#Health: Readiness
#=============================
@app.get("/health/ready")
def health_ready():
     #Check database
     try:
         with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
     except Exception as e:
         return {"statue": "not ready", "reason":"database unavailable"}

     #check Redis
     try: 
         r = redis.Redis.form_url(settings.REDIS_URL)
         r.ping()
     except Exception as e :
         return {"status": "not ready", "rason": "redis unavailable"}

     return {"status": "ready"}       


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
