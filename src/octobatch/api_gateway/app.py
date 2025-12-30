from __future__ import annotations

from fastapi import FastAPI

from octobatch.common.settings import ServiceSettings
from octobatch.common.web import build_health_router


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    current_settings = settings or ServiceSettings(service_name="api-gateway")
    app = FastAPI(
        title="Octobatch API Gateway",
        version="0.1.0",
        description="FastAPI entrypoint for Octobatch control-plane services.",
    )
    app.include_router(build_health_router(current_settings))

    @app.get("/status")
    async def status() -> dict[str, str]:
        return {"service": current_settings.service_name, "environment": current_settings.environment}

    return app

