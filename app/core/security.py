# app/core/security.py

from datetime import datetime, timedelta
from typing import Optional, Dict

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# -----------------------------
# Password utilities
# -----------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# REQUIRED FOR BACKWARD COMPATIBILITY
# (Your app uses get_password_hash, so we map it to hash_password)
def get_password_hash(password: str) -> str:
    return hash_password(password)


# -----------------------------
# JWT: Create access token
# -----------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})

    # Default role injection
    if "role" not in to_encode:
        to_encode["role"] = "operator"

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


# -----------------------------
# JWT: Verify token (used in dependencies)
# -----------------------------
def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise Exception(f"Invalid token: {e}")
