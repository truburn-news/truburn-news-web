import uuid
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .models import User


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    """
    Fetch logged-in mock wallet user from session.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    user = await session.get(User, uuid.UUID(user_id))
    if not user:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return user


async def get_optional_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await session.get(User, uuid.UUID(user_id))
