from fastapi import APIRouter

router = APIRouter()

@router.get("/devices")
def list_devices():
    return {"message": "devices endpoint works"}
