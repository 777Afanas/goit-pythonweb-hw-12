from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactCreate, ContactResponse, ContactUpdate
from src.services.auth import AuthService
from src.services.contacts import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/birthdays", response_model=List[ContactResponse])
def get_upcoming_birthdays(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(AuthService.get_current_user),
):
    service = ContactService(db)
    return service.get_upcoming_birthdays(user=user, days=days)


@router.get("/", response_model=List[ContactResponse])
def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(AuthService.get_current_user),
):
    service = ContactService(db)
    return service.get_contacts(
        user=user,
        skip=skip,
        limit=limit,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact_by_id(
    contact_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(AuthService.get_current_user),
):
    service = ContactService(db)
    contact = service.get_contact_by_id(contact_id=contact_id, user=user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    body: ContactCreate,
    db: Session = Depends(get_db),
    user: User = Depends(AuthService.get_current_user),
):
    service = ContactService(db)
    return service.create_contact(body=body, user=user)


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    body: ContactUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(AuthService.get_current_user),
):
    service = ContactService(db)
    contact = service.update_contact(contact_id=contact_id, body=body, user=user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(AuthService.get_current_user),
):
    service = ContactService(db)
    contact = service.delete_contact(contact_id=contact_id, user=user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return None
