# users.py
from fastapi import APIRouter, Depends, HTTPException
from db import get_user_by_username
from data_science_api.app.api.routes.auth import get_current_user
from data_science_api.app.models.models import UserOut

user_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@user_router.get("/me", response_model=UserOut)
def read_me(username: str = Depends(get_current_user)):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
