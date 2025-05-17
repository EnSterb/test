from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, delete, insert

from app.routers.auth import get_current_user
from app.database import get_db
from app.models import Links, Collections, t_collection_links
from app.schemas import User, Collection, CollectionUpdate
from app.utils import verify_token_validity

routerCollections = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@routerCollections.get("/get_collections", response_model=list[Collection])
def get_links(user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    """
    Получить список всех коллекций пользователя
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        result = db.execute(select(Collections).where(Collections.user_id == user.id)).scalars().all()
        if not result:
            raise HTTPException(status_code=402, detail="У пользователя нет коллекций")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@routerCollections.get("/get_collection", response_model=Collection)
def get_links(user: User = Depends(get_current_user),
              token: str = Depends(oauth2_scheme),
              name: Optional[str] = None):
    """
    Получить коллекцию по названию

    - **name**: Название коллекции
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        collection = db.execute(
            select(Collections)
            .where(Collections.user_id == user.id)
            .where(Collections.name == name)
        ).scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=400, detail="Коллекция не существует")
        return collection
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@routerCollections.delete("/delete_collection", response_model=Collection)
def delete_collection(user: User = Depends(get_current_user),
                      token: str = Depends(oauth2_scheme),
                      name: Optional[str] = None):
    """
    Удалить коллекцию по названию

    - **name**: Название коллекции
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Collections).where(Collections.name == name).where(Collections.user_id == user.id)
        result = db.execute(stmt).scalar_one_or_none()

        if not result:
            raise HTTPException(status_code=400, detail="Коллекция не существует")

        stmt = delete(Collections).where(Collections.name == name).where(Collections.user_id == user.id)
        result = db.execute(stmt)
        db.commit()
        return {"msg": "Коллекция удалена", "Collections deleted": result.rowcount}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@routerCollections.post("/create_collection", response_model=Collection)
def create_collection(user: User = Depends(get_current_user),
                      token: str = Depends(oauth2_scheme),
                      name: Optional[str] = None,
                      description: Optional[str] = None):
    """
    Создать новую коллекцию

    - **name**: Название коллекции
    - **description**: Описание коллекции
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Collections).where(Collections.name == name)
        collection = db.execute(stmt)
        if collection.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Коллекция с таким названием уже существует")

        new_collection = Collections(
            name=name,
            user_id=user.id,
            description=description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_collection)
        db.commit()
        db.refresh(new_collection)
        return new_collection
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@routerCollections.post("/update_collection", response_model=Collection)
def update_collection(update_data: CollectionUpdate,
                      user: User = Depends(get_current_user),
                      token: str = Depends(oauth2_scheme),
                      name: Optional[str] = None):
    """
    Обновить данные коллекции

    - **name**: Название коллекции
    - **update_data**: Поля для обновления
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Collections).where(Collections.name == name).where(Collections.user_id == user.id)
        collection = db.execute(stmt).scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=400, detail="Коллекция не существует")

        update_dict = update_data.model_dump(exclude_unset=True)
        if "name" in update_dict and len(update_dict["name"]) < 1:
            raise HTTPException(
                status_code=400,
                detail="Название коллекции не может быть пустым"
            )
        for field, value in update_dict.items():
            setattr(collection, field, value)

        collection.updated_at = datetime.utcnow()
        db.merge(collection)
        db.commit()
        db.refresh(collection)
        return collection
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@routerCollections.post("/add_link", response_model=Collection)
def add_link(user: User = Depends(get_current_user),
             token: str = Depends(oauth2_scheme),
             url: Optional[str] = None,
             name: Optional[str] = None):
    """
    Добавить ссылку в коллекцию

    - **url**: URL ссылки
    - **name**: Название коллекции
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Links).where(Links.url == url).where(Links.user_id == user.id)
        link = db.execute(stmt).scalar_one_or_none()
        if not link:
            raise HTTPException(status_code=400, detail="Ссылка не найдена в вашей базе данных")

        collection = db.execute(select(Collections).where(Collections.name == name)).scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=400, detail="Коллекция не существует")

        existing_link = db.execute(
            select(t_collection_links)
            .where(t_collection_links.c.collection_id == collection.id)
            .where(t_collection_links.c.link_id == link.id)
        ).scalar_one_or_none()
        if existing_link:
            raise HTTPException(
                status_code=400,
                detail="Ссылка уже добавлена в эту коллекцию"
            )
        stmt = insert(t_collection_links).values(
            collection_id=collection.id,
            link_id=link.id
        )
        db.execute(stmt)
        db.commit()
        db.refresh(collection)
        return collection
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@routerCollections.post("/remove_link", response_model=Collection)
def delete_link(user: User = Depends(get_current_user),
                token: str = Depends(oauth2_scheme),
                url: Optional[str] = None,
                name: Optional[str] = None):
    """
    Удалить ссылку из коллекции

    - **url**: URL ссылки
    - **name**: Название коллекции
    """
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Links).where(Links.url == url).where(Links.user_id == user.id)
        link = db.execute(stmt).scalar_one_or_none()
        if not link:
            raise HTTPException(status_code=400, detail="Ссылка не найдена в вашей базе данных")

        collection = db.execute(select(Collections).where(Collections.name == name)).scalar_one_or_none()
        if not collection:
            raise HTTPException(status_code=400, detail="Коллекция не существует")

        link_in_collection = db.execute(
            select(t_collection_links)
            .where(t_collection_links.c.collection_id == collection.id)
            .where(t_collection_links.c.link_id == link.id)
        ).scalar_one_or_none()

        if not link_in_collection:
            raise HTTPException(
                status_code=400,
                detail="Ссылка не найдена в указанной коллекции"
            )

        stmt = delete(t_collection_links).where(
            (t_collection_links.c.collection_id == collection.id) &
            (t_collection_links.c.link_id == link.id)
        )
        db.execute(stmt)
        db.commit()
        db.refresh(collection)
        return collection
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
