# app/api/v1/health.py

from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.config import settings
import redis

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check():
    status = {
        "postgres": "unknown",
        "redis": "unknown",
    }

    # --- PostgreSQL CHECK ---
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {str(e)}"
    finally:
        try:
            db.close()
        except:
            pass

    # --- REDIS CHECK ---
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"

    return status
