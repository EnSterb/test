import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException

from sqlalchemy import delete, select

from app.models import TempUsers, Users
from app.database import get_db
from app.send_email import send_email
import os


def create_temp_user(email: str, password_hash: str):
    db = next(get_db())
    try:
        # Удаляем старые записи для этого email
        db.execute(
            delete(TempUsers)
            .where(TempUsers.email == email)
        )

        # Создаем новую временную запись
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        temp_user = TempUsers(
            email=email,
            password_hash=password_hash,
            token=token,
            expires_at=expires_at
        )

        db.add(temp_user)
        db.commit()

        return token
    finally:
        db.close()


def send_verification_email(email: str, token: str):
    verification_url = f"{os.getenv("BASE_URL")}/auth/verify_email?token={token}"

    subject = "Подтверждение регистрации"
    body = f"""
    Добро пожаловать!
    Пожалуйста, подтвердите ваш email, перейдя по ссылке:
    {verification_url}

    Ссылка действительна 30 минут.
    """

    send_email(
        email_from=os.getenv("GMAIL"),
        email_password=os.getenv("GMAILPASSWORD"),
        email_to=email,
        subject=subject,
        body=body
    )


def verify_token_and_register(token: str):
    db = next(get_db())
    try:
        # Находим временного пользователя
        temp_user = db.execute(
            select(TempUsers)
            .where(TempUsers.token == token)
            .where(TempUsers.expires_at > datetime.utcnow())
        ).scalar_one_or_none()

        if not temp_user:
            raise HTTPException(status_code=400, detail="Token expired")

        # Проверяем, не зарегистрирован ли уже email
        existing_user = db.execute(
            select(Users)
            .where(Users.email == temp_user.email)
        ).scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Создаем настоящего пользователя
        new_user = Users(
            email=temp_user.email,
            password_hash=temp_user.password_hash
        )

        db.add(new_user)
        db.delete(temp_user)  # Удаляем временную запись
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=(e))
    finally:
        db.close()