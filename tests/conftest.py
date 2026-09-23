import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.database.models import User, UserRole

@pytest.fixture
def mock_session():
    """Синхронний мок сесії бази даних SQLAlchemy."""
    return MagicMock(spec=Session)


@pytest.fixture
def test_user():
    """Фікстура тестового користувача."""
    user = User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        password="hashed_password",
        avatar="https://example.com/avatar.jpg",
        role=UserRole.USER,
        confirmed=True,
    )
    return user
