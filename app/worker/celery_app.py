# app/worker/celery_app.py

from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime
import traceback
import time

# Correct absolute imports (Docker-safe)
from app.metrics import jobs_pushed_total, job_execution_seconds
from app.db.database import SessionLocal
from app.models.job import JobDB, JobAttempt, JobLog
from app.models.device import DeviceDB
from app.models.snapshot import ConfigSnapshot
from app.core.config import settings
from app.utils.secrets import get_secret

# Deployment utilities
from app.utils.deploy import (
    save_snapshot_to_fs,
    fetch_running_config,
    apply_config,
    verify_config,
    rollback_from_snapshot
)

# Celery instance
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)


@celery_app.task(bind=True, name="app.worker.celery_app.push_config_job")
def push_config_job(self, job_id: int, attempt_id: int, config_lines: list, verify_commands: list = None):
    db: Session = SessionLocal()

    # Metrics start
    jobs_pushed_total.inc()
    start_time = time.time()

    try:
        job = db.query(JobDB).get(job_id)
        attempt = db.query(JobAttempt).get(attempt_id)

        if not job or not attempt:
            return {"status": "MISSING"}

        device = db.query(DeviceDB).get(job.device_id)
        if not device:
            raise Exception("Device not found")

        # ----------- 🔐 Fetch credentials ------------
        creds = get_secret(device.credentials_ref)
        device.username = creds.get("username")
        device.password = creds.get("password")
        device.enable = creds.get("enable")
        # ----------------------------------------------

        # Mark job running
        job.status = "RUNNING"
        attempt.started_at = datetime.utcnow()
        db.add(job)
        db.add(attempt)
        db.commit()

        # 1) Snapshot
        code, running_config = fetch_running_config(device)
        if code != 0:
            msg = f"Snapshot failed: {running_config}"
            db.add(JobLog(job_id=job.id, attempt_id=attempt.id, output=msg, exit_code=2))
            job.status = "FAILED"
            db.commit()
            return {"status": "FAILED", "reason": "snapshot_failed"}

        snapshot_path = save_snapshot_to_fs(device.id, running_config)
        snap_record = ConfigSnapshot(
            device_id=device.id,
            filename=snapshot_path,
            content=running_config
        )
        db.add(snap_record)
        db.commit()

        # 2) Apply config
        apply_exit, apply_output = apply_config(device, config_lines)
        db.add(JobLog(
            job_id=job.id,
            attempt_id=attempt.id,
            output=f"Apply output:\n{apply_output}",
            exit_code=apply_exit
        ))
        db.commit()

        # 3) Verify
        ok, verify_output = verify_config(device, verify_commands or [])
        db.add(JobLog(
            job_id=job.id,
            attempt_id=attempt.id,
            output=f"Verify output:\n{verify_output}",
            exit_code=(0 if ok else 1)
        ))
        db.commit()

        if not ok:
            rb_exit, rb_output = rollback_from_snapshot(device, snapshot_path)
            db.add(JobLog(
                job_id=job.id,
                attempt_id=attempt.id,
                output=f"Rollback output:\n{rb_output}",
                exit_code=rb_exit
            ))
            job.status = "FAILED"
            attempt.completed_at = datetime.utcnow()
            attempt.exit_code = 1
            db.commit()

            job_execution_seconds.observe(time.time() - start_time)
            return {"status": "FAILED", "rollback": True}

        # SUCCESS
        job.status = "SUCCESS"
        attempt.completed_at = datetime.utcnow()
        attempt.exit_code = 0
        db.commit()

        job_execution_seconds.observe(time.time() - start_time)
        return {"status": "SUCCESS"}

    except Exception as e:
        msg = f"Worker exception: {e}\n{traceback.format_exc()}"
        db.add(JobLog(job_id=job_id, attempt_id=attempt_id, output=msg, exit_code=1))

        job = db.query(JobDB).get(job_id)
        if job:
            job.status = "FAILED"
            db.add(job)

        db.commit()

        job_execution_seconds.observe(time.time() - start_time)
        return {"status": "FAILED", "error": str(e)}

    finally:
        db.close()
