# app/api/v1/jobs_api.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models.job import JobDB
from app.metrics import get_metrics
from app.worker.celery_app import celery_app  # ✅ correct import

router = APIRouter(prefix="/jobs", tags=["jobs"])

logger = logging.getLogger(__name__)


@router.post("/run/{job_id}")
def run_job_async(job_id: int, db: Session = Depends(get_db)):

    # -----------------------------
    # Validate job exists
    # -----------------------------
    job = db.get(JobDB, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # -----------------------------
    # Metrics (STRICT API SCOPE)
    # -----------------------------
    metrics = get_metrics(scope="api")

    # 🔒 HARD GUARD (relaxed but safe)
    assert "pushed" in metrics, "API must expose pushed metric"

    metrics["pushed"].inc()

    # -----------------------------
    # Enqueue Celery task (CORRECT WAY)
    # -----------------------------
    try:
        celery_app.send_task(
            "app.worker.tasks.run_job",  # ✅ fully qualified name
            args=[job_id],
        )
        logger.info(f"Job {job_id} enqueued")

    except Exception as e:
        logger.error(f"Failed to enqueue job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue job: {e}"
        )

    # -----------------------------
    # Response
    # -----------------------------
    return {
        "job_id": job.id,
        "status": "QUEUED"
    }