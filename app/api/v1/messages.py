from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.schemas.message import SendMessageRequest, MessageResponse
from app.services import message_service
from app.core.security import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=list[MessageResponse])
def list_messages(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user),
):
    return message_service.get_messages(db, username)


@router.post("")
async def send_message(
    request: Request,
    recipient_username: str = Form(...),
    message: str = Form(...),
    caesar_key: int = Form(...),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user),
):
    data = SendMessageRequest(
        recipient_username=recipient_username,
        message=message,
        caesar_key=caesar_key,
    )
    message_service.send_message(db, username, data)
    return RedirectResponse(url="/send?success=1", status_code=status.HTTP_303_SEE_OTHER)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user),
):
    message_service.delete_message(db, message_id, username)