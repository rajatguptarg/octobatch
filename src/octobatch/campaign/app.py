from __future__ import annotations

from fastapi import FastAPI

from octobatch.common.settings import ServiceSettings
from octobatch.common.web import build_health_router


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    current_settings = settings or ServiceSettings(service_name="campaign-service")
    app = FastAPI(
        title="Octobatch Campaign Service",
        version="0.1.0",
        description="Owns campaign lifecycle, specs, runs, and orchestration hooks.",
    )
    app.include_router(build_health_router(current_settings))

    @app.get("/runs/placeholder")
    async def placeholder() -> dict[str, str]:
        return {"status": "campaign service skeleton ready"}

    return app

