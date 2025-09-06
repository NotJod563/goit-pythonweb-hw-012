from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter
from io import BytesIO
import cloudinary.uploader as cu

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=schemas.UserOut,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
def me(
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    user = db.get(models.User, current.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

@router.post("/me/avatar", response_model=schemas.UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: models.User = Depends(get_current_user),
):
    user = db.get(models.User, current.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    data = await file.read()
    res = cu.upload(BytesIO(data), folder="avatars", public_id=str(user.id), overwrite=True)
    user.avatar_url = res["secure_url"]
    db.commit()
    db.refresh(user)
    return user
