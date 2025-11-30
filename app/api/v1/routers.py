from fastapi import APIRouter

from .audit_api import router as audit_router
from .devices_api import router as devices_router
from .jobs_api import router as jobs_router
from .users_api import router as users_router
from .health import router as health_router

router = APIRouter()
router.include_router(audit_router, prefix="/audit", tags=["audit"])
router.include_router(devices_router, prefix="/devices", tags=["devices"])
router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(health_router, tags=["health"])
