from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.db import User
from app.schemas.user import UserProfile, PublicKeyResponse
from app.services.auth_service import get_user_by_username


def get_profile(db: Session, username: str) -> UserProfile:
    user: User | None = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserProfile(
        username=user.username,
        public_key_e=user.public_key_e,
        public_key_n=user.public_key_n,
    )


def get_public_key(db: Session, username: str) -> PublicKeyResponse:
    user: User | None = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return PublicKeyResponse(username=user.username, e=user.public_key_e, n=user.public_key_n)