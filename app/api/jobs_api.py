from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.job import JobDB, JobAttempt, JobLog
from app.models.device import DeviceDB
from app.worker.celery_app import push_config_job

# 🔐 RBAC
from app.api.deps import require_role

# 📝 Audit logging
from app.utils.audit import audit

router = APIRouter(prefix="/jobs", tags=["jobs"])

# ---------------------------
# Schemas
# ---------------------------
class JobCreate(BaseModel):
    name: str
    device_id: int
    command: str

class JobOut(BaseModel):
    id: int
    name: str
    device_id: int
    command: str
    status: str

    class Config:
        orm_mode = True

class LogOut(BaseModel):
    id: int
    job_id: int
    attempt_id: int | None
    output: str | None
    exit_code: int | None
    created_at: str

    class Config:
        orm_mode = True

class PushPayload(BaseModel):
    config: List[str]
    verify_commands: List[str] = []

# ---------------------------
# Routes
# ---------------------------

# ADMIN + OPERATOR: create job
@router.post("/", response_model=JobOut,
             dependencies=[Depends(require_role("admin", "operator"))])
@audit(action="create_job")
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    device = db.query(DeviceDB).get(payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    job = JobDB(
        name=payload.name,
        device_id=payload.device_id,
        command=payload.command
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

# ADMIN + OPERATOR: run job
@router.post("/run/{job_id}",
             dependencies=[Depends(require_role("admin", "operator"))])
@audit(action="run_job")
def run_job_endpoint(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobDB).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "RUNNING":
        raise HTTPException(status_code=400, detail="Job already running")

    attempt = JobAttempt(
        job_id=job.id,
        attempt_no=(len(job.attempts) + 1 if job.attempts else 1)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "message": "Run job endpoint hit, but no execute_job task exists",
        "job_id": job.id,
        "attempt_id": attempt.id
    }

# ALL ROLES: read job details
@router.get("/{job_id}", response_model=JobOut,
            dependencies=[Depends(require_role("admin", "operator", "auditor"))])
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobDB).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# ADMIN + AUDITOR: read logs
@router.get("/{job_id}/logs", response_model=List[LogOut],
            dependencies=[Depends(require_role("admin", "auditor"))])
@audit(action="view_logs")
def get_logs(job_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(JobLog)
        .filter(JobLog.job_id == job_id)
        .order_by(JobLog.created_at.desc())
        .all()
    )
    return logs

# ADMIN + OPERATOR: push config
@router.post("/push/{job_id}",
             dependencies=[Depends(require_role("admin", "operator"))])
@audit(action="push_config")
def push_config(job_id: int, payload: PushPayload, db: Session = Depends(get_db)):

    job = db.query(JobDB).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "RUNNING":
        raise HTTPException(status_code=400, detail="Job already running")

    attempt = JobAttempt(
        job_id=job.id,
        attempt_no=(len(job.attempts) + 1 if job.attempts else 1)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    task = push_config_job.delay(
        job.id,
        attempt.id,
        payload.config,
        payload.verify_commands
    )

    return {
        "job_id": job.id,
        "attempt_id": attempt.id,
        "task_id": task.id,
        "message": "Config push job enqueued"
    }
