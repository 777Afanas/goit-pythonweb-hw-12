import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock, patch

from main import app
from src.database.db import get_db
from src.database.models import Base, User, UserRole
from src.services.auth import AuthService

# Тестовая база данных SQLite в оперативной памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# expire_on_commit=False предотвращает отсоединение объектов от сессии после коммита
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session():
    """Сбрасывает базу данных и кэш Redis перед каждым тестом."""
    try:
        from src.database.cache import redis_client

        if redis_client:
            redis_client.flushall()
    except Exception:
        pass

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Тестовый клиент FastAPI с подменой сессии БД и моком фоновых писем."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Патчим только те функции, которые реально существуют и вызываются в фоновых задачах auth
    with patch("src.api.auth.send_verification_email", new=MagicMock()), patch(
        "src.api.auth.send_reset_password_email", new=MagicMock()
    ):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Создает базового подтвержденного пользователя с ролью USER."""
    user = User(
        username="testuser",
        email="testuser@example.com",
        password=AuthService.get_password_hash("secret123"),
        confirmed=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Создает пользователя с правами администратора (роль ADMIN)."""
    admin = User(
        username="adminuser",
        email="admin@example.com",
        password=AuthService.get_password_hash("secret123"),
        confirmed=True,
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Заголовок авторизации Bearer JWT для обычного пользователя."""
    token = AuthService.create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_user):
    """Заголовок авторизации Bearer JWT для администратора."""
    token = AuthService.create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {token}"}


# # Алиас для фикстуры db_session: если тесты репозиториев запрашивают 'session'
# @pytest.fixture(scope="function")
# def session(db_session):
#     """Предоставляет сессию БД под именем 'session' для тестов репозиториев."""
#     yield db_session


# # Фикстуры репозиториев, если они требуются в тестах
# @pytest.fixture(scope="function")
# def user_repo(db_session):
#     from src.repository.users import UserRepository

#     return UserRepository(db_session)


# @pytest.fixture(scope="function")
# def contact_repo(db_session):
#     from src.repository.contacts import ContactRepository

#     return ContactRepository(db_session)


# 1. Алиасы сессии базы данных
@pytest.fixture(scope="function")
def session(db_session):
    """Предоставляет сессию под именем 'session'."""
    yield db_session


@pytest.fixture(scope="function")
def db(db_session):
    """Предоставляет сессию под именем 'db'."""
    yield db_session


# 2. Фикстуры репозиториев
@pytest.fixture(scope="function")
def user_repo(db_session):
    """Репозиторий пользователей."""
    from src.repository.users import UserRepository

    return UserRepository(db_session)


@pytest.fixture(scope="function")
def contact_repo(db_session):
    """Репозиторий контактов."""
    from src.repository.contacts import ContactRepository

    return ContactRepository(db_session)


@pytest.fixture(scope="function")
def mock_session():
    """Мок сессии SQLAlchemy для тестов репозиториев."""
    return MagicMock(spec=Session)
