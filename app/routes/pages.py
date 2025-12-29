from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..deps import get_current_user, get_optional_user
from ..models import Record, ReviewRequest, VerificationPoint

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding(
    request: Request, current_user=Depends(get_optional_user)
) -> HTMLResponse:
    return templates.TemplateResponse(
        "onboarding.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )


@router.get("/vault", response_class=HTMLResponse)
async def vault(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_user),
) -> HTMLResponse:
    if not current_user:
        return RedirectResponse(url="/auth", status_code=303)
    records_result = await session.execute(
        select(Record).where(Record.created_by == current_user.id).order_by(Record.created_at.desc())
    )
    my_records = records_result.scalars().all()
    rr_result = await session.execute(
        select(ReviewRequest)
        .where(ReviewRequest.requester_id == current_user.id)
        .order_by(ReviewRequest.created_at.desc())
    )
    my_requests = rr_result.scalars().all()
    tx_result = await session.execute(
        select(VerificationPoint)
        .where(VerificationPoint.user_id == current_user.id)
        .order_by(VerificationPoint.created_at.desc())
    )
    transactions = tx_result.scalars().all()
    return templates.TemplateResponse(
        "vault.html",
        {
            "request": request,
            "current_user": current_user,
            "records": my_records,
            "review_requests": my_requests,
            "transactions": transactions,
        },
    )


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, current_user=Depends(get_optional_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )
