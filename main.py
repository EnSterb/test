import requests
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer

from app.routers.auth import get_current_user
from app.routers.auth import router as auth_router
from app.models import Users
from app.routers.user import router as user_router
from app.routers.links import routerLinks as links_router
from app.routers.collections import routerCollections as collection_router

app = FastAPI(
    title="Test",
    version="0.3.1",
)
app.include_router(user_router)
app.include_router(links_router)
app.include_router(collection_router)
app.include_router(auth_router)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@app.get("/me", tags=["Auth"])
def read_profile(current_user: Users = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    return {
        'email': current_user.email,
        'access_token': token
    }
