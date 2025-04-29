import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, APIRouter
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db, user_exists  # если get_db в другом файле
from app.email_verification import send_verification_email, create_temp_user, \
    verify_token_and_register
from app.models import Users
from app.schemas import UserCreate
from app.utils import verify_password, hash_password

load_dotenv(".env")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


def register_user(email: str, password: str):
    db = next(get_db())
    try:
        # Проверяем, не зарегистрирован ли уже email
        if user_exists(email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Создаем временную запись
        hashed_password = hash_password(password)
        token = create_temp_user(email, hashed_password)

        # Отправляем письмо с подтверждением
        send_verification_email(email, token)

        return {"message": "Verification email sent. Please check your email.", "token": token}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/verify_email")
def verify_email(token: Optional[str] = ...):
    if verify_token_and_register(token):
        return {"message": "Email successfully verified and account created"}
    raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post('/register/', response_model=dict)
def register(user_data: UserCreate):
    return register_user(user_data.email, user_data.password)


SECRET_KEY = os.getenv("SECRET_KEY")  # храни в .env!
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 30 мин

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise credentials_exception

    stmt = select(Users).where(Users.id==user_id)
    user = db.execute(stmt).scalar()
    if user is None:
        raise credentials_exception
    return user
