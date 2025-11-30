from fastapi import APIRouter
from app.api.v1.routers import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
