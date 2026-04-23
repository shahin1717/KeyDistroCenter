from fastapi import APIRouter
from app.api.v1 import auth, messages, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(messages.router)
api_router.include_router(users.router)