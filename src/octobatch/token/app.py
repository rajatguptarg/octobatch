from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException

from octobatch.common.settings import ServiceSettings
from octobatch.common.web import build_health_router

from .service import TokenService


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    current_settings = settings or ServiceSettings(service_name="token-service")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = httpx.AsyncClient(
            base_url=str(current_settings.github.api_base_url).rstrip("/"),
            timeout=max(current_settings.healthcheck_timeout_seconds, 10.0),
        )
        token_service = TokenService(current_settings, client)
        app.state.token_service = token_service
        try:
            yield
        finally:
            await token_service.close()

    app = FastAPI(
        title="Octobatch Token Service",
        version="0.1.0",
        description="Exchanges GitHub App credentials for installation tokens.",
        lifespan=lifespan,
    )

    app.include_router(build_health_router(current_settings))

    def get_token_service() -> TokenService:
        return app.state.token_service  # type: ignore[no-any-return]

    @app.get("/tokens/installations/{installation_id}")
    async def get_installation_token(
        installation_id: int, token_service: TokenService = Depends(get_token_service)
    ) -> dict:
        try:
            return await token_service.mint_installation_token(installation_id)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.text,
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app
