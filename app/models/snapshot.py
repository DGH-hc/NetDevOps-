# app/models/snapshot.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text
from app.db.database import Base
from sqlalchemy.orm import relationship

class ConfigSnapshot(Base):
    __tablename__ = "config_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    content = Column(Text, nullable=True)        # optional: store config in DB too
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("DeviceDB", backref="snapshots")
