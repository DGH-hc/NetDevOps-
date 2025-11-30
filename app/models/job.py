# app/models/job.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.device import DeviceDB 
from app.db.database import Base

class JobDB(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("JobAttempt", back_populates="job")
    logs = relationship("JobLog", back_populates="job")

class JobAttempt(Base):
    __tablename__ = "job_attempts"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    attempt_no = Column(Integer, nullable=False, default=1)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    exit_code = Column(Integer, nullable=True)

    job = relationship("JobDB", back_populates="attempts")
    logs = relationship("JobLog", back_populates="attempt")

class JobLog(Base):
    __tablename__ = "job_logs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    attempt_id = Column(Integer, ForeignKey("job_attempts.id"), nullable=True)
    output = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB", back_populates="logs")
    attempt = relationship("JobAttempt", back_populates="logs")
