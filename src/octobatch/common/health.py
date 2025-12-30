from __future__ import annotations

import asyncio
import time
from typing import Any, Iterable, List

import aioboto3
import asyncpg
import httpx
from pydantic import BaseModel
from redis import asyncio as aioredis

from .settings import ServiceSettings


class HealthStatus(BaseModel):
    name: str
    healthy: bool
    latency_ms: float | None = None
    detail: str | None = None


class HealthReport(BaseModel):
    service: str
    environment: str
    healthy: bool
    checks: List[HealthStatus]


class HealthChecker:
    def __init__(self, settings: ServiceSettings):
        self.settings = settings

    async def check_postgres(self) -> HealthStatus:
        if not self.settings.postgres.enabled:
            return HealthStatus(name="postgres", healthy=True, detail="disabled")
        if not self.settings.postgres.dsn:
            return HealthStatus(
                name="postgres", healthy=False, detail="POSTGRES_DSN is not configured"
            )

        start = time.perf_counter()
        connection = None
        try:
            connection = await asyncpg.connect(
                self.settings.postgres.dsn,
                timeout=self.settings.postgres.connect_timeout_seconds,
            )
            await connection.execute("SELECT 1")
            latency = (time.perf_counter() - start) * 1000
            return HealthStatus(name="postgres", healthy=True, latency_ms=latency)
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return HealthStatus(
                name="postgres",
                healthy=False,
                latency_ms=latency,
                detail=str(exc),
            )
        finally:
            if connection:
                await connection.close()

    async def check_redis(self) -> HealthStatus:
        if not self.settings.redis.enabled:
            return HealthStatus(name="redis", healthy=True, detail="disabled")
        if not self.settings.redis.url:
            return HealthStatus(
                name="redis", healthy=False, detail="REDIS_URL is not configured"
            )

        start = time.perf_counter()
        client = aioredis.from_url(self.settings.redis.url, encoding="utf-8")
        try:
            await asyncio.wait_for(
                client.ping(), timeout=self.settings.redis.ping_timeout_seconds
            )
            latency = (time.perf_counter() - start) * 1000
            return HealthStatus(name="redis", healthy=True, latency_ms=latency)
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return HealthStatus(
                name="redis",
                healthy=False,
                latency_ms=latency,
                detail=str(exc),
            )
        finally:
            await client.aclose()

    async def check_blobstore(self) -> HealthStatus:
        if not self.settings.blobstore.enabled:
            return HealthStatus(name="blobstore", healthy=True, detail="disabled")
        if not self.settings.blobstore.endpoint_url:
            return HealthStatus(
                name="blobstore",
                healthy=False,
                detail="BLOBSTORE_ENDPOINT is not configured",
            )
        session = aioboto3.Session()
        start = time.perf_counter()
        try:
            async with session.client(
                "s3",
                endpoint_url=self.settings.blobstore.endpoint_url,
                region_name=self.settings.blobstore.region_name,
                aws_access_key_id=self.settings.blobstore.access_key_id,
                aws_secret_access_key=self.settings.blobstore.secret_access_key,
                aws_session_token=self.settings.blobstore.session_token,
            ) as client:
                if self.settings.blobstore.bucket:
                    await client.head_bucket(Bucket=self.settings.blobstore.bucket)
                else:
                    await client.list_buckets()
            latency = (time.perf_counter() - start) * 1000
            return HealthStatus(name="blobstore", healthy=True, latency_ms=latency)
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - start) * 1000
            return HealthStatus(
                name="blobstore",
                healthy=False,
                latency_ms=latency,
                detail=str(exc),
            )

    async def check_github(self) -> HealthStatus:
        start = time.perf_counter()
        async with httpx.AsyncClient(
            timeout=self.settings.healthcheck_timeout_seconds
        ) as client:
            try:
                response = await client.get(
                    f"{self.settings.github.api_base_url}/meta",
                    headers={"Accept": "application/vnd.github+json"},
                )
                latency = (time.perf_counter() - start) * 1000
                healthy = response.status_code < 400
                detail = None if healthy else f"GitHub meta returned {response.status_code}"
                return HealthStatus(
                    name="github_api",
                    healthy=healthy,
                    latency_ms=latency,
                    detail=detail,
                )
            except Exception as exc:  # noqa: BLE001
                latency = (time.perf_counter() - start) * 1000
                return HealthStatus(
                    name="github_api",
                    healthy=False,
                    latency_ms=latency,
                    detail=str(exc),
                )

    async def run(self) -> HealthReport:
        checks: Iterable[asyncio.Task[Any]] = [
            asyncio.create_task(self.check_postgres()),
            asyncio.create_task(self.check_redis()),
            asyncio.create_task(self.check_blobstore()),
            asyncio.create_task(self.check_github()),
        ]
        statuses: list[HealthStatus] = []
        for task in checks:
            try:
                statuses.append(await task)
            except Exception as exc:  # noqa: BLE001
                statuses.append(
                    HealthStatus(name="unknown", healthy=False, detail=str(exc))
                )

        healthy = all(status.healthy for status in statuses)
        return HealthReport(
            service=self.settings.service_name,
            environment=self.settings.environment,
            healthy=healthy,
            checks=statuses,
        )
