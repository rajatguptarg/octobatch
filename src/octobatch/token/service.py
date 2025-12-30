from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
import jwt

from octobatch.common.settings import ServiceSettings

from .cache import TokenCache, TokenCacheEntry


def _parse_github_timestamp(value: str) -> datetime:
    # GitHub returns ISO timestamps like 2021-01-01T00:00:00Z
    cleaned = value.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned).astimezone(timezone.utc)


class TokenService:
    def __init__(self, settings: ServiceSettings, client: httpx.AsyncClient):
        self.settings = settings
        self.client = client
        self.cache = TokenCache()

    async def close(self) -> None:
        await self.client.aclose()

    def _build_app_jwt(self) -> str:
        if not self.settings.github.app_id:
            raise ValueError("GITHUB_APP_ID must be configured for token minting")

        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 9 * 60,
            "iss": self.settings.github.app_id,
        }
        private_key = self.settings.github.load_private_key_pem()
        return jwt.encode(payload, private_key, algorithm="RS256")

    async def mint_installation_token(self, installation_id: int) -> Dict[str, Any]:
        cache_key = str(self.settings.github.api_base_url)
        cached = self.cache.get(cache_key, installation_id)
        if cached and cached.is_valid(self.settings.github.token_skew_seconds):
            return {
                "token": cached.token,
                "expires_at": cached.expires_at.isoformat(),
                "permissions": cached.permissions,
                "cached": True,
            }

        app_jwt = self._build_app_jwt()
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "octobatch-token-service",
        }
        response = await self.client.post(
            f"/app/installations/{installation_id}/access_tokens", headers=headers
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        expires_at = _parse_github_timestamp(payload["expires_at"])
        entry = TokenCacheEntry(
            token=payload["token"],
            expires_at=expires_at,
            permissions=payload.get("permissions", {}),
        )
        self.cache.set(cache_key, installation_id, entry)
        return {
            "token": payload["token"],
            "expires_at": expires_at.isoformat(),
            "permissions": payload.get("permissions", {}),
            "cached": False,
        }

