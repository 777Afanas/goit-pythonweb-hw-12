"""
Модуль ендпоінтів для роботи з користувачами системи.

Містить синхронні маршрути перегляду власного профілю та оновлення аватара
з перевіркою адміністративних прав (RBAC).
"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas import UserResponse
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from src.services.upload_avatar import upload_avatar
from src.repository.users import UserRepository

router = APIRouter(prefix="/users", tags=["users"])

# Обмеження доступу виключно для користувачів з роллю ADMIN
admin_access = RoleAccess([UserRole.ADMIN])


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(user: User = Depends(auth_service.get_current_user)) -> User:
    """
    Отримати інформацію про поточного автентифікованого користувача.

    Args:
        user: Поточний користувач, отриманий під час автентифікації.

    Returns:
        User: Об'єкт поточного користувача.
    """
    return user


@router.patch("/avatar", response_model=UserResponse)
def patch_avatar(
    file: UploadFile = File(...),
    user: User = Depends(admin_access),
    db: Session = Depends(get_db),
) -> User:
    """
    Оновити аватар облікового запису.

    Операція доступна виключно адміністраторам (роль ADMIN).

    Args:
        file: Завантажений файл нового аватара.
        user: Поточний користувач-адміністратор, валідований RoleAccess.
        db: Синхронна сесія бази даних SQLAlchemy.

    Returns:
        User: Оновлений запис користувача з новим URL аватара.
    """
    avatar_url = upload_avatar(file.file, f"avatars/{user.id}")
    user_repo = UserRepository(db)
    return user_repo.update_avatar(user.email, avatar_url)
