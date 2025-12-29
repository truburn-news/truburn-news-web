import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session
from ..deps import get_optional_user
from ..models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.get("/auth", response_class=HTMLResponse)
async def auth_page(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_user),
) -> HTMLResponse:
    return templates.TemplateResponse(
        "auth.html",
        {
            "request": request,
            "current_user": current_user,
            "initial_vp": settings.initial_vp,
        },
    )


@router.post("/auth/mock")
async def mock_login(
    request: Request,
    display_name: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    wallet_address = str(uuid.uuid4())
    name = display_name.strip() if display_name else f"Operator-{wallet_address[:4]}"
    user = User(display_name=name, wallet_address=wallet_address, vp_balance=settings.initial_vp)
    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    request.session["user_id"] = str(user.id)
    return RedirectResponse(url="/onboarding", status_code=303)


@router.post("/auth/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/auth", status_code=303)
