from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from app.database import get_db
from app import models, schemas
from app.models import User
from app.config import settings
from app.cache import get_user_from_cache, cache_user

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Перевіряє, чи відповідає пароль хешованому паролю.

    :param plain: Пароль у відкритому вигляді.
    :param hashed: Хешований пароль з бази даних.
    :return: True, якщо паролі збігаються.
    """
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    """
    Хешує plain password для збереження в БД.

    :param plain: Пароль у відкритому вигляді.
    :return: Хешований пароль.
    """
    return pwd_context.hash(plain)


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """
    Створює JWT access token для користувача.

    :param data: Дані для токена. Має містити ключ "sub".
    :param expires_minutes: Час дії токена в хвилнах.
    :return: JWT токен.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False,
)


def get_token_from_header(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return auth.split(" ", 1)[1]


cred_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _serialize_user(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "role": u.role.value if hasattr(u.role, "value") else str(u.role),
        "is_verified": u.is_verified,
        "avatar_url": u.avatar_url,
    }


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User:
    """
    Отримує поточного авторизованого користувача.

    :param token: JWTтокен з заголовка Authorization.
    :param db: Сесія SQLAlchemy.
    :return: Обєкт користувача.
    :raises HTTPException: Якщо токен недійсний .
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if not user_id:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(User).get(user_id)
    if not user:
        raise cred_exc

    return user


@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_in: schemas.UserCreate, bg: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Реєструє нового користувача та надсилає лист з підтвердженням email.

    :param user_in: Дані нового користувача (email, password).
    :param bg: Об'єкт BackgroundTasks для асинхронного надсилання листа.
    :param db: Сесія бази даних SQLAlchemy.
    :return: Об'єкт користувача у відповіді.
    :raises HTTPException: 409 — якщо користувач уже існує.
    """
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    user = models.User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    msg = MessageSchema(
        subject="Verify your email",
        recipients=[user.email],
        body=f"Your verification token: {token}",
        subtype="plain",
    )

    async def _send():
        await FastMail(conf).send_message(msg)

    bg.add_task(_send)
    return user


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Авторизує користувача за email та паролем.

    :param form: Об'єкт із username (email) та паролем.
    :param db: Сесія бази даних.
    :return: JWT токен.
    :raises HTTPException: Якщо авторизація не вдалася або email не підтверджено.
    """
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not verified")

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, token_type="bearer")


@router.get("/verify", response_model=str)
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Верифікує користувача через токен з email.

    :param token: JWT токен з підтвердження email.
    :param db: Сесія БД.
    :return: Рядок "verified".
    :raises HTTPException: Якщо токен або користувач недійсні.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        user_id = int(sub)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user.is_verified = True
    db.commit()
    return "verified"


@router.post("/reset/request")
def reset_request(body: schemas.ResetRequest, db: Session = Depends(get_db)):
    """
    Генерує токен для скидання пароля та друкує його в консоль.

    :param body: Об'єкт з email користувача.
    :param db: Сесія БД.
    :return: JSON: {"ok": True}
    """
    user = db.query(User).filter_by(email=body.email).first()
    if not user:
        return {"ok": True}

    payload = {
        "sub": str(user.id),
        "purpose": "pwd_reset",
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    print(f"[DEV] Reset token for {user.email}:\n{token}")
    return {"ok": True, "token": token}


@router.post("/reset/confirm")
def reset_confirm(body: schemas.ResetConfirm, db: Session = Depends(get_db)):
    """
    Приймає токен скидання пароля та новий пароль, оновлює в БД.

    :param body: Об'єкт із токеном та новим паролем.
    :param db: Сесія БД.
    :return: JSON: {"ok": True}
    :raises HTTPException: Якщо токен невалідний або користувача не знайдено.
    """
    try:
        data = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if data.get("purpose") != "pwd_reset":
            raise ValueError("Invalid purpose")

        user = db.query(User).get(int(data["sub"]))
        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(body.new_password)
        db.commit()
        return {"ok": True}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
