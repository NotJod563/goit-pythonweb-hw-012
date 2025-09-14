# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models import Base, User
from app.auth import create_access_token, hash_password
from app.database import get_db
from app.main import app

# Підключення до тестової БД
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:postgres@db:5432/test_contacts_db_hw12"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Тестова база
@pytest.fixture(scope="session")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Токен адмін ролі   
@pytest.fixture
def admin_token(db):
    existing = db.query(User).filter_by(email="admin@example.com").first()
    if existing:
        db.delete(existing)
        db.commit()

    admin = User(
        email="admin@example.com",
        password_hash="notused", 
        is_verified=True,
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token(data={"sub": str(admin.id)})
    return token

# Переоприділення get_db для FastAPI
@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 🛠 Замінюємо маршрут /users/me без RateLimiter
    from fastapi import APIRouter, Depends
    from app.users import get_current_user
    from app.schemas import UserOut

    router = APIRouter(prefix="/users", tags=["users"])

    @router.get("/me", response_model=UserOut)
    async def get_me(current_user: User = Depends(get_current_user)):
        return current_user

    app.router.routes = [route for route in app.router.routes if not getattr(route, "path", "") == "/users/me"]
    app.include_router(router)

    with TestClient(app) as c:
        yield c


# Тестовий токен
@pytest.fixture
def token(db):
    from sqlalchemy.exc import IntegrityError

    email = "contactuser@example.com"

    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password("contactpass"),
            is_verified=True,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter_by(email=email).first()
        else:
            db.refresh(user)

    return create_access_token({"sub": str(user.id)})
