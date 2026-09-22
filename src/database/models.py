from datetime import date, datetime
import enum
from typing import List, Optional
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.db import Base


class UserRole(str, enum.Enum):
    """Перелік доступних ролей користувачів."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    Модель користувача системи.

    Attributes:
        id: Первинний ключ облікового запису.
        username: Псевдонім/ім'я користувача.
        email: Унікальна електронна пошта.
        password: Хеш пароля.
        avatar: URL посилання на аватар користувача.
        role: Роль у системі контролю доступу ('user' або 'admin').
        confirmed: Прапорець підтвердження електронної адреси.
        refresh_token: Довгоживучий токен для оновлення сесії авторизації.
        created_at: Час реєстрації користувача.
        contacts: Зв'язок один-до-багатьох із контактами користувача.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)     
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="userrole",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=UserRole.USER,
        nullable=False,
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )


class Contact(Base):
    """
    Модель контактної книги користувача.

    Attributes:
        id: Первинний ключ контакту.
        first_name: Ім'я контакту.
        last_name: Прізвище контакту.
        email: Унікальна пошта контакту.
        phone: Номер телефону.
        birthday: День народження.
        additional_data: Додаткова довільна інформація.
        user_id: Зовнішній ключ, прив'язка до облікового запису User.
        user: Зв'язок багато-до-одного з моделлю User.
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    additional_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="contacts")
