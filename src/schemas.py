"""
Модуль Pydantic-схем для валідації вхідних та вихідних даних REST API.

Містить моделі автентифікації, користувачів, управління ролями,
скидання пароля, токенів та управління контактами.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.database.models import UserRole

# --- Схеми аутентифікації та токенів ---


class TokenModel(BaseModel):
    """
    Схема відповіді для автентифікації та оновлення токенів за допомогою пари JWT.

    Attributes:
        access_token: Короткоживучий JWT токен доступу.
        refresh_token: Довгоживучий JWT токен для ротації та оновлення access_token.
        token_type: Тип токена (за замовчуванням 'bearer').
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class Token(BaseModel):
    """
    Спрощена схема для повернення одиночного токена доступу.

    Attributes:
        access_token: JWT токен доступу.
        token_type: Тип токена (за замовчуванням 'bearer').
    """

    access_token: str
    token_type: str = "bearer"


# --- Схеми користувачів ---


class UserCreate(BaseModel):
    """
    Схема для реєстрації нового користувача.

    Attributes:
        username: Ім'я користувача (довжина від 3 до 50 символів).
        email: Унікальна електронна адреса користувача.
        password: Пароль користувача у відкритому вигляді (від 6 до 128 символів).
    """

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    """
    Схема публічної відповіді з даними користувача.

    Attributes:
        id: Унікальний ідентифікатор користувача.
        username: Ім'я користувача.
        email: Електронна адреса.
        avatar: URL-адреса аватара.
        role: Роль користувача в системі ('user' або 'admin').
        confirmed: Статус підтвердження електронної пошти.
        created_at: Дата та час створення облікового запису.
    """

    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    role: UserRole = UserRole.USER
    confirmed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDb(BaseModel):
    """
    Спрощена схема користувача для кешування в Redis та внутрішніх операцій.

    Attributes:
        id: Унікальний ідентифікатор користувача.
        username: Ім'я користувача.
        email: Електронна адреса.
        avatar: URL-адреса аватара.
        role: Роль користувача.
    """

    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    role: UserRole = UserRole.USER

    model_config = ConfigDict(from_attributes=True)


# --- Схеми для верифікації та скидання пароля ---


class RequestEmail(BaseModel):
    """
    Схема запиту на повторне відправлення листа верифікації пошти.

    Attributes:
        email: Електронна адреса зареєстрованого користувача.
    """

    email: EmailStr


class RequestResetPassword(BaseModel):
    """
    Схема запиту на відновлення пароля.

    Attributes:
        email: Електронна адреса облікового запису для надсилання токена скидання.
    """

    email: EmailStr


class ResetPassword(BaseModel):
    """
    Схема безпосереднього оновлення пароля за токеном.

    Attributes:
        token: Валідний токен підтвердження скидання пароля.
        new_password: Новий пароль користувача (від 6 до 128 символів).
    """

    token: str
    new_password: str = Field(min_length=6, max_length=128)


# --- Схеми контактів ---


class ContactBase(BaseModel):
    """
    Базова схема контакту із загальними полями валідації.

    Attributes:
        first_name: Ім'я контакту.
        last_name: Прізвище контакту.
        email: Електронна пошта контакту.
        phone: Номер телефону контакту.
        birthday: Дата народження контакту.
        additional_data: Додаткова інформація або примітки (опціонально).
    """

    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=20)
    birthday: date
    additional_data: Optional[str] = None


class ContactCreate(ContactBase):
    """Схема створення нового контакту."""

    pass


class ContactUpdate(ContactBase):
    """Схема повного оновлення існуючого контакту."""

    pass


class ContactResponse(ContactBase):
    """
    Схема відповіді з повною інформацією про контакт.

    Attributes:
        id: Унікальний ідентифікатор контакту в БД.
        user_id: Ідентифікатор власника контакту.
    """

    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
