from datetime import date, timedelta


def test_create_contact(client, auth_headers):
    payload = {
        "first_name": "Іван",
        "last_name": "Франко",
        "email": "franko@example.com",
        "phone": "+380501234567",
        "birthday": "1990-08-27",
        "additional_data": "Письменник",
    }
    # Зверніть увагу на кінцевий слеш: /api/contacts/
    response = client.post("/api/contacts/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == payload["first_name"]
    assert data["email"] == payload["email"]
    assert "id" in data


def test_get_contacts_list(client, auth_headers):
    payload = {
        "first_name": "Тарас",
        "last_name": "Шевченко",
        "email": "shevchenko@example.com",
        "phone": "+380671112233",
        "birthday": "1985-03-09",
    }
    client.post("/api/contacts/", json=payload, headers=auth_headers)

    # Зверніть увагу на кінцевий слеш: /api/contacts/
    response = client.get("/api/contacts/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_contact_by_id(client, auth_headers):
    payload = {
        "first_name": "Леся",
        "last_name": "Українка",
        "email": "lesya@example.com",
        "phone": "+380631234567",
        "birthday": "1991-02-25",
    }
    create_res = client.post("/api/contacts/", json=payload, headers=auth_headers)
    contact_id = create_res.json()["id"]

    response = client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == contact_id


def test_get_contact_not_found(client, auth_headers):
    response = client.get("/api/contacts/99999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"


def test_update_contact(client, auth_headers):
    payload = {
        "first_name": "Микола",
        "last_name": "Гоголь",
        "email": "gogol@example.com",
        "phone": "+380509876543",
        "birthday": "1980-04-01",
    }
    create_res = client.post("/api/contacts/", json=payload, headers=auth_headers)
    contact_id = create_res.json()["id"]

    update_payload = {
        "first_name": "Микола",
        "last_name": "Оновлений",
        "email": "gogol_new@example.com",
        "phone": "+380509876543",
        "birthday": "1980-04-01",
    }
    response = client.put(
        f"/api/contacts/{contact_id}", json=update_payload, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["last_name"] == "Оновлений"


def test_update_contact_not_found(client, auth_headers):
    update_payload = {
        "first_name": "Невідомий",
        "last_name": "Користувач",
        "email": "unknown@example.com",
        "phone": "+380500000000",
        "birthday": "1990-01-01",
    }
    response = client.put(
        "/api/contacts/99999", json=update_payload, headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_contact(client, auth_headers):
    payload = {
        "first_name": "Григорій",
        "last_name": "Сковорода",
        "email": "skovoroda@example.com",
        "phone": "+380501110022",
        "birthday": "1972-12-03",
    }
    create_res = client.post("/api/contacts/", json=payload, headers=auth_headers)
    contact_id = create_res.json()["id"]

    del_res = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_delete_contact_not_found(client, auth_headers):
    del_res = client.delete("/api/contacts/99999", headers=auth_headers)
    assert del_res.status_code == 404


def test_get_upcoming_birthdays(client, auth_headers):
    # Створюємо контакт із днем народження через 3 дні
    upcoming_date = date.today() + timedelta(days=3)
    payload = {
        "first_name": "Іменинник",
        "last_name": "Тестовий",
        "email": "birthday@example.com",
        "phone": "+380509998877",
        "birthday": upcoming_date.strftime("%Y-%m-%d"),
    }
    client.post("/api/contacts/", json=payload, headers=auth_headers)

    response = client.get("/api/contacts/birthdays?days=7", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(c["email"] == "birthday@example.com" for c in data)


def test_contacts_unauthorized(client):
    response = client.get("/api/contacts/")
    assert response.status_code == 401
