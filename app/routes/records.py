import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session
from ..models import Record, ReviewRequest, ReviewStatus
from ..schemas import RecordCreate, ReviewRequestCreate
from ..services.analysis import simple_5w1h

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


async def fetch_record(session: AsyncSession, record_id: uuid.UUID) -> Record:
    record = await session.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.get("/records", response_class=HTMLResponse)
async def list_records(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    result = await session.execute(select(Record).order_by(Record.created_at.desc()))
    records = result.scalars().all()
    center = datetime.now(timezone.utc)
    default_resolution_hours = settings.review_request_duration_hours
    start, end = _calc_window(center, default_resolution_hours)
    return templates.TemplateResponse(
        "records/index.html",
        {
            "request": request,
            "records": records,
            "analysis": {r.id: simple_5w1h(r.body) for r in records},
            "center": center,
            "resolution_hours": default_resolution_hours,
            "start": start,
            "end": end,
        },
    )


@router.post("/records")
async def create_record(
    request: Request,
    title: str = Form(...),
    body: str = Form(...),
    source_url: str | None = Form(None),
    time_occurred_start: str | None = Form(None),
    time_occurred_end: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    create_data = RecordCreate(
        title=title,
        body=body,
        source_url=source_url if source_url else None,
        time_occurred_start=_parse_dt(time_occurred_start),
        time_occurred_end=_parse_dt(time_occurred_end),
    )
    if not create_data.time_occurred_start or not create_data.time_occurred_end:
        raise HTTPException(status_code=400, detail="time_occurred_start/end are required")
    if create_data.time_occurred_start > create_data.time_occurred_end:
        raise HTTPException(status_code=400, detail="Start must be before end")

    record = Record(
        title=create_data.title,
        body=create_data.body,
        source_url=str(create_data.source_url) if create_data.source_url else None,
        time_occurred_start=create_data.time_occurred_start,
        time_occurred_end=create_data.time_occurred_end,
    )
    session.add(record)
    await session.commit()
    return RedirectResponse(url=f"/records/{record.id}", status_code=303)


@router.get("/records/{record_id}", response_class=HTMLResponse)
async def record_detail(
    request: Request, record_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    record = await fetch_record(session, record_id)
    analysis = simple_5w1h(record.body)
    result = await session.execute(
        select(ReviewRequest).where(ReviewRequest.record_id == record.id).order_by(ReviewRequest.created_at.desc())
    )
    review_requests = result.scalars().all()
    return templates.TemplateResponse(
        "records/detail.html",
        {
            "request": request,
            "record": record,
            "analysis": analysis,
            "review_requests": review_requests,
            "default_resolution_hours": settings.review_request_duration_hours,
        },
    )


@router.post("/records/{record_id}/review-requests")
async def create_review_request(
    request: Request, record_id: uuid.UUID, session: AsyncSession = Depends(get_session)
):
    record = await fetch_record(session, record_id)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.review_request_duration_hours)
    review_request = ReviewRequest(record_id=record.id, status=ReviewStatus.pending, expires_at=expires_at)
    session.add(review_request)
    await session.commit()
    return RedirectResponse(url=f"/records/{record.id}", status_code=303)


@router.get("/records/resolution-preview", response_class=HTMLResponse)
async def resolution_preview(
    request: Request,
    center: str,
    resolution_hours: int = settings.review_request_duration_hours,
) -> HTMLResponse:
    center_dt = _parse_dt(center)
    if not center_dt:
        raise HTTPException(status_code=400, detail="Center datetime required")
    start, end = _calc_window(center_dt, resolution_hours)
    return templates.TemplateResponse(
        "partials/resolution_preview.html",
        {
            "request": request,
            "start": start,
            "end": end,
        },
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # Ensure timezone-aware; assume UTC if missing offset.
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")


def _calc_window(center: datetime, resolution_hours: int) -> tuple[datetime, datetime]:
    half = timedelta(hours=resolution_hours / 2)
    return center - half, center + half
