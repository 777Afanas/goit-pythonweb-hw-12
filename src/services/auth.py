"""Модуль автентифікації, авторизації та керування токенами безпеки.

Забезпечує хешування паролів, роботу з JWT (access/refresh/email токени),
а також швидку верифікацію користувача через кешування в Redis.
"""

from datetime import datetime, timedelta, timezone
import json
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import redis
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.cache import redis_client
from src.database.db import get_db
from src.database.models import User
from src.repository.users import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """Сервіс для автентифікації користувачів і контролю доступу."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Перевіряє відповідність відкритого пароля його хешу.

        :param plain_password: Пароль у відкритому вигляді.
        :param hashed_password: Хеш пароля з бази даних.
        :return: True, якщо пароль збігається, інакше False.
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Генерує bcrypt-хеш для пароля.

        :param password: Пароль у відкритому вигляді.
        :return: Захешований рядок пароля.
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[float] = None) -> str:
        """Генерує короткоживучий JWT токен доступу (access token).

        :param data: Словник з даними (payload), зазвичай містить 'sub': email.
        :param expires_delta: Опціональний час життя в секундах.
        :return: Закодований рядок токена.
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = (
            now + timedelta(seconds=expires_delta)
            if expires_delta
            else now + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
        )
        to_encode.update({"iat": now, "exp": expire, "scope": "access_token"})
        return jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[float] = None) -> str:
        """Генерує довгоживучий JWT токен оновлення (refresh token).

        :param data: Словник з даними для кодування.
        :param expires_delta: Опціональний час життя в секундах.
        :return: Закодований рядок токена.
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = (
            now + timedelta(seconds=expires_delta)
            if expires_delta
            else now + timedelta(days=7)
        )
        to_encode.update({"iat": now, "exp": expire, "scope": "refresh_token"})
        return jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_email_token(data: dict) -> str:
        """Створює тимчасовий токен для підтвердження пошти або скидання пароля.

        :param data: Словник з даними користувача.
        :return: Закодований рядок токена.
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=settings.RESET_TOKEN_EXPIRATION_SECONDS)
        to_encode.update({"iat": now, "exp": expire, "scope": "email_token"})
        return jwt.encode(
            to_encode, settings.RESET_TOKEN_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_reset_password_token(data: dict) -> str:
        """
        Створює тимчасовий токен для безпечного скидання пароля.

        :param data: Словник з даними користувача (зокрема email у полі 'sub').
        :type data: dict
        :return: Закодований рядок токена зі scope 'reset_password'.
        :rtype: str
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=settings.RESET_TOKEN_EXPIRATION_SECONDS)
        to_encode.update({"iat": now, "exp": expire, "scope": "reset_password"})
        return jwt.encode(
            to_encode,
            settings.RESET_TOKEN_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @staticmethod
    def decode_token(token: str, expected_scope: str) -> str:
        """Декодує JWT токен і перевіряє відповідність scope.

        :param token: JWT токен у вигляді рядка.
        :param expected_scope: Очікуване значення поля scope ('access_token', 'refresh_token', 'reset_password', тощо).
        :raises HTTPException: Якщо токен недійсний, прострочений або містить некоректний scope.
        :return: Email користувача (sub).
        """
        # Використовуємо секретний ключ для тимчасових токенів (email та скидання пароля)
        secret_key = (
            settings.RESET_TOKEN_SECRET_KEY
            if expected_scope in ("email_token", "reset_password")
            else settings.JWT_SECRET_KEY
        )
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.JWT_ALGORITHM],
            )
            if payload.get("scope") != expected_scope:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid scope for token",
                )
            email: str | None = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not validate credentials",
                )
            return email
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )

    @staticmethod
    def get_current_user(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ) -> User:
        """Отримує поточного користувача за access_token, використовуючи кеш Redis.

        Спочатку виконується спроба отримати користувача з кешу Redis за ключем user:{email}.
        Якщо в кеші даних немає — користувач запитується з PostgreSQL і записується в Redis на 15 хв.

        :param token: Bearer токен доступу.
        :param db: Сесія SQLAlchemy.
        :raises HTTPException: Якщо токен недійсний або користувача не знайдено.
        :return: Об'єкт користувача моделі User.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        email = AuthService.decode_token(token, expected_scope="access_token")
        cache_key = f"user:{email}"

        # 1. Спроба отримати користувача з кешу Redis
        try:
            cached_user = redis_client.get(cache_key)
            if cached_user:
                user_data = json.loads(cached_user)  # type: ignore
                detached_user = User(**user_data)
                # Прив'язуємо об'єкт до поточної сесії через merge для коректної роботи ORM
                return db.merge(detached_user, load=False)
        except redis.RedisError:
            pass

        # 2. Якщо в кеші немає — звернення до PostgreSQL
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_email(email)
        if user is None:
            raise credentials_exception

        # 3. Запис у кеш Redis із TTL 900 сек (15 хвилин)
        try:
            role_val = getattr(user, "role", None)
            if hasattr(role_val, "value"):
                role_val = str(getattr(user, "role", "user"))

            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": getattr(user, "avatar", None),
                "role": role_val,
                "confirmed": getattr(user, "confirmed", False),
            }
            redis_client.setex(cache_key, 900, json.dumps(user_dict))
        except redis.RedisError:
            pass

        return user


auth_service = AuthService()
