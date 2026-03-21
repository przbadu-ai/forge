from fastapi import APIRouter, Depends

from app.api.v1.auth import router as auth_router
from app.api.v1.deps import get_current_user
from app.models.user import User

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])


@api_router.get("/health")
async def health_check(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return {"status": "ok", "service": "forge-api"}
