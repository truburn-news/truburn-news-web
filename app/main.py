from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .routes import auth, pages, records


settings = get_settings()
app = FastAPI(title="Truburn Phase1", version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="truburn_session",
    max_age=60 * 60 * 24 * 30,  # 30 days
    same_site="lax",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/feed/live")


app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(records.router)
