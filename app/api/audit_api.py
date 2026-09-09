# app/api/audit_api.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.database import get_db
from app.models.audit import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", dependencies=[Depends(require_role("admin", "auditor"))])
def list_audit_events(db: Session = Depends(get_db)):
    return db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).all()
