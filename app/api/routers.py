from fastapi import APIRouter
from app.api.v1 import health
from app.api.v1 import jobs_api   # ← THIS WAS MISSING

router = APIRouter()

router.include_router(health.router)
router.include_router(jobs_api.router, prefix="/v1")