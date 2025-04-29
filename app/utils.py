import os
import httpx
from bs4 import BeautifulSoup
import requests
from fastapi import HTTPException
from passlib.context import CryptContext
from typing_extensions import Optional

from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:Optional[str]) -> Optional[str]:
    return pwd_context.hash(password)

def verify_password(plain_password:Optional[str], hashed_password: Optional[str]) -> Optional[bool]:
    return pwd_context.verify(plain_password, hashed_password)

def verify_token_validity(token: str, BASE_URL: str = os.getenv("BASE_URL")):
    me_url = f"{BASE_URL}/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(me_url, headers=headers)

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Токен истек или недействителен.")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Неизвестная ошибка при проверке токена.")
    return response.json()  # Возвращаем информацию о пользователе, если токен валиден

# Вместо класса Enum просто определяем список допустимых типов
ALLOWED_LINK_TYPES = ["website", "book", "article", "music", "video"]
DEFAULT_LINK_TYPE = "website"


def normalize_link_type(og_type: Optional[str]) -> str:
    """Приводит og:type к одному из допустимых значений"""
    if not og_type:
        return DEFAULT_LINK_TYPE
    # Берем только первую часть до точки (на случай video.other)
    type_value = og_type.lower().split('.')[0]
    # Проверяем, есть ли такое значение в разрешенных типах
    return type_value if type_value in ALLOWED_LINK_TYPES else DEFAULT_LINK_TYPE

def get_metadata_from_link(url: Optional[str]):
    """
    Извлекает метаданные страницы (Open Graph или стандартные meta-теги).
    Возвращает словарь, который можно передать в LinkCreate.
    """
    if not url:
        raise HTTPException(status_code=400, detail="Invalid URL.")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        with httpx.Client() as client:  # Changed from AsyncClient to Client since your route isn't async
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "html.parser")

        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_description = soup.find("meta", attrs={"property": "og:description"})
        og_image = soup.find("meta", attrs={"property": "og:image"})
        og_type = soup.find("meta", attrs={"property": "og:type"})

        meta_title = soup.find("title")
        meta_description = soup.find("meta", attrs={"name": "description"})  # Fixed property to name

        link_type = DEFAULT_LINK_TYPE  # Значение по умолчанию
        if og_type:
            link_type = normalize_link_type(og_type.get("content"))

        result = {
            "title": og_title["content"] if og_title else meta_title.text if meta_title else url,
            "url": url,
            "description": og_description["content"] if og_description else meta_description["content"] if meta_description else None,
            "image": og_image["content"] if og_image else None,
            "type": link_type,
        }

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))