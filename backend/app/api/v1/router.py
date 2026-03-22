from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.files import router as files_router
from app.api.v1.health_diagnostics import router as diagnostics_router
from app.api.v1.settings.embeddings import router as embeddings_settings_router
from app.api.v1.settings.general import router as general_settings_router
from app.api.v1.settings.mcp_servers import router as mcp_servers_router
from app.api.v1.settings.providers import router as providers_router
from app.api.v1.settings.skills import router as skills_router
from app.api.v1.settings.web_search import router as web_search_settings_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(files_router, prefix="/files", tags=["files"])
api_router.include_router(providers_router, prefix="/settings/providers", tags=["settings"])
api_router.include_router(general_settings_router, prefix="/settings/general", tags=["settings"])
api_router.include_router(
    embeddings_settings_router, prefix="/settings/embeddings", tags=["settings"]
)
api_router.include_router(
    web_search_settings_router, prefix="/settings/web-search", tags=["settings"]
)
api_router.include_router(mcp_servers_router, prefix="/settings/mcp-servers", tags=["mcp-servers"])
api_router.include_router(skills_router, prefix="/settings/skills", tags=["skills"])
api_router.include_router(diagnostics_router, prefix="/diagnostics", tags=["diagnostics"])


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "forge-api"}
