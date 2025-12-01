from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Audit logs")
def list_audit_logs():
    return {"message": "audit endpoint working"}
