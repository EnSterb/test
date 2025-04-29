import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, delete

from app.auth import get_current_user
from app.database import get_db
from app.models import Links
from app.schemas import User, Link, LinkCreate, LinkUpdate
from app.utils import verify_token_validity, get_metadata_from_link

routerLinks = APIRouter(
    prefix="/links",
    tags=["Links"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@routerLinks.get("/get_links", response_model=list[Link])
def get_links(user:User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    db = next(get_db())
    verify_token_validity(token)
    result = db.execute(select(Links).where(Links.user_id == user.id))
    return result.scalars().all()

@routerLinks.get("/get_link", response_model=Link)
def get_links(user:User = Depends(get_current_user),
              token: str = Depends(oauth2_scheme),
              url:Optional[str] = Query(...)):
    db = next(get_db())
    verify_token_validity(token)
    try:
        result = db.execute(select(Links).where(Links.user_id == user.id).where(Links.url == url)).scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=400, detail="Link does not exist")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@routerLinks.post('/create_link')
def add_url(
        user: User = Depends(get_current_user),
        token: str = Depends(oauth2_scheme),
        url: Optional[str] = None,
):
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Links).where(Links.url == url)
        link = db.execute(stmt)
        if link.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Link already exists")

        metadata = get_metadata_from_link(url)
        link_data = LinkCreate(**metadata)

        user_id = user.id

        new_link = Links(
            title=link_data.title,
            url=link_data.url,
            description=link_data.description,
            image=link_data.image,
            type=link_data.type,
            user_id=user_id,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )

        db.add(new_link)
        db.commit()
        db.refresh(new_link)

        return new_link
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@routerLinks.delete('/delete_link')
def delete_link(
        user: User = Depends(get_current_user),
        token: str = Depends(oauth2_scheme),
        url: Optional[str] = None,
):
    db = next(get_db())
    verify_token_validity(token)
    try:
        stmt = select(Links).where(Links.url == url).where(Links.user_id == user.id)
        result = db.execute(stmt).scalar_one_or_none()

        if not result:
            raise HTTPException(status_code=400, detail="Link do not exists")

        stmt = delete(Links).where(Links.url == url).where(Links.user_id == user.id)
        result = db.execute(stmt)
        db.commit()
        return {"msg": "Link deleted", "Links deleted": result.rowcount}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

ALLOWED_LINK_TYPES = ["website", "book", "article", "music", "video"]
DEFAULT_LINK_TYPE = "website"

@routerLinks.post('/update_link')
def update_link(
        update_data: LinkUpdate,
        user: User = Depends(get_current_user),
        token: str = Depends(oauth2_scheme),
        url: Optional[str] = None,
):
    db = next(get_db())
    verify_token_validity(token)

    try:
        stmt = select(Links).where(Links.url == url).where(Links.user_id == user.id)
        link = db.execute(stmt).scalar_one_or_none()

        if not link:
            raise HTTPException(status_code=400, detail="Link do not exists")

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict.get('type') not in ALLOWED_LINK_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid link type. Maybe you a want one from {ALLOWED_LINK_TYPES}")
        for field, value in update_dict.items():
            setattr(link, field, value)



        link.updated_at = datetime.datetime.utcnow()
        db.merge(link)
        db.commit()
        db.refresh(link)
        return link

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()