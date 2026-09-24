# app/api/v1/health.py

import redis
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.database import SessionLocal

router = APIRouter()


# --------------------------------------------------
# FULL SYSTEM HEALTH (Diagnostics Only)
# NOT used by Kubernetes probes
# --------------------------------------------------
@router.get("/health/full", tags=["system"])
def health_check():
    status = {
        "postgres": "unknown",
        "redis": "unknown",
    }

    # ---------------------------
    # PostgreSQL Check
    # ---------------------------
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {e!s}"
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass

    # ---------------------------
    # Redis Check
    # ---------------------------
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.set("health_check", "ok")
        value = r.get("health_check")

        if value.decode() == "ok":
            status["redis"] = "ok"
        else: 
             status["redis"] = "error: value mismatch"

    except Exception as e:
        status["redis"] = f"error: {e!s}" 

    return {
        "debug": "health/full executed",
        "status": status
    }      