from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="List all jobs")
def list_jobs():
    return {"message": "jobs endpoint working"}
