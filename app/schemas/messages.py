from pydantic import BaseModel, field_validator


class SendMessageRequest(BaseModel):
    recipient_username: str
    message: str
    caesar_key: int

    @field_validator("caesar_key")
    @classmethod
    def key_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Caesar key must be a positive integer")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v


class MessageResponse(BaseModel):
    id: int
    sender: str
    message: str
    caesar_key: int