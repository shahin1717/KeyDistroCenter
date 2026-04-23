from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.schemas.user import UserProfile, PublicKeyResponse
from app.services import user_service
from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user),
):
    return user_service.get_profile(db, username)


@router.get("/{username}/pubkey", response_model=PublicKeyResponse)
def get_pubkey(username: str, db: Session = Depends(get_db)):
    return user_service.get_public_key(db, username)