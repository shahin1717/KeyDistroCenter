from fastapi import APIRouter, Depends, Form, Request, status
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _safe_validation_detail(e: ValidationError) -> list[dict]:
    return [
        {"loc": err.get("loc", ()), "msg": err.get("msg", "Invalid input"), "type": err.get("type", "value_error")}
        for err in e.errors()
    ]


@router.post("/register")
async def register(
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


@router.post("/login")
async def login(
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


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)