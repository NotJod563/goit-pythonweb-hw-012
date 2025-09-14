from fastapi import Depends, HTTPException, status
from app.auth import get_current_user
from app.models import User


async def require_admin(current: User = Depends(get_current_user)):
    if current is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    role_value = current.role.value if hasattr(current.role, "value") else str(current.role)

    if role_value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only",
        )
    return current
