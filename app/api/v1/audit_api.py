from fastapi import APIRouter

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/")
async def audit_root():
    return {"status": "ok", "message": "audit API placeholder"}
