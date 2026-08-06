from fastapi import APIRouter

from app.api.v1.endpoints.attendance import router as attendance_router
from app.api.v1.endpoints.permissions import router as permissions_router
from app.api.v1.endpoints.schedules import router as schedules_router
from app.api.v1.endpoints.users import router as users_router


api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(attendance_router)
api_router.include_router(schedules_router)
api_router.include_router(permissions_router)
