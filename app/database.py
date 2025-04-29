import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.models import Users, Collections, Links

load_dotenv(dotenv_path='.env')

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{os.getenv("BDUSER")}:{os.getenv("BDPASSWORD")}@localhost:8888/test"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def user_exists(email:Optional[str]) -> bool:
    db = next(get_db())
    try:
        return db.query(Users).filter(Users.email == email).first() is not None
    finally:
        db.close()

