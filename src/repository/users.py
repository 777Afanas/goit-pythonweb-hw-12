from typing import Optional
from sqlalchemy.orm import Session
from src.database.models import User, UserRole
from src.schemas import UserCreate


class UserRepository:
    """Клас репозиторію для виконання операцій доступу до даних користувачів."""

    def __init__(self, db: Session):
        """Ініціалізує екземпляр репозиторію сесією бази даних.

        :param db: Сесія SQLAlchemy для роботи з базою даних.
        """
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Шукає користувача за його електронною поштою.

        :param email: Електронна адреса користувача.
        :return: Об'єкт User, якщо знайдено, інакше None.
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Шукає користувача за унікальним ідентифікатором.

        :param user_id: ID користувача.
        :return: Об'єкт User, якщо знайдено, інакше None.
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, body: UserCreate, hashed_password: str) -> User:
        """Створює та зберігає нового користувача в базі даних.

        :param body: Дані схеми реєстрації нового користувача.
        :param hashed_password: Захешований пароль.
        :return: Створений об'єкт користувача з призначеним id.
        """
        user = User(
            username=body.username,
            email=body.email,
            password=hashed_password,
            role=UserRole.USER,
            confirmed=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def confirm_email(self, email: str) -> None:
        """Підтверджує адресу електронної пошти користувача.

        :param email: Електронна адреса користувача.
        """
        user = self.get_user_by_email(email)
        if user:
            user.confirmed = True
            self.db.commit()

    def update_avatar(self, email: str, url: str) -> Optional[User]:
        """Оновлює URL-адресу аватара користувача.

        :param email: Електронна адреса користувача.
        :param url: Нова URL-адреса зображення аватара.
        :return: Оновлений об'єкт User або None.
        """
        user = self.get_user_by_email(email)
        if user:
            user.avatar = url
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_token(self, user: User, token: str | None) -> None:
        """Оновлює або скидає refresh_token користувача в БД.

        :param user: Об'єкт користувача моделі User.
        :param token: Рядок токена або None для відкликання сесії.
        """
        user.refresh_token = token
        self.db.commit()

    def update_password(self, user: User, new_hashed_password: str) -> None:
        """Оновлює захешований пароль користувача в БД.

        :param user: Об'єкт користувача моделі User.
        :param new_hashed_password: Новий захешований рядок пароля.
        """
        user.password = new_hashed_password
        self.db.commit()
