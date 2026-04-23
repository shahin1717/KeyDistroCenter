from pydantic import BaseModel


class UserProfile(BaseModel):
    username: str
    public_key_e: int
    public_key_n: int


class PublicKeyResponse(BaseModel):
    username: str
    e: int
    n: int