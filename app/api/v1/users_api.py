from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="List all users")
def list_users():
    return {"message": "users endpoint working"}
