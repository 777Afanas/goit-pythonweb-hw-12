from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.repository.users import UserRepository
from src.schemas import UserResponse
from src.services.auth import AuthService
from src.services.upload_avatar import upload_avatar

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,     
)
async def get_me(user: User = Depends(AuthService.get_current_user)):
    return user


@router.patch("/avatar", response_model=UserResponse)
def patch_avatar(
    file: UploadFile = File(...),
    user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db),
):
    avatar_url = upload_avatar(file.file, f"avatars/{user.id}")
    user_repo = UserRepository(db)
    return user_repo.update_avatar(user.email, avatar_url)
