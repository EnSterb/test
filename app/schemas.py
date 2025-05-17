from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, Field


# === LINKS ===

class LinkBase(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    image: Optional[str] = None
    type: Optional[str] = 'website'


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    title: Optional[str] = ""
    description: Optional[str] = ""
    image: Optional[str] = ""
    type: Optional[str] = "website"


class Link(LinkBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = datetime.utcnow()
    updated_at: Optional[datetime] = datetime.utcnow()

    class Config:
        from_attributes = True


# === COLLECTIONS ===

class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionCreate(CollectionBase):
    link_: Optional[List[Link]] = []


class CollectionCreateNested(CollectionBase):
    links: Optional[List[LinkCreate]] = []  # вложенное создание ссылок


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = datetime.utcnow()


class Collection(CollectionBase):
    id: int
    user_id: int
    links: List[Link] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @validator("links", pre=True)
    def handle_links_loading(cls, v):
        if v is None:
            return []
        return list(v)

# === USERS ===

class UserBase(BaseModel):
    email: EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator("email")
    def validate_email_format(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Неверный формат email: должен содержать '@' и домен")
        return v

    @validator("password")
    def validate_password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return v


class UserCreateNested(UserBase):
    password: str
    collections: Optional[List[CollectionCreateNested]] = []
    links: Optional[List[LinkCreate]] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    collections: List[Collection] = []
    links: List[Link] = []

    class Config:
        from_attributes = True
