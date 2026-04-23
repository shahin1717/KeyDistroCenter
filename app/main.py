import logging
import secrets
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.models.db import create_tables, get_db
from app.services.user_service import get_profile
from app.services.message_service import get_messages
from app.services import auth_service
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


def _safe_validation_detail(e: ValidationError) -> list[dict]:
    return [
        {"loc": err.get("loc", ()), "msg": err.get("msg", "Invalid input"), "type": err.get("type", "value_error")}
        for err in e.errors()
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # --- Static files & templates ---
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY or secrets.token_hex(32),
        max_age=settings.SESSION_MAX_AGE,
        same_site="lax",
        https_only=False,
    )

    # --- API routes ---
    app.include_router(api_router)

    # -----------------------------------------------------------------------
    # Page routes (HTML)
    # -----------------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        user = request.session.get("user")
        return templates.TemplateResponse("index.html", {"request": request, "user": user})

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        if request.session.get("user"):
            return RedirectResponse("/profile", 303)
        return templates.TemplateResponse("login.html", {"request": request})

    @app.get("/register", response_class=HTMLResponse)
    def register_page(request: Request):
        if request.session.get("user"):
            return RedirectResponse("/profile", 303)
        return templates.TemplateResponse("register.html", {"request": request})

    @app.post("/register")
    async def register_submit(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
    ):
        try:
            data = RegisterRequest(username=username, password=password)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_safe_validation_detail(e))
        user = auth_service.register(db, data)
        request.session["user"] = user.username
        return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/login")
    async def login_submit(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
    ):
        try:
            data = LoginRequest(username=username, password=password)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_safe_validation_detail(e))
        user = auth_service.login(db, data)
        request.session["user"] = user.username
        return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/profile", response_class=HTMLResponse)
    def profile_page(request: Request, db: Session = Depends(get_db)):
        user = request.session.get("user")
        if not user:
            return RedirectResponse("/login", 303)
        profile = get_profile(db, user)
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "profile": profile,
        })

    @app.get("/send", response_class=HTMLResponse)
    def send_page(request: Request):
        user = request.session.get("user")
        if not user:
            return RedirectResponse("/login", 303)
        success = request.query_params.get("success")
        return templates.TemplateResponse("send.html", {
            "request": request,
            "user": user,
            "success": "Message sent successfully!" if success else None,
        })

    @app.get("/messages", response_class=HTMLResponse)
    def messages_page(request: Request, db: Session = Depends(get_db)):
        user = request.session.get("user")
        if not user:
            return RedirectResponse("/login", 303)
        msgs = get_messages(db, user)
        return templates.TemplateResponse("messages.html", {
            "request": request,
            "user": user,
            "messages": msgs,
        })

    # Keep /logout as GET for nav link convenience
    @app.get("/logout")
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/login", 303)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)