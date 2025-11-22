# app/models/device.py

from sqlalchemy import Column, Integer, String
from db.database import Base

class DeviceDB(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    ip = Column(String(100), nullable=False)
    platform = Column(String(100), nullable=False)  # e.g. cisco_ios, juniper, etc.

    # 🔐 Vault reference replaces plaintext credentials
    credentials_ref = Column(String(255), nullable=False)

    port = Column(Integer, default=22)
