import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.db import Message, User
from app.schemas.message import SendMessageRequest, MessageResponse
from app.core.crypto import rsa_encrypt, rsa_decrypt, caesar_encrypt, caesar_decrypt
from app.core.security import decrypt_private_key_value
from app.core.config import get_settings
from app.services.auth_service import get_user_by_username

logger = logging.getLogger(__name__)
settings = get_settings()


def send_message(db: Session, sender_username: str, data: SendMessageRequest) -> Message:
    recipient: User | None = get_user_by_username(db, data.recipient_username)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{data.recipient_username}' not found",
        )

    public_key = (recipient.public_key_e, recipient.public_key_n)
    if data.caesar_key >= public_key[1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Caesar key is too large for recipient's RSA key",
        )

    encrypted_key = rsa_encrypt(data.caesar_key, public_key)
    encrypted_message = caesar_encrypt(data.message, data.caesar_key)

    msg = Message(
        sender_username=sender_username,
        recipient_username=data.recipient_username,
        encrypted_key=encrypted_key,
        encrypted_message=encrypted_message,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    logger.info("Message sent from %s to %s", sender_username, data.recipient_username)
    return msg


def get_messages(db: Session, username: str) -> list[MessageResponse]:
    user: User | None = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    private_key = (
        decrypt_private_key_value(user.private_key_d),
        decrypt_private_key_value(user.private_key_n),
    )
    messages = db.query(Message).filter(Message.recipient_username == username).all()

    results = []
    for msg in messages:
        try:
            key = rsa_decrypt(msg.encrypted_key, private_key)
            text = caesar_decrypt(msg.encrypted_message, key)
            results.append(MessageResponse(
                id=msg.id,
                sender=msg.sender_username,
                message=text,
                caesar_key=key,
            ))
        except Exception as e:
            logger.error("Failed to decrypt message %d: %s", msg.id, e)
            results.append(MessageResponse(
                id=msg.id,
                sender=msg.sender_username,
                message="[decryption failed]",
                caesar_key=0,
            ))
    return results


def delete_message(db: Session, message_id: int, username: str) -> None:
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if msg.recipient_username != username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your message")
    db.delete(msg)
    db.commit()


def cleanup_expired_messages(db: Session) -> int:
    """Delete messages older than MESSAGE_TTL_MINUTES. Returns count deleted."""
    cutoff = datetime.utcnow() - timedelta(minutes=settings.MESSAGE_TTL_MINUTES)
    expired = db.query(Message).filter(Message.created_at < cutoff).all()
    count = len(expired)
    for msg in expired:
        db.delete(msg)
    db.commit()
    if count:
        logger.info("Cleanup: deleted %d expired messages", count)
    return count