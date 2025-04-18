from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Create a proper router for the /me endpoint
me_router = APIRouter()
me_router.get("/me", tags=["Users"])(auth.get_current_user_info)
api_router.include_router(me_router, prefix="/users")
