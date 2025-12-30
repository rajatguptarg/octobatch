from __future__ import annotations

from fastapi import APIRouter, Depends

from .health import HealthChecker, HealthReport
from .settings import ServiceSettings


def get_settings() -> ServiceSettings:
    return ServiceSettings()


def build_health_router(settings: ServiceSettings) -> APIRouter:
    router = APIRouter()
    checker = HealthChecker(settings)

    @router.get("/healthz", response_model=HealthReport)
    async def healthcheck() -> HealthReport:
        return await checker.run()

    return router

