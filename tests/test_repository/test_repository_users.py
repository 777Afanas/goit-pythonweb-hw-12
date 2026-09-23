import pytest
from unittest.mock import MagicMock, patch
from src.database.models import User, UserRole
from src.schemas import UserCreate
from src.repository.users import UserRepository


@pytest.fixture
def user_repo(mock_session: MagicMock) -> UserRepository:
    """Фикстура инициализации репозитория пользователей с мок-сессией БД."""
    return UserRepository(db=mock_session)


def test_get_user_by_email_found(user_repo: UserRepository, mock_session: MagicMock, test_user: User):
    mock_session.query.return_value.filter.return_value.first.return_value = test_user

    result = user_repo.get_user_by_email(email="testuser@example.com") 
    
    assert result is not None
    assert result == test_user
    assert result.email == "testuser@example.com"


def test_get_user_by_email_not_found(user_repo: UserRepository, mock_session: MagicMock):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    result = user_repo.get_user_by_email(email="notfound@example.com")

    assert result is None


def test_get_user_by_id_found(user_repo: UserRepository, mock_session: MagicMock, test_user: User):
    mock_session.query.return_value.filter.return_value.first.return_value = test_user

    result = user_repo.get_user_by_id(user_id=1)
    assert result is not None
    assert result == test_user
    assert result.id == 1


def test_get_user_by_id_not_found(user_repo: UserRepository, mock_session: MagicMock):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    result = user_repo.get_user_by_id(user_id=999)

    assert result is None


def test_create_user(user_repo: UserRepository, mock_session: MagicMock):
    body = UserCreate(
        username="newuser",
        email="newuser@example.com",
        password="plain_password",
    )
    hashed_password = "secure_hashed_password"

    created_user = user_repo.create_user(body=body, hashed_password=hashed_password)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert created_user.username == body.username
    assert created_user.email == body.email
    assert created_user.password == hashed_password
    assert created_user.role == UserRole.USER
    assert created_user.confirmed is False


@patch("src.repository.users.redis_client")
def test_confirm_email_found(mock_redis: MagicMock, user_repo: UserRepository, mock_session: MagicMock, test_user: User):
    test_user.confirmed = False
    mock_session.query.return_value.filter.return_value.first.return_value = test_user

    user_repo.confirm_email(email=test_user.email)

    assert test_user.confirmed is True
    mock_session.commit.assert_called_once()
    mock_redis.delete.assert_called_once_with(f"user:{test_user.email}")


@patch("src.repository.users.redis_client")
def test_confirm_email_not_found(mock_redis: MagicMock, user_repo: UserRepository, mock_session: MagicMock):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    user_repo.confirm_email(email="nonexistent@example.com")

    mock_session.commit.assert_not_called()
    mock_redis.delete.assert_not_called()


@patch("src.repository.users.redis_client")
def test_update_avatar_found(mock_redis: MagicMock, user_repo: UserRepository, mock_session: MagicMock, test_user: User):
    mock_session.query.return_value.filter.return_value.first.return_value = test_user
    new_avatar_url = "https://example.com/images/new_avatar.png"

    result = user_repo.update_avatar(email=test_user.email, url=new_avatar_url)

    assert result is not None
    assert result.avatar == new_avatar_url
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(test_user)
    mock_redis.delete.assert_called_once_with(f"user:{test_user.email}")


@patch("src.repository.users.redis_client")
def test_update_avatar_not_found(mock_redis: MagicMock, user_repo: UserRepository, mock_session: MagicMock):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    result = user_repo.update_avatar(email="notfound@example.com", url="https://example.com/avatar.png")

    assert result is None
    mock_session.commit.assert_not_called()
    mock_redis.delete.assert_not_called()


def test_update_token(user_repo: UserRepository, mock_session: MagicMock, test_user: User):
    token = "sample_refresh_token"

    user_repo.update_token(user=test_user, token=token)

    assert test_user.refresh_token == token
    mock_session.commit.assert_called_once()


@patch("src.repository.users.redis_client")
def test_update_password(mock_redis: MagicMock, user_repo: UserRepository, mock_session: MagicMock, test_user: User):
    new_hashed = "new_hashed_password"

    user_repo.update_password(user=test_user, new_hashed_password=new_hashed)

    assert test_user.password == new_hashed
    mock_session.commit.assert_called_once()
    mock_redis.delete.assert_called_once_with(f"user:{test_user.email}")
