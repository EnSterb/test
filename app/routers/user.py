import datetime
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select

from app.routers.auth import get_current_user
from app.database import get_db
from app.models import Users, PasswordResetToken
from app.send_email import send_password_reset_email
from app.utils import hash_password, verify_password, verify_token_validity

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post('/change_password')
def change_password(
        current_user: Users = Depends(get_current_user),
        token: str = Depends(oauth2_scheme),
        new_password1: Optional[str] = None,
        new_password2: Optional[str] = None
):
    """
    Изменение пароля пользователя.
    """
    db = next(get_db())
    verify_token_validity(token)

    if len(new_password1) < 8:
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 8 символов.")

    if new_password1 != new_password2:
        raise HTTPException(status_code=400, detail="Новый пароль и подтверждение не совпадают.")

    if verify_password(new_password1, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Новый пароль не должен совпадать со старым.")

    hashed_new_password = hash_password(new_password1)
    if not hashed_new_password:
        raise HTTPException(status_code=400, detail="Не удалось захешировать новый пароль.")

    try:
        current_user.password_hash = hashed_new_password
        db.merge(current_user)
        db.commit()
        return {"message": "Пароль успешно изменён"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка при обновлении пароля.")
    finally:
        db.close()


@router.post("/request-password-reset")
async def request_password_reset(email: str):
    """
    Запрос на сброс пароля по email.
    """
    db = next(get_db())
    try:
        user = db.execute(
            select(Users).where(Users.email == email)
        ).scalar_one_or_none()

        if not user:
            return {"message": "Если пользователь с таким email существует, ссылка для сброса отправлена."}

        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()

        reset_link = f"{os.getenv('BASE_URL')}/user/reset-password?token={token}"
        send_password_reset_email(email, reset_link)

        return {"message": "Если пользователь с таким email существует, ссылка для сброса отправлена.", "token": token}
    finally:
        db.close()


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Сброс пароля по токену.
    """
    db = next(get_db())
    try:
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Пароли не совпадают."
            )

        reset_token = db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token == request.token)
            .where(PasswordResetToken.expires_at > datetime.datetime.utcnow())
        ).scalar_one_or_none()

        if not reset_token:
            raise HTTPException(
                status_code=400,
                detail="Неверный или просроченный токен."
            )

        user = db.execute(
            select(Users).where(Users.id == reset_token.user_id)
        ).scalar_one_or_none()

        if user:
            user.password_hash = hash_password(request.new_password)
            db.delete(reset_token)
            db.commit()
            return {"message": "Пароль успешно сброшен."}

        raise HTTPException(
            status_code=400,
            detail="Пользователь не найден."
        )
    finally:
        db.close()


@router.get("/validate-reset-token")
async def validate_reset_token(token: str):
    """
    Проверка действительности токена сброса пароля.
    """
    db = next(get_db())
    try:
        reset_token = db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .where(PasswordResetToken.expires_at > datetime.datetime.utcnow())
        ).scalar_one_or_none()

        if not reset_token:
            raise HTTPException(
                status_code=400,
                detail="Неверный или просроченный токен."
            )

        return {"valid": True, "user_id": reset_token.user_id}
    finally:
        db.close()
