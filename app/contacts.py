from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["default"])


def _field_names():
    first = "first_name" if hasattr(models.Contact, "first_name") else "name"
    phone = "phone_number" if hasattr(models.Contact, "phone_number") else "phone"
    return first, phone


def _to_model_kwargs(payload: Dict[str, Any]) -> Dict[str, Any]:
    first_field, phone_field = _field_names()
    out: Dict[str, Any] = {}
    if "first_name" in payload:
        out[first_field] = payload["first_name"]
    if "name" in payload:
        out[first_field] = payload["name"]
    if "phone_number" in payload:
        out[phone_field] = payload["phone_number"]
    if "phone" in payload:
        out[phone_field] = payload["phone"]
    for k in ("last_name", "email", "birthday", "extra"):
        if k in payload:
            out[k] = payload[k]
    return out


def _ensure_owner(obj_owner_id: int, user_id: int):
    if obj_owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def _to_search_filter(db: Session, user_id: int, search: Optional[str]):
    q = db.query(models.Contact).filter(models.Contact.owner_id == user_id)
    if search:
        like = f"%{search.lower()}%"
        first_field, _ = _field_names()
        first_col = getattr(models.Contact, first_field)
        q = q.filter(
            or_(
                first_col.ilike(like),
                models.Contact.last_name.ilike(like),
                models.Contact.email.ilike(like),
            )
        )
    return q


def _check_duplicates_global(db: Session, kwargs: Dict[str, Any]):
    email = kwargs.get("email")
    if email:
        exists_email = db.query(models.Contact).filter(models.Contact.email == email).first()
        if exists_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact with this email already exists")

    first_field, _ = _field_names()
    first_name = kwargs.get(first_field)
    last_name = kwargs.get("last_name")
    if first_name and last_name:
        first_col = getattr(models.Contact, first_field)
        exists_name = (
            db.query(models.Contact)
            .filter(and_(first_col == first_name, models.Contact.last_name == last_name))
            .first()
        )
        if exists_name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact with this name already exists")


@router.post("/", response_model=schemas.Contact, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_in: schemas.ContactCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    data = contact_in.dict(exclude_unset=True)
    kwargs = _to_model_kwargs(data)
    kwargs["owner_id"] = user.id

    _check_duplicates_global(db, kwargs)

    contact = models.Contact(**kwargs)
    db.add(contact)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact already exists")
    db.refresh(contact)
    return contact


@router.get("/", response_model=List[schemas.Contact])
def read_contacts(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = _to_search_filter(db, user.id, search)
    return q.order_by(models.Contact.id.asc()).all()


@router.get("/{contact_id}", response_model=schemas.Contact)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    contact = db.get(models.Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _ensure_owner(contact.owner_id, user.id)
    return contact


@router.patch("/{contact_id}", response_model=schemas.Contact)
def update_contact(
    contact_id: int,
    contact_in: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    contact = db.get(models.Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _ensure_owner(contact.owner_id, user.id)

    data = contact_in.dict(exclude_unset=True)
    kwargs = _to_model_kwargs(data)

    tmp = {}
    tmp.update({k: getattr(contact, k) for k in contact.__table__.columns.keys() if hasattr(contact, k)})
    tmp.update(kwargs)
    _check_duplicates_global(db, tmp)

    for k, v in kwargs.items():
        setattr(contact, k, v)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    contact = db.get(models.Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _ensure_owner(contact.owner_id, user.id)
    db.delete(contact)
    db.commit()
    return None


@router.get("/upcoming-birthdays", response_model=List[schemas.Contact])
def upcoming_birthdays(
    days: int = Query(7, ge=1, le=366),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    today = date.today()
    end = today + timedelta(days=days)
    contacts = db.query(models.Contact).filter(models.Contact.owner_id == user.id).all()

    def next_bday(d: date) -> date:
        year = today.year
        nb = date(year, d.month, d.day)
        if nb < today:
            nb = date(year + 1, d.month, d.day)
        return nb

    result: List[models.Contact] = []
    for c in contacts:
        if c.birthday is None:
            continue
        nb = next_bday(c.birthday)
        if today <= nb <= end:
            result.append(c)
    return result
