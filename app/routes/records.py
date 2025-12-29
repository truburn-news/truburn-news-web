import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_session
from ..deps import get_current_user, get_optional_user
from ..models import (
    Record,
    RecordStatus,
    ReviewRequest,
    ReviewRequestStatus,
    VerificationPoint,
)
from ..schemas import RecordCreate, ReviewRequestCreate
from ..services.analysis import simple_5w1h
from ..services.resolution import calc_resolution_window, compute_resolution_level, resolution_multiplier
from ..services.review import finalize_expired_reviews

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


async def fetch_record(session: AsyncSession, record_id: uuid.UUID) -> Record:
    record = await session.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.get("/feed/{bucket}", response_class=HTMLResponse)
async def feed(
    request: Request,
    bucket: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_user),
) -> HTMLResponse:
    await finalize_expired_reviews(session)
    mapping = {
        "live": [RecordStatus.live],
        "investigating": [RecordStatus.under_review],
        "archive": [RecordStatus.verified, RecordStatus.falsified],
    }
    if bucket not in mapping:
        raise HTTPException(status_code=404, detail="Feed not found")
    result = await session.execute(
        select(Record).where(Record.status.in_(mapping[bucket])).order_by(Record.created_at.desc())
    )
    records = result.scalars().all()
    return templates.TemplateResponse(
        "records/feed.html",
        {
            "request": request,
            "bucket": bucket,
            "records": records,
            "analysis": {r.id: simple_5w1h(r.body) for r in records},
            "current_user": current_user,
        },
    )


@router.get("/report", response_class=HTMLResponse)
async def report_form(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_user),
) -> HTMLResponse:
    if not current_user:
        return RedirectResponse(url="/auth", status_code=303)
    center = datetime.now(timezone.utc)
    default_resolution_hours = settings.review_request_duration_hours
    start, end = calc_resolution_window(center, default_resolution_hours)
    level = compute_resolution_level(start, end)
    return templates.TemplateResponse(
        "records/report.html",
        {
            "request": request,
            "center": center,
            "resolution_hours": default_resolution_hours,
            "start": start,
            "end": end,
            "resolution_level": level,
            "resolution_multiplier": resolution_multiplier(level),
            "current_user": current_user,
        },
    )


@router.post("/records")
async def create_record(
    request: Request,
    title: str = Form(...),
    body: str = Form(...),
    evidence_url: str | None = Form(None),
    time_occurred_start: str | None = Form(None),
    time_occurred_end: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    create_data = RecordCreate(
        title=title,
        body=body,
        evidence_url=evidence_url if evidence_url else None,
        time_occurred_start=_parse_dt(time_occurred_start),
        time_occurred_end=_parse_dt(time_occurred_end),
    )
    if create_data.time_occurred_end <= create_data.time_occurred_start:
        raise HTTPException(status_code=400, detail="time_occurred_end must be after start")
    level = compute_resolution_level(create_data.time_occurred_start, create_data.time_occurred_end)
    record = Record(
        title=create_data.title,
        body=create_data.body,
        evidence_url=str(create_data.evidence_url) if create_data.evidence_url else None,
        time_occurred_start=create_data.time_occurred_start,
        time_occurred_end=create_data.time_occurred_end,
        resolution_level=level,
        resolution_multiplier=resolution_multiplier(level),
        status=RecordStatus.live,
        created_by=current_user.id,
    )
    session.add(record)
    await session.commit()
    return RedirectResponse(url=f"/case/{record.id}", status_code=303)


@router.get("/case/{record_id}", response_class=HTMLResponse)
async def record_detail(
    request: Request,
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_optional_user),
) -> HTMLResponse:
    await finalize_expired_reviews(session)
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
            "current_user": current_user,
        },
    )


@router.post("/case/{record_id}/review-requests")
async def create_review_request(
    request: Request,
    record_id: uuid.UUID,
    reason: str = Form(...),
    evidence_url: str = Form(...),
    is_counter_evidence: str | None = Form("true"),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    record = await fetch_record(session, record_id)
    if record.status in (RecordStatus.verified, RecordStatus.falsified):
        raise HTTPException(status_code=400, detail="Record already finalized")
    if len(reason.strip()) < 200:
        raise HTTPException(status_code=400, detail="Reason must be at least 200 characters")
    if current_user.vp_balance <= 0:
        raise HTTPException(status_code=400, detail="Not enough VP to submit review request")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.review_request_duration_hours)
    review_request = ReviewRequest(
        record_id=record.id,
        requester_id=current_user.id,
        reason=reason,
        evidence_url=evidence_url,
        is_counter_evidence=(is_counter_evidence != "false"),
        status=ReviewRequestStatus.open,
        expires_at=expires_at,
        vp_cost=1,
    )
    record.status = RecordStatus.under_review
    current_user.vp_balance -= review_request.vp_cost
    tx = VerificationPoint(
        user_id=current_user.id,
        record_id=record.id,
        delta=-review_request.vp_cost,
        note="Review Request consumption",
    )
    session.add_all([review_request, tx])
    await session.commit()
    return RedirectResponse(url=f"/case/{record.id}", status_code=303)


@router.get("/records/resolution-preview", response_class=HTMLResponse)
async def resolution_preview(
    request: Request,
    center: str,
    resolution_hours: int = settings.review_request_duration_hours,
) -> HTMLResponse:
    center_dt = _parse_dt(center)
    if not center_dt:
        raise HTTPException(status_code=400, detail="Center datetime required")
    start, end = calc_resolution_window(center_dt, resolution_hours)
    level = compute_resolution_level(start, end)
    return templates.TemplateResponse(
        "partials/resolution_preview.html",
        {
            "request": request,
            "start": start,
            "end": end,
            "resolution_level": level,
            "resolution_multiplier": resolution_multiplier(level),
        },
    )


def _parse_dt(value: str | None) -> datetime:
    if not value:
        raise HTTPException(status_code=400, detail="Datetime required")
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
