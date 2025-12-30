from __future__ import annotations

from fastapi import FastAPI

from octobatch.common.settings import ServiceSettings
from octobatch.common.web import build_health_router


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    current_settings = settings or ServiceSettings(service_name="selection-service")
    app = FastAPI(
        title="Octobatch Selection Service",
        version="0.1.0",
        description="GitHub GraphQL discovery wrapper for repo selection operations.",
    )
    app.include_router(build_health_router(current_settings))

    @app.get("/selection/placeholder")
    async def placeholder() -> dict[str, str]:
        return {"status": "selection service skeleton ready"}

    return app

