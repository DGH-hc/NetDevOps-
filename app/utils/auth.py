from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.user import UserDB
from db.database import get_db
from core.security import verify_password, get_password_hash

# -------------------------------
# 🔐 JWT Configuration
# -------------------------------
SECRET_KEY = "super-secure-and-random-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# -------------------------------
# 🔑 Password Utilities
# -------------------------------
def verify_password(plain_password, hashed_password):
    """Verify hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash plain password"""
    return pwd_context.hash(password)


# -------------------------------
# 🎟️ JWT Token Utilities
# -------------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generate access token for authentication"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------------
# 👤 User Authentication
# -------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return current user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    db: Session = SessionLocal()
    user = db.query(UserDB).filter(UserDB.username == username).first()
    db.close()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user
