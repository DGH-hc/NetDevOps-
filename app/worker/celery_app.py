# app/worker/celery_app.py
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime
import time
import traceback
from typing import List, Optional, Tuple

# App-local imports (absolute)
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

# Optional metrics — use if available, otherwise keep no-op
try:
    from app.metrics import jobs_pushed_total, job_execution_seconds
except Exception:
    jobs_pushed_total = None
    job_execution_seconds = None


# ==========================================================
#  Celery Instance (must be named 'app')
# ==========================================================
app = Celery(
    "network_devops_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Route all tasks to default queue
app.conf.task_routes = {"app.worker.celery_app.*": {"queue": "default"}}
app.conf.update(task_soft_time_limit=300, task_time_limit=600)


# ==========================================================
#  BASIC TEST TASK
# ==========================================================
@app.task(name="app.worker.celery_app.test_task")
def test_task():
    return "Test task executed successfully!"


# ==========================================================
#  SIMPLE DB-TEST PLACEHOLDER
# ==========================================================
@app.task(bind=True, name="app.worker.celery_app.placeholder_job")
def placeholder_job(self, job_id: int):
    db: Session = SessionLocal()
    try:
        db.execute("SELECT 1")
        return {"status": "OK", "message": "Worker DB connection successful", "job_id": job_id}
    except Exception as e:
        return {"status": "FAILED", "error": str(e), "job_id": job_id}
    finally:
        db.close()


# ==========================================================
#  FULL PRODUCTION push_config_job (Phase A3)
# ==========================================================
@app.task(bind=True, name="app.worker.celery_app.push_config_job")
def push_config_job(
    self,
    job_id: int,
    attempt_id: int,
    config_lines: Optional[List[str]],
    verify_commands: Optional[List[str]] = None,
) -> dict:
    """
    Full job flow:
      1) Load Job, Attempt, Device from DB
      2) Fetch credentials (secrets)
      3) Snapshot running-config
      4) Save snapshot record
      5) Apply config_lines
      6) Verify using verify_commands
      7) On failure -> rollback_from_snapshot
      8) Write JobLogs and update statuses/attempts
      9) Observe metrics if available
    Returns a dict with status and optional details.
    """
    db: Session = SessionLocal()
    start_time = time.time()
    if jobs_pushed_total:
        try:
            jobs_pushed_total.inc()
        except Exception:
            pass

    try:
        # --- Fetch job and attempt records ---
        job = db.query(JobDB).filter(JobDB.id == job_id).one_or_none()
        attempt = db.query(JobAttempt).filter(JobAttempt.id == attempt_id).one_or_none()

        if not job or not attempt:
            return {"status": "MISSING", "reason": "job_or_attempt_not_found"}

        device = db.query(DeviceDB).filter(DeviceDB.id == job.device_id).one_or_none()
        if not device:
            # mark job failed
            job.status = "FAILED"
            db.add(job)
            db.commit()
            return {"status": "FAILED", "reason": "device_not_found"}

        # --- Fetch credentials from secret store (safe) ---
        try:
            creds = get_secret(device.credentials_ref) if getattr(device, "credentials_ref", None) else {}
            device.username = creds.get("username") or getattr(device, "username", None)
            device.password = creds.get("password") or getattr(device, "password", None)
            device.enable = creds.get("enable") or getattr(device, "enable", None)
        except Exception as e:
            db.add(JobLog(job_id=job.id, attempt_id=attempt.id, output=f"Secret fetch failed: {e}", exit_code=2))
            job.status = "FAILED"
            db.add(job)
            db.commit()
            return {"status": "FAILED", "reason": "secret_fetch_failed", "error": str(e)}

        # --- Mark job as RUNNING ---
        job.status = "RUNNING"
        attempt.started_at = datetime.utcnow()
        db.add(job)
        db.add(attempt)
        db.commit()

        # --- 1) Snapshot running-config ---
        code, running_config = fetch_running_config(device)
        if code != 0:
            msg = f"Snapshot failed: {running_config}"
            db.add(JobLog(job_id=job.id, attempt_id=attempt.id, output=msg, exit_code=2))
            job.status = "FAILED"
            db.add(job)
            db.commit()
            # observe metrics
            if job_execution_seconds:
                try:
                    job_execution_seconds.observe(time.time() - start_time)
                except Exception:
                    pass
            return {"status": "FAILED", "reason": "snapshot_failed", "output": running_config}

        # --- Save snapshot to filesystem + DB record ---
        snapshot_path = save_snapshot_to_fs(device.id, running_config)
        snap_record = ConfigSnapshot(device_id=device.id, filename=snapshot_path, content=running_config)
        db.add(snap_record)
        db.commit()

        # --- 2) Apply config ---
        if not config_lines:
            db.add(JobLog(job_id=job.id, attempt_id=attempt.id, output="No config_lines provided", exit_code=1))
            job.status = "FAILED"
            db.add(job)
            db.commit()
            if job_execution_seconds:
                try:
                    job_execution_seconds.observe(time.time() - start_time)
                except Exception:
                    pass
            return {"status": "FAILED", "reason": "no_config_lines"}

        apply_exit, apply_output = apply_config(device, config_lines)
        db.add(
            JobLog(
                job_id=job.id,
                attempt_id=attempt.id,
                output=f"Apply output:\n{apply_output}",
                exit_code=apply_exit,
            )
        )
        db.commit()

        # If apply returned non-zero high-level error, treat as failed and attempt rollback
        if apply_exit != 0:
            # Attempt rollback immediately from snapshot
            rb_exit, rb_output = rollback_from_snapshot(device, snapshot_path)
            db.add(
                JobLog(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    output=f"Rollback output (after failed apply):\n{rb_output}",
                    exit_code=rb_exit,
                )
            )
            job.status = "FAILED"
            attempt.completed_at = datetime.utcnow()
            attempt.exit_code = apply_exit or 1
            db.add(job)
            db.add(attempt)
            db.commit()
            if job_execution_seconds:
                try:
                    job_execution_seconds.observe(time.time() - start_time)
                except Exception:
                    pass
            return {"status": "FAILED", "reason": "apply_failed", "apply_exit": apply_exit, "apply_output": apply_output}

        # --- 3) Verify ---
        ok, verify_output = verify_config(device, verify_commands or [])
        db.add(
            JobLog(
                job_id=job.id,
                attempt_id=attempt.id,
                output=f"Verify output:\n{verify_output}",
                exit_code=(0 if ok else 1),
            )
        )
        db.commit()

        if not ok:
            # Verification failed — rollback
            rb_exit, rb_output = rollback_from_snapshot(device, snapshot_path)
            db.add(
                JobLog(
                    job_id=job.id,
                    attempt_id=attempt.id,
                    output=f"Rollback output (after verify failure):\n{rb_output}",
                    exit_code=rb_exit,
                )
            )
            job.status = "FAILED"
            attempt.completed_at = datetime.utcnow()
            attempt.exit_code = 1
            db.add(job)
            db.add(attempt)
            db.commit()
            if job_execution_seconds:
                try:
                    job_execution_seconds.observe(time.time() - start_time)
                except Exception:
                    pass
            return {"status": "FAILED", "reason": "verify_failed", "verify_output": verify_output, "rollback_exit": rb_exit}

        # --- SUCCESS path ---
        job.status = "SUCCESS"
        attempt.completed_at = datetime.utcnow()
        attempt.exit_code = 0
        db.add(job)
        db.add(attempt)
        db.commit()

        if job_execution_seconds:
            try:
                job_execution_seconds.observe(time.time() - start_time)
            except Exception:
                pass

        return {"status": "SUCCESS", "job_id": job.id}

    except Exception as e:
        # Log full traceback to JobLog and mark job failed
        msg = f"Worker exception: {e}\n{traceback.format_exc()}"
        try:
            db.add(JobLog(job_id=job_id, attempt_id=attempt_id, output=msg, exit_code=1))
        except Exception:
            # if even logging fails, swallow to avoid crash loop
            pass

        try:
            job = db.query(JobDB).filter(JobDB.id == job_id).one_or_none()
            if job:
                job.status = "FAILED"
                db.add(job)
        except Exception:
            pass

        db.commit()
        if job_execution_seconds:
            try:
                job_execution_seconds.observe(time.time() - start_time)
            except Exception:
                pass
        return {"status": "FAILED", "error": str(e)}

    finally:
        try:
            db.close()
        except Exception:
            pass
