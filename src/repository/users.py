from typing import Optional
from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserCreate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, body: UserCreate, hashed_password: str) -> User:
        user = User(
            username=body.username,
            email=body.email,
            password=hashed_password,
            confirmed=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def confirm_email(self, email: str) -> None:
        user = self.get_user_by_email(email)
        if user:
            user.confirmed = True
            self.db.commit()

    def update_avatar(self, email: str, url: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if user:
            user.avatar = url
            self.db.commit()
            self.db.refresh(user)
        return user
