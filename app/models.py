from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Text,
    UniqueConstraint,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Integer, default=0)
    avatar_url = Column(String, nullable=True)
    role = Column(Enum(RoleEnum, name="roleenum"), default=RoleEnum.user, nullable=False)

    contacts = relationship(
        "Contact",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("email", name="uq_contacts_email"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, index=True, nullable=False)
    birthday = Column(Date, nullable=True)
    extra = Column(Text, nullable=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner = relationship("User", back_populates="contacts")
