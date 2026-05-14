from __future__ import annotations

from fastapi import Depends, FastAPI

from ai_orchestrator.api.deps import require_api_auth
from ai_orchestrator.api.routes.approvals import router as approvals_router
from ai_orchestrator.api.routes.workflows import router as workflows_router
from ai_orchestrator.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, dependencies=[Depends(require_api_auth)])
    app.include_router(workflows_router)
    app.include_router(approvals_router)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
