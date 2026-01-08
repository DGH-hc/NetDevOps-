# app/worker/celery_app.py

from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime
import time
import traceback
from typing import List, Optional

# App-local imports
from app.core.config import settings
from app.db.database import SessionLocal
from app.utils.secrets import get_secret
from app.utils.deploy import (
    fetch_running_config,
    save_snapshot_to_fs,
    apply_config,
    verify_config,
    rollback_from_snapshot,
)

# Models
from app.models.job import JobDB, JobAttempt, JobLog
from app.models.device import DeviceDB
from app.models.snapshot import ConfigSnapshot

# Optional metrics
try:
    from app.metrics import jobs_pushed_total, job_execution_seconds
except Exception:
    jobs_pushed_total = None
    job_execution_seconds = None


# ==========================================================
# Celery instance (single source of truth)
# ==========================================================
celery_app = Celery(
    "netdevops",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery_app.conf.task_routes = {
    "app.worker.celery_app.*": {"queue": "default"}
}
celery_app.conf.update(
    task_soft_time_limit=300,
    task_time_limit=600,
)


# ==========================================================
# Test task
# ==========================================================
@celery_app.task(name="app.worker.celery_app.test_task")
def test_task():
    return "Test task executed successfully!"


# ==========================================================
# DB connectivity test task
# ==========================================================
@celery_app.task(bind=True, name="app.worker.celery_app.placeholder_job")
def placeholder_job(self, job_id: int):
    db: Session = SessionLocal()
    try:
        db.execute("SELECT 1")
        return {
            "status": "OK",
            "message": "Worker DB connection successful",
            "job_id": job_id,
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
            "job_id": job_id,
        }
    finally:
        db.close()


# ==========================================================
# Production job: push_config_job
# ==========================================================
@celery_app.task(bind=True, name="app.worker.celery_app.push_config_job")
def push_config_job(
    self,
    job_id: int,
    attempt_id: int,
    config_lines: Optional[List[str]],
    verify_commands: Optional[List[str]] = None,
) -> dict:
    db: Session = SessionLocal()
    start_time = time.time()

    if jobs_pushed_total:
        try:
            jobs_pushed_total.inc()
        except Exception:
            pass

    try:
        job = db.query(JobDB).filter(JobDB.id == job_id).one_or_none()
        attempt = db.query(JobAttempt).filter(JobAttempt.id == attempt_id).one_or_none()

        if not job or not attempt:
            return {"status": "MISSING", "reason": "job_or_attempt_not_found"}

        device = db.query(DeviceDB).filter(DeviceDB.id == job.device_id).one_or_none()
        if not device:
            job.status = "FAILED"
            db.add(job)
            db.commit()
            return {"status": "FAILED", "reason": "device_not_found"}

        # Fetch secrets
        try:
            creds = (
                get_secret(device.credentials_ref)
                if getattr(device, "credentials_ref", None)
                else {}
            )
            device.username = creds.get("username") or device.username
            device.password = creds.get("password") or device.password
            device.enable = creds.get("enable") or device.enable
        except Exception as e:
            db.add(
                JobLog(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    output=f"Secret fetch failed: {e}",
                    exit_code=2,
                )
            )
            job.status = "FAILED"
            db.add(job)
            db.commit()
            return {"status": "FAILED", "reason": "secret_fetch_failed"}

        # Mark running
        job.status = "RUNNING"
        attempt.started_at = datetime.utcnow()
        db.add(job)
        db.add(attempt)
        db.commit()

        # Snapshot
        code, running_config = fetch_running_config(device)
        if code != 0:
            job.status = "FAILED"
            db.add(
                JobLog(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    output=f"Snapshot failed: {running_config}",
                    exit_code=2,
                )
            )
            db.add(job)
            db.commit()
            return {"status": "FAILED", "reason": "snapshot_failed"}

        snapshot_path = save_snapshot_to_fs(device.id, running_config)
        db.add(
            ConfigSnapshot(
                device_id=device.id,
                filename=snapshot_path,
                content=running_config,
            )
        )
        db.commit()

        # Apply config
        if not config_lines:
            job.status = "FAILED"
            db.add(job)
            db.commit()
            return {"status": "FAILED", "reason": "no_config_lines"}

        apply_exit, apply_output = apply_config(device, config_lines)
        db.add(
            JobLog(
                job_id=job.id,
                attempt_id=attempt.id,
                output=apply_output,
                exit_code=apply_exit,
            )
        )
        db.commit()

        if apply_exit != 0:
            rollback_from_snapshot(device, snapshot_path)
            job.status = "FAILED"
            attempt.completed_at = datetime.utcnow()
            attempt.exit_code = apply_exit
            db.add(job)
            db.add(attempt)
            db.commit()
            return {"status": "FAILED", "reason": "apply_failed"}

        # Verify
        ok, verify_output = verify_config(device, verify_commands or [])
        db.add(
            JobLog(
                job_id=job.id,
                attempt_id=attempt.id,
                output=verify_output,
                exit_code=0 if ok else 1,
            )
        )
        db.commit()

        if not ok:
            rollback_from_snapshot(device, snapshot_path)
            job.status = "FAILED"
            attempt.completed_at = datetime.utcnow()
            attempt.exit_code = 1
            db.add(job)
            db.add(attempt)
            db.commit()
            return {"status": "FAILED", "reason": "verify_failed"}

        # Success
        job.status = "SUCCESS"
        attempt.completed_at = datetime.utcnow()
        attempt.exit_code = 0
        db.add(job)
        db.add(attempt)
        db.commit()

        return {"status": "SUCCESS", "job_id": job.id}

    except Exception as e:
        db.add(
            JobLog(
                job_id=job_id,
                attempt_id=attempt_id,
                output=f"{e}\n{traceback.format_exc()}",
                exit_code=1,
            )
        )
        db.commit()
        return {"status": "FAILED", "error": str(e)}

    finally:
        if job_execution_seconds:
            try:
                job_execution_seconds.observe(time.time() - start_time)
            except Exception:
                pass
        db.close()
