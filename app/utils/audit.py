# app/utils/audit.py

from functools import wraps
from fastapi import Request, Depends

from app.db.database import SessionLocal
from app.models.audit import AuditEvent
from app.api.deps import get_current_user


def audit(action: str, target: str = None):
    """
    Decorator for logging audit events.
    Automatically logs: user, role, action, endpoint, timestamp.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, token_data = Depends(get_current_user), **kwargs):
            db = SessionLocal()

            event = AuditEvent(
                user_id = token_data.get("user_id"),
                username = token_data.get("username"),
                role = token_data.get("role"),
                action = action,
                endpoint = str(request.url),
                target = target
            )

            db.add(event)
            db.commit()

            return await func(*args, request=request, **kwargs)

        return wrapper
    return decorator
