from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.device import DeviceDB
from app.schemas.device import DeviceCreate
from app.utils.auth import get_current_user
from app.db.database import get_db

router = APIRouter(prefix="/devices", tags=["Devices"])

# ---------------------------
# ➕ Add Device (Admin Only)
# ---------------------------
@router.post("/")
def add_device(device: DeviceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can add devices")

    new_device = DeviceDB(name=device.name, ip=device.ip)
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return {"message": f"✅ Device '{device.name}' added by {current_user.username}"}

# ---------------------------
# 📋 Get All Devices
# ---------------------------
@router.get("/")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(DeviceDB).all()
    return {"devices": [{"id": d.id, "name": d.name, "ip": d.ip} for d in devices]}
