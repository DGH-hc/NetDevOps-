from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.models.user import UserDB
from app.utils.auth import get_password_hash, verify_password, create_access_token
from app.db.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

# ---------------------------
# 👤 Register User
# ---------------------------
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = get_password_hash(user.password)
    new_user = UserDB(username=user.username, hashed_password=hashed_pw, role=user.role)
    db.add(new_user)
    db.commit()
    return {"message": f"✅ User '{user.username}' registered as {user.role}"}

# ---------------------------
# 🔐 Login and Token Creation
# ---------------------------
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
