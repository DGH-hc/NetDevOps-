# app/worker/celery_app.py 

import logging
import os
import time
import traceback
from datetime import datetime
from typing import List, Optional


from celery import Celery
from sqlalchemy.orm import Session
from celery.exceptions import MaxRetriesExceededError 
from app.metrics import get_metrics 

logger = logging.getLogger("netdevops.worker")

# ==========================================================
# ENV CONFIG
# ==========================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# ==========================================================
# CELERY INSTANCE
# ==========================================================
celery_app = Celery(
    "netdevops",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_default_queue="celery",
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.worker.celery_app.test_task": {"queue": "celery"},
        "app.worker.celery_app.placeholder_job": {"queue": "celery"},
        "app.worker.celery_app.push_config_job": {"queue": "celery"},
        "app.worker.celery_app.fail_task": {"queue": "celery"},
    },
    task_soft_time_limit=300,
    task_time_limit=600,
)

# ==========================================================
# CRITICAL :FORCE TASK REGISTRATION
# ==========================================================
import app.worker.tasks 


# ==========================================================
# IMPORTS
# ==========================================================
from app.db.database import SessionLocal
from app.utils.secrets import get_secret
from app.utils.deploy import (
    fetch_running_config,
    save_snapshot_to_fs,
    apply_config,
    verify_config,
    rollback_from_snapshot,
)
from app.models.job import JobDB, JobAttempt
from app.models.device import DeviceDB

# ==========================================================
# TEST TASK
# ==========================================================
@celery_app.task(name="app.worker.celery_app.test_task")
def test_task():
    metrics = get_metrics(scope="worker")

    # 🔒 HARD GUARD
    assert "pushed" not in metrics

    start_time = time.time()
    logger.warning("🔥 TASK RECEIVED")

    try:
        time.sleep(1)
        logger.warning("✅ TASK SUCCESS")

        metrics["success"].inc()
        return {"status": "SUCCESS"}

    except Exception as e:
        logger.error(f"❌ TASK FAILED: {e}")
        metrics["failed"].inc()
        return {"status": "FAILED"}

    finally:
        metrics["duration"].observe(time.time() - start_time)


# ==========================================================
# DB TEST TASK
# ==========================================================
@celery_app.task(bind=True, name="app.worker.celery_app.placeholder_job")
def placeholder_job(self, job_id: int):
    db: Session = SessionLocal()

    try:
        db.execute("SELECT 1")
        return {"status": "OK", "job_id": job_id}

    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

    finally:
        db.close()


# ==========================================================
# PRODUCTION JOB
# ==========================================================
@celery_app.task(bind=True, name="app.worker.celery_app.push_config_job")
def push_config_job(
    self,
    job_id: int,
    attempt_id: int,
    config_lines: Optional[List[str]],
    verify_commands: Optional[List[str]] = None,
):
    metrics = get_metrics(scope="worker")

    # 🔒 HARD GUARD
    assert "pushed" not in metrics

    db: Session = SessionLocal()
    start_time = time.time()

    try:
        job = db.query(JobDB).filter(JobDB.id == job_id).one_or_none()
        attempt = db.query(JobAttempt).filter(JobAttempt.id == attempt_id).one_or_none()

        if not job or not attempt:
            metrics["failed"].inc()
            return {"status": "FAILED", "reason": "not_found"}

        device = db.query(DeviceDB).filter(DeviceDB.id == job.device_id).one_or_none()
        if not device:
            metrics["failed"].inc()
            return {"status": "FAILED", "reason": "device_not_found"}

        creds = get_secret(device.credentials_ref) if device.credentials_ref else {}
        device.username = creds.get("username", device.username)
        device.password = creds.get("password", device.password)

        job.status = "RUNNING"
        attempt.started_at = datetime.utcnow()
        db.commit()

        code, running_config = fetch_running_config(device)
        if code != 0:
            metrics["failed"].inc()
            return {"status": "FAILED", "reason": "snapshot_failed"}

        snapshot_path = save_snapshot_to_fs(device.id, running_config)

        apply_exit, _ = apply_config(device, config_lines or [])
        if apply_exit != 0:
            rollback_from_snapshot(device, snapshot_path)
            metrics["failed"].inc()
            return {"status": "FAILED", "reason": "apply_failed"}

        ok, _ = verify_config(device, verify_commands or [])
        if not ok:
            rollback_from_snapshot(device, snapshot_path)
            metrics["failed"].inc()
            return {"status": "FAILED", "reason": "verify_failed"}

        job.status = "SUCCESS"
        attempt.completed_at = datetime.utcnow()
        attempt.exit_code = 0
        db.commit()

        metrics["success"].inc()
        return {"status": "SUCCESS"}

    except Exception as e:
        logger.error(traceback.format_exc())
        metrics["failed"].inc()
        return {"status": "FAILED", "error": str(e)}

    finally:
        metrics["duration"].observe(time.time() - start_time)
        db.close()


# ==========================================================
# FAILURE TASK (CRITICAL FOR GATE 5)
# ==========================================================
@celery_app.task(
    bind=True,
    retry_backoff=False,
    max_retries=3,
    default_retry_delay=1,
    name="app.worker.celery_app.fail_task",
)
def fail_task(self):
    from app.metrics import get_metrics
    import time

    metrics = get_metrics(scope="worker")

    assert "pushed" not in metrics

    start_time = time.time()

    attempt = self.request.retries
    print(f"💣 FAIL TASK TRIGGERED | attempt={attempt}")

    try:
        raise Exception("Intentional failure for testing")

    except Exception as e:
        if attempt >= self.max_retries:
            print("❌ FINAL FAILURE REACHED")
            metrics["failed"].inc()
            raise e
        else:
            raise self.retry(exc=e)

    finally:
        metrics["duration"].observe(time.time() - start_time)