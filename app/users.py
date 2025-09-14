from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter
from io import BytesIO
import cloudinary.uploader as cu

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.deps import require_admin

router = APIRouter(prefix="/users", tags=["users"])

DEFAULT_AVATAR = "https://res.cloudinary.com/demo/image/upload/sample.jpg"


@router.get(
    "/me",
    response_model=schemas.UserOut,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
def me(
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    user = db.get(models.User, current.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


@router.post("/me/avatar", response_model=schemas.UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    data = await file.read()
    try:
        res = cu.upload(
            BytesIO(data),
            folder="avatars",
            public_id=str(current.id),
            overwrite=True,
        )
        current.avatar_url = res["secure_url"]
        db.commit()
        db.refresh(current)
        return current
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


# --- Лише для адміністраторів: скинути аватар користувачу на дефолтний ---
@router.post(
    "/avatar/default",
    response_model=schemas.UserOut,
    dependencies=[Depends(require_admin)],
)
async def set_default_avatar(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.avatar_url = DEFAULT_AVATAR
    db.commit()
    db.refresh(user)
    return user


# Лише для адміністраторів: змінити роль користувача ---
@router.patch(
    "/{user_id}/role",
    response_model=schemas.UserOut,
    dependencies=[Depends(require_admin)],
)
async def update_user_role(
    user_id: int,
    body: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Перевірка валідності ролі додатково до Pydantic (на випадок майбутніх enum-ролей)
    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")

    user.role = body.role
    db.commit()
    db.refresh(user)
    return user
