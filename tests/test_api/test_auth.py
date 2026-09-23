from unittest.mock import MagicMock, patch
from src.database.models import User, UserRole
from src.services.auth import AuthService


def test_register_user_success(client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Password123!",
    }
    with patch("src.api.auth.send_verification_email", new=MagicMock()):
        response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data


def test_register_duplicate_email(client, test_user):
    payload = {
        "username": "anotheruser",
        "email": test_user.email,
        "password": "Password123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_login_user_success(client, test_user):
    login_data = {
        "username": test_user.email,
        "password": "secret123",
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, test_user):
    login_data = {
        "username": test_user.email,
        "password": "wrong_password",
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_unconfirmed_user(client, db_session):
    unconfirmed = User(
        username="unconfirmed",
        email="unconfirmed@example.com",
        password=AuthService.get_password_hash("secret123"),
        confirmed=False,
        role=UserRole.USER,
    )
    db_session.add(unconfirmed)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": unconfirmed.email, "password": "secret123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email not verified"


def test_confirm_email_success(client, db_session):
    user = User(
        username="confirmme",
        email="confirmme@example.com",
        password=AuthService.get_password_hash("secret123"),
        confirmed=False,
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()

    email_token = AuthService.create_email_token({"sub": user.email})
    response = client.get(f"/api/auth/confirmed_email/{email_token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email successfully confirmed"

    # Повторне підтвердження
    response_again = client.get(f"/api/auth/confirmed_email/{email_token}")
    assert response_again.status_code == 200
    assert response_again.json()["message"] == "Email already confirmed"


def test_confirm_email_invalid_token(client):
    response = client.get("/api/auth/confirmed_email/invalidtoken123")
    assert response.status_code == 400


def test_refresh_token_success(client, test_user, db_session):
    refresh_token = AuthService.create_refresh_token({"sub": test_user.email})
    test_user.refresh_token = refresh_token
    db_session.commit()

    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = client.get("/api/auth/refresh_token", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_revoked_or_invalid(client, test_user, db_session):
    # Зберігаємо один токен у БД
    test_user.refresh_token = "stored_token"
    db_session.commit()

    # Створюємо інший валідний за структурою токен
    different_token = AuthService.create_refresh_token({"sub": test_user.email})
    headers = {"Authorization": f"Bearer {different_token}"}
    response = client.get("/api/auth/refresh_token", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or revoked refresh token"


def test_request_reset_password(client, test_user):
    payload = {"email": test_user.email}
    with patch("src.api.auth.send_reset_password_email", new=MagicMock()):
        response = client.post("/api/auth/request-reset-password", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Check your email for the reset instructions"


def test_reset_password_success(client, test_user):
    reset_token = AuthService.create_reset_password_token({"sub": test_user.email})
    payload = {
        "token": reset_token,
        "new_password": "NewSecretPassword123!",
    }
    response = client.post("/api/auth/reset-password", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Password successfully updated"

    # Перевірка логіну з новим паролем
    login_data = {
        "username": test_user.email,
        "password": "NewSecretPassword123!",
    }
    login_res = client.post("/api/auth/login", data=login_data)
    assert login_res.status_code == 200


def test_reset_password_invalid_token(client):
    payload = {
        "token": "invalid_token_value",
        "new_password": "NewSecretPassword123!",
    }
    response = client.post("/api/auth/reset-password", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"
