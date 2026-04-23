import bcrypt
from fastapi import Request, HTTPException, status
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

settings = get_settings()
_ENC_PREFIX = "enc:"


def _get_fernet() -> Fernet:
    key = settings.PRIVATE_KEY_ENCRYPTION_KEY.encode()
    return Fernet(key)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def encrypt_private_key_value(value: int) -> str:
    token = _get_fernet().encrypt(str(value).encode()).decode()
    return f"{_ENC_PREFIX}{token}"


def decrypt_private_key_value(value: int | str) -> int:
    # Backward compatibility: old rows may still store raw numeric values.
    if isinstance(value, int):
        return value

    if value.startswith(_ENC_PREFIX):
        token = value[len(_ENC_PREFIX):]
        try:
            raw = _get_fernet().decrypt(token.encode()).decode()
            return int(raw)
        except (InvalidToken, ValueError) as e:
            raise ValueError("Invalid encrypted private key value") from e

    try:
        return int(value)
    except ValueError as e:
        raise ValueError("Unsupported private key format") from e


def get_current_user(request: Request) -> str:
    """Return username from session or raise 401."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_guest(request: Request) -> None:
    """Raise 403 if user is already logged in."""
    if request.session.get("user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Already authenticated",
        )