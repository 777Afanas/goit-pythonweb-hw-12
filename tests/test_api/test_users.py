from io import BytesIO
from unittest.mock import patch


def test_get_current_user_profile(client, auth_headers, test_user):
    response = client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


def test_update_avatar_as_admin(client, admin_headers):
    fake_file = BytesIO(b"fake image content")
    files = {"file": ("avatar.png", fake_file, "image/png")}

    # Мокаємо саме функцію upload_avatar там, де вона імпортована й викликається
    with patch("src.api.users.upload_avatar") as mock_upload:
        mock_upload.return_value = (
            "https://res.cloudinary.com/demo/image/upload/avatar.png"
        )
        response = client.patch("/api/users/avatar", files=files, headers=admin_headers)

    assert response.status_code == 200
    assert (
        response.json()["avatar"]
        == "https://res.cloudinary.com/demo/image/upload/avatar.png"
    )


def test_update_avatar_forbidden_for_regular_user(client, auth_headers):
    fake_file = BytesIO(b"fake image content")
    files = {"file": ("avatar.png", fake_file, "image/png")}

    # Звичайний користувач (USER) блокується залежністю admin_access ще до виклику завантаження
    response = client.patch("/api/users/avatar", files=files, headers=auth_headers)
    assert response.status_code == 403
