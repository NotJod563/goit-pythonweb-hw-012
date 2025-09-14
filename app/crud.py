from sqlalchemy.orm import Session
from datetime import date, timedelta
from app import models, schemas

def get_contact(db: Session, contact_id: int, owner_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == owner_id).first()

def get_contact_by_email(db: Session, email: str, owner_id: int):
    return db.query(models.Contact).filter(models.Contact.email == email, models.Contact.owner_id == owner_id).first()

def get_contacts(db: Session, owner_id: int, skip: int = 0, limit: int = 100,
                 name: str | None = None, last_name: str | None = None, email: str | None = None):
    q = db.query(models.Contact).filter(models.Contact.owner_id == owner_id)
    if name: q = q.filter(models.Contact.name.ilike(f"%{name}%"))
    if last_name: q = q.filter(models.Contact.last_name.ilike(f"%{last_name}%"))
    if email: q = q.filter(models.Contact.email.ilike(f"%{email}%"))
    return q.offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate, owner_id: int):
    db_contact = models.Contact(owner_id=owner_id, **contact.dict())
    db.add(db_contact); db.commit(); db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, owner_id: int, updates: schemas.ContactUpdate):
    db_contact = get_contact(db, contact_id, owner_id)
    if not db_contact: return None
    data = updates.dict(exclude_unset=True)
    for k, v in data.items(): setattr(db_contact, k, v)
    db.add(db_contact); db.commit(); db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int, owner_id: int) -> bool:
    db_contact = get_contact(db, contact_id, owner_id)
    if not db_contact: return False
    db.delete(db_contact); db.commit()
    return True

def get_upcoming_birthdays(db: Session, owner_id: int, days: int = 7):
    from datetime import date
    today = date.today(); end = today + timedelta(days=days)
    results = []
    contacts = db.query(models.Contact).filter(models.Contact.owner_id == owner_id, models.Contact.birthday.isnot(None)).all()
    for c in contacts:
        bday_this_year = c.birthday.replace(year=today.year)
        next_bday = bday_this_year if bday_this_year >= today else c.birthday.replace(year=today.year + 1)
        if today <= next_bday <= end:
            results.append((next_bday, c))
    results.sort(key=lambda t: t[0])
    return [c for _, c in results]

def search_contacts(db: Session, owner_id: int, query: str):
    return db.query(models.Contact).filter(
        models.Contact.owner_id == owner_id,
        models.Contact.name.ilike(f"%{query}%")
    ).all()

