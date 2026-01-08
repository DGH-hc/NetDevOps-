# app/worker/tasks.py

from datetime import datetime
from app.db.database import SessionLocal
from app.models.job import JobDB, JobAttempt, JobLog

try:
    from app.worker.celery_app import celery_app
except ImportError:
    celery_app = None


@celery_app.task(bind=True, name="run_job")
def run_job(self, job_id: int):
    if celery_app is None:
        raise RuntimeError("Celery is not enabled in this environment")

    db = SessionLocal()
    job = None
    attempt = None

    try:
        job = db.get(JobDB, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = "RUNNING"
        db.add(job)
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

        db.add(job)
        db.add(attempt)
        db.commit()

        return {"job_id": job_id, "status": "SUCCESS"}

    except Exception as exc:
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
            db.add(job)

        if attempt:
            attempt.completed_at = datetime.utcnow()
            attempt.exit_code = 1
            db.add(attempt)

        db.commit()
        raise

    finally:
        db.close()
