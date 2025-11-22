# app/api/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import verify_token

# Token entrypoint (standard OAuth2 bearer token in FastAPI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT and returns its payload.
    """
    try:
        token_data = verify_token(token)
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles):
    """
    Dependency that enforces RBAC based on token 'role'.
    Usage:
        Depends(require_role("admin", "operator"))
    """
    def inner(token_data = Depends(get_current_user)):
        role = token_data.get("role")

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{role}' not permitted"
            )

        return token_data

    return inner
