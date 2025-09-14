from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, Literal


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


class Contact(BaseModel):
    id: int
    owner_id: int
    name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: Optional[date] = None
    extra: Optional[str] = None

    class Config:
        from_attributes = True


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirm(BaseModel):
    token: str
    new_password: str


# --- лише admin ---
class UserRoleUpdate(BaseModel):
    role: Literal["user", "admin"]