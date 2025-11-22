from pydantic import BaseModel

# ---------------------------
# 📦 Schema for Device Creation
# ---------------------------
class DeviceCreate(BaseModel):
    name: str
    ip: str


# ---------------------------
# 🧾 Schema for Job Log Output
# ---------------------------
class JobLog(BaseModel):
    id: int
    device_ip: str
    command: str
    result: str

    class Config:
        orm_mode = True  # allows reading data directly from SQLAlchemy models
