from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import Device, User, Job  # adjust these imports to your actual model names
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    # Create all tables
    logger.info("Creating tables (if they don't exist)...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Example default user
        user = User(
            username="admin",
            email="admin@netdevops.com",
            password="admin123"
        )

        # Example devices
        devices = [
            Device(name="Router-1", type="Cisco", status="Active"),
            Device(name="Switch-1", type="Juniper", status="Inactive"),
        ]

        # Example jobs
        jobs = [
            Job(name="Backup Configuration", status="Pending"),
            Job(name="Software Update", status="Completed"),
        ]

        # Add only if not already seeded
        if not db.query(User).first():
            logger.info("Seeding users, devices, and jobs...")
            db.add(user)
            db.add_all(devices)
            db.add_all(jobs)
            db.commit()
        else:
            logger.info("Database already seeded. Skipping.")

    except Exception as e:
        logger.error(f"Error while seeding: {e}")
        db.rollback()
    finally:
        db.close()
        logger.info("Seeding complete.")

if __name__ == "__main__":
    seed_database()
