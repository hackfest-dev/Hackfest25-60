from fastapi import APIRouter
from app.core.auth import get_current_active_user
from app.api.v1.endpoints import auth, chat, podcast

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chats", tags=["Chat"])
api_router.include_router(podcast.router, prefix="/podcast", tags=["Podcast"])

# Create a proper router for the /me endpoint
me_router = APIRouter()
me_router.get("/me", tags=["Users"])(auth.get_current_user_info)
api_router.include_router(me_router, prefix="/users")
