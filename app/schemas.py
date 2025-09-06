from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

# ------ Users ------
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    avatar_url: Optional[str] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ------ Contacts ------
class ContactBase(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: Optional[date] = None
    extra: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    extra: Optional[str] = None

class Contact(ContactBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True
