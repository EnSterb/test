import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException

from sqlalchemy import delete, select

from app.models import TempUsers, Users
from app.database import get_db
from app.send_email import send_email
import os


def create_temp_user(email: str, password_hash: str):
    """
    Создает временного пользователя с токеном для подтверждения.
    Удаляет старые записи для данного email.
    """
    db = next(get_db())
    try:
        db.execute(
            delete(TempUsers)
            .where(TempUsers.email == email)
        )

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
    """
    Отправляет email с ссылкой для подтверждения регистрации.
    """
    verification_url = f"{os.getenv('BASE_URL')}/auth/verify_email?token={token}"

    subject = "Подтверждение регистрации"
    html_body = f"""
    <html>
        <body>
            <p>Добро пожаловать!</p>
            <p>Пожалуйста, подтвердите вашу почту, перейдя по ссылке ниже:</p>
            <p><a href="{verification_url}">Для подтверждения регистрации нажмите здесь</a></p>
            <p>Ссылка действительна 30 минут.</p>
        </body>
    </html>
    """

    send_email(
        email_from=os.getenv("GMAIL"),
        email_password=os.getenv("GMAILPASSWORD"),
        email_to=email,
        subject=subject,
        body=html_body,
        is_html=True
    )


def verify_token_and_register(token: str):
    """
    Проверяет токен подтверждения, регистрирует пользователя и удаляет временную запись.
    """
    db = next(get_db())
    try:
        temp_user = db.execute(
            select(TempUsers)
            .where(TempUsers.token == token)
            .where(TempUsers.expires_at > datetime.utcnow())
        ).scalar_one_or_none()

        if not temp_user:
            raise HTTPException(status_code=400, detail="Токен истек")

        existing_user = db.execute(
            select(Users)
            .where(Users.email == temp_user.email)
        ).scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

        new_user = Users(
            email=temp_user.email,
            password_hash=temp_user.password_hash
        )

        db.add(new_user)
        db.delete(temp_user)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
