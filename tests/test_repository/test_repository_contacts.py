import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate
from src.repository.contacts import ContactRepository


@pytest.fixture
def contact_repo(mock_session: MagicMock) -> ContactRepository:
    """Фикстура инициализации репозитория с мок-сессией БД."""
    return ContactRepository(db=mock_session)


def test_get_contacts_all(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    expected_contacts = [
        Contact(id=1, first_name="John", last_name="Doe", user_id=test_user.id),
        Contact(id=2, first_name="Jane", last_name="Doe", user_id=test_user.id),
    ]
    mock_session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
        expected_contacts
    )

    contacts = contact_repo.get_contacts(user=test_user, skip=0, limit=100)

    assert contacts == expected_contacts
    assert len(contacts) == 2


def test_get_contacts_with_filters(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    expected_contacts = [
        Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            user_id=test_user.id,
        )
    ]
    # Настройка цепочки вызовов фильтрации (по user_id, first_name, last_name, email)
    (
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value
    ) = expected_contacts

    contacts = contact_repo.get_contacts(
        user=test_user,
        skip=0,
        limit=10,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
    )

    assert contacts == expected_contacts
    assert len(contacts) == 1


def test_get_contact_by_id_found(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    expected_contact = Contact(
        id=1, first_name="John", last_name="Doe", user_id=test_user.id
    )
    mock_session.query.return_value.filter.return_value.first.return_value = (
        expected_contact
    )

    contact = contact_repo.get_contact_by_id(contact_id=1, user=test_user)

    assert contact is not None
    assert contact == expected_contact
    assert contact.id == 1


def test_get_contact_by_id_not_found(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    contact = contact_repo.get_contact_by_id(contact_id=999, user=test_user)

    assert contact is None


def test_create_contact(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    body = ContactCreate(
        first_name="Ivan",
        last_name="Franko",
        email="ivan@example.com",
        phone="+380991234567",
        birthday=date(1990, 8, 27),
        additional_data="Writer",
    )

    created_contact = contact_repo.create_contact(body=body, user=test_user)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert created_contact.first_name == body.first_name
    assert created_contact.last_name == body.last_name
    assert created_contact.email == body.email
    assert created_contact.phone == body.phone
    assert created_contact.user_id == test_user.id


def test_update_contact_found(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    existing_contact = Contact(
        id=1,
        first_name="Old",
        last_name="Name",
        email="old@example.com",
        phone="+380000000000",
        birthday=date(2000, 1, 1),
        user_id=test_user.id,
    )
    mock_session.query.return_value.filter.return_value.first.return_value = (
        existing_contact
    )

    body = ContactUpdate(
        first_name="New",
        last_name="Name",
        email="new@example.com",
        phone="+380991112233",
        birthday=date(2000, 1, 1),
        additional_data="Updated info",
    )

    updated = contact_repo.update_contact(contact_id=1, body=body, user=test_user)

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(existing_contact)
    assert updated is not None
    assert updated.first_name == "New"
    assert updated.email == "new@example.com"
    assert updated.phone == "+380991112233"


def test_update_contact_not_found(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    mock_session.query.return_value.filter.return_value.first.return_value = None
    body = ContactUpdate(
        first_name="New",
        last_name="Name",
        email="new@example.com",
        phone="+380991112233",
        birthday=date(2000, 1, 1),
    )

    updated = contact_repo.update_contact(contact_id=999, body=body, user=test_user)

    mock_session.commit.assert_not_called()
    assert updated is None


def test_delete_contact_found(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    existing_contact = Contact(
        id=1, first_name="Delete", last_name="Me", user_id=test_user.id
    )
    mock_session.query.return_value.filter.return_value.first.return_value = (
        existing_contact
    )

    removed = contact_repo.delete_contact(contact_id=1, user=test_user)

    mock_session.delete.assert_called_once_with(existing_contact)
    mock_session.commit.assert_called_once()
    assert removed == existing_contact


def test_delete_contact_not_found(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    removed = contact_repo.delete_contact(contact_id=999, user=test_user)

    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()
    assert removed is None


def test_get_upcoming_birthdays(
    contact_repo: ContactRepository, mock_session: MagicMock, test_user: User
):
    today = date.today()
    # День рождения через 3 дня (попадает в окно 7 дней)
    target_birthday = (today + timedelta(days=3)).replace(year=1995)
    contact_with_bday = Contact(
        id=1,
        first_name="Lesya",
        last_name="Ukrainka",
        birthday=target_birthday,
        user_id=test_user.id,
    )

    # День рождения был 10 дней назад (не должен попасть)
    past_birthday = (today - timedelta(days=10)).replace(year=1990)
    contact_past = Contact(
        id=2,
        first_name="Taras",
        last_name="Shevchenko",
        birthday=past_birthday,
        user_id=test_user.id,
    )

    # Контакт без дня рождения
    contact_no_bday = Contact(
        id=3,
        first_name="No",
        last_name="Birthday",
        birthday=None,
        user_id=test_user.id,
    )

    mock_session.query.return_value.filter.return_value.all.return_value = [
        contact_with_bday,
        contact_past,
        contact_no_bday,
    ]

    upcoming = contact_repo.get_upcoming_birthdays(user=test_user, days=7)

    assert len(upcoming) == 1
    assert upcoming[0] == contact_with_bday
