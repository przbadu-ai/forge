from fastapi import APIRouter, Depends

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.deps import get_current_user
from app.api.v1.settings.general import router as general_settings_router
from app.api.v1.settings.mcp_servers import router as mcp_servers_router
from app.api.v1.settings.providers import router as providers_router
from app.models.user import User

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(providers_router, prefix="/settings/providers", tags=["settings"])
api_router.include_router(general_settings_router, prefix="/settings/general", tags=["settings"])
api_router.include_router(
    mcp_servers_router, prefix="/settings/mcp-servers", tags=["mcp-servers"]
)


@api_router.get("/health")
async def health_check(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return {"status": "ok", "service": "forge-api"}
