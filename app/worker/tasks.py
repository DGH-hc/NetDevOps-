from app.worker.celery_app import celery_app
from app.db.database import SessionLocal
from app.models.job import Job, JobAttempt, JobLog
from datetime import datetime

@celery_app.task(bind=True)
def run_job(self, job_id):
    db = SessionLocal()

    job = db.query(Job).get(job_id)
    job.status = "RUNNING"
    db.add(job)
    db.commit()

    attempt = JobAttempt(
        job_id=job_id,
        attempt_no=1,
        started_at=datetime.utcnow()
    )
    db.add(attempt)
    db.commit()

    try:
        log_output = "Executing job... (placeholder)\nJob complete."
        exit_code = 0

        log = JobLog(
            job_id=job_id,
            attempt_id=attempt.id,
            output=log_output,
            exit_code=exit_code
        )
        db.add(log)

        job.status = "SUCCESS"
        attempt.completed_at = datetime.utcnow()
        attempt.exit_code = exit_code

        db.commit()
        return {"status": "SUCCESS"}

    except Exception as e:
        log = JobLog(
            job_id=job_id,
            attempt_id=attempt.id,
            output=str(e),
            exit_code=1
        )
        db.add(log)
        db.commit()

        job.status = "FAILED"
        db.add(job)
        db.commit()
        return {"status": "FAILED"}

    finally:
        db.close()
