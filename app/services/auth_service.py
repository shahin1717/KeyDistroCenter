import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.db import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, encrypt_private_key_value
from app.core.crypto import generate_keypair
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def register(db: Session, data: RegisterRequest) -> User:
    if get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    public_key, private_key = generate_keypair(
        prime_min=settings.RSA_PRIME_MIN,
        prime_max=settings.RSA_PRIME_MAX,
    )

    user = User(
        username=data.username,
        password=hash_password(data.password),
        public_key_e=public_key[0],
        public_key_n=public_key[1],
        private_key_d=encrypt_private_key_value(private_key[0]),
        private_key_n=encrypt_private_key_value(private_key[1]),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered user: %s", data.username)
    return user


def login(db: Session, data: LoginRequest) -> User:
    user = get_user_by_username(db, data.username)
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    logger.info("Logged in user: %s", data.username)
    return user