# app/worker/tasks.py

from datetime import datetime
from app.db.database import SessionLocal
from app.models.job import JobDB, JobAttempt, JobLog

# -----------------------------
# Celery Import (SAFE)
# -----------------------------
try:
    from app.worker.celery_app import celery_app
except ImportError:
    celery_app = None


# -----------------------------
# CORE LOGIC (NO METRICS HERE)
# -----------------------------
def _run_job_impl(job_id: int):
    db = SessionLocal()
    job = None
    attempt = None 

    try:
        job = db.get(JobDB, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = "RUNNING"
        db.commit()

        attempt_no = (
            db.query(JobAttempt)
            .filter(JobAttempt.job_id == job_id)
            .count()
            + 1
        )

        attempt = JobAttempt(
            job_id=job_id,
            attempt_no=attempt_no,
            started_at=datetime.utcnow(),
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        db.add(
            JobLog(
                job_id=job_id,
                attempt_id=attempt.id,
                output="Executing job...\nJob completed successfully.",
                exit_code=0,
            )
        )

        job.status = "SUCCESS"
        attempt.completed_at = datetime.utcnow()
        attempt.exit_code = 0

        db.commit()

        return {"job_id": job_id, "status": "SUCCESS"}

    except Exception as exc:
        try:
            db.add(
                JobLog(
                    job_id=job_id,
                    attempt_id=attempt.id if attempt else None,
                    output=str(exc),
                    exit_code=1,
                )
            )

            if job:
                job.status = "FAILED"

            if attempt:
                attempt.completed_at = datetime.utcnow()
                attempt.exit_code = 1

            db.commit()

        except Exception:
            db.rollback()

        raise

    finally:
        db.close()


# -----------------------------
# CELERY WRAPPER (ALL METRICS HERE)
# -----------------------------
if celery_app:

    @celery_app.task(bind=True, name="app.worker.tasks.run_job")
    def run_job(self, job_id: int):
        # 🔥 CRITICAL: import INSIDE task (ensures correct process context)
        from app.metrics import get_metrics

        # 🔥 CRITICAL: initialize metrics INSIDE execution scope
        metrics = get_metrics(scope="worker")

        # 🔒 HARD GUARD
        assert "pushed" not in metrics, "Worker must not access pushed metric"

        start_time = datetime.utcnow()

        try:
            result = _run_job_impl(job_id)

            # ✅ increment ONLY on success
            metrics["success"].inc()

            return result

        except Exception:
            # ✅ increment ONLY on failure
            metrics["failed"].inc()
            raise

        finally:
            # 🔥 ALWAYS record duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics["duration"].observe(duration)

else:
    def run_job(job_id: int):
        return _run_job_impl(job_id)