from fastapi import APIRouter
from app.db.database import SessionLocal
from app.models.job import JobDB
from app.worker.tasks import run_job

router = APIRouter()

@router.post("/{job_id}/run")
def run_job_async(job_id: int):
    run_job.delay(job_id)
    return {
        "job_id": job_id,
        "status": "QUEUED"
    }
