from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate


class ContactService:
    def __init__(self, db: Session):
        self.repository = ContactRepository(db)

    def get_contacts(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Contact]:
        return self.repository.get_contacts(
            user=user,
            skip=skip,
            limit=limit,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

    def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        return self.repository.get_contact_by_id(contact_id=contact_id, user=user)

    def create_contact(self, body: ContactCreate, user: User) -> Contact:
        return self.repository.create_contact(body=body, user=user)

    def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Optional[Contact]:
        return self.repository.update_contact(
            contact_id=contact_id, body=body, user=user
        )

    def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        return self.repository.delete_contact(contact_id=contact_id, user=user)

    def get_upcoming_birthdays(self, user: User, days: int = 7) -> List[Contact]:
        return self.repository.get_upcoming_birthdays(user=user, days=days)
