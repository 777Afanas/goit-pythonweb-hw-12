"""
Модуль контролю доступу на основі ролей (RBAC).

Забезпечує перевірку дозволів користувача для доступу до захищених
маршрутів API (FastAPI Dependencies).
"""

from typing import Sequence
from fastapi import Depends, HTTPException, status

from src.database.models import User, UserRole
from src.services.auth import auth_service


class RoleAccess:
    """
    Клас-залежність для контролю доступу на основі ролей користувача.

    Attributes:
        allowed_roles: Список дозволених ролей для виконання операції.
    """

    def __init__(self, allowed_roles: Sequence[UserRole]) -> None:
        """
        Ініціалізує фільтр ролей.

        Args:
            allowed_roles: Послідовність ролей (UserRole), яким надано доступ.
        """
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: User = Depends(auth_service.get_current_user)
    ) -> User:
        """
        Перевіряє відповідність ролі поточного авторизованого користувача.

        Args:
            current_user: Поточний автентифікований користувач (FastAPI Dependency).

        Returns:
            User: Об'єкт користувача у разі успішної перевірки прав.

        Raises:
            HTTPException: 403 Forbidden, якщо поточна роль не входить до дозволених.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for current user role",
            )
        return current_user
