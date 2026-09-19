from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


class ContactRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_contacts(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> List[Contact]:
        query = self.db.query(Contact).filter(Contact.user_id == user.id)
        if first_name:
            query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            query = query.filter(Contact.email.ilike(f"%{email}%"))
        return query.offset(skip).limit(limit).all()

    def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        return (
            self.db.query(Contact)
            .filter(Contact.id == contact_id, Contact.user_id == user.id)
            .first()
        )

    def create_contact(self, body: ContactCreate, user: User) -> Contact:
        contact = Contact(**body.model_dump(), user_id=user.id)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Optional[Contact]:
        contact = self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.model_dump().items():
                setattr(contact, key, value)
            self.db.commit()
            self.db.refresh(contact)
        return contact

    def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        contact = self.get_contact_by_id(contact_id, user)
        if contact:
            self.db.delete(contact)
            self.db.commit()
        return contact

    def get_upcoming_birthdays(self, user: User, days: int = 7) -> List[Contact]:
        today = date.today()
        contacts = self.db.query(Contact).filter(Contact.user_id == user.id).all()
        upcoming = []

        for contact in contacts:
            if not contact.birthday:
                continue
            try:
                birthday_this_year = contact.birthday.replace(year=today.year)
            except ValueError:
                # Обробка 29 лютого для невисокосного року
                birthday_this_year = contact.birthday.replace(year=today.year, day=28)

            if birthday_this_year < today:
                try:
                    birthday_this_year = contact.birthday.replace(year=today.year + 1)
                except ValueError:
                    birthday_this_year = contact.birthday.replace(
                        year=today.year + 1, day=28
                    )

            delta_days = (birthday_this_year - today).days
            if 0 <= delta_days <= days:
                upcoming.append(contact)

        return upcoming
