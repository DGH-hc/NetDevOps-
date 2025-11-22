from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from db.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100), nullable=True)
    role = Column(String(50), nullable=True)
    action = Column(String(200), nullable=False)
    target = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # FIXED: cannot use "metadata"
    details = Column(JSON, nullable=True)
