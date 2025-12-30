from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple


@dataclass
class TokenCacheEntry:
    token: str
    expires_at: datetime
    permissions: dict

    def is_valid(self, skew_seconds: int) -> bool:
        now = datetime.now(tz=timezone.utc)
        return self.expires_at - timedelta(seconds=skew_seconds) > now


class TokenCache:
    def __init__(self) -> None:
        self._cache: Dict[Tuple[str, int], TokenCacheEntry] = {}

    def get(self, api_base_url: str, installation_id: int) -> TokenCacheEntry | None:
        return self._cache.get((api_base_url, installation_id))

    def set(
        self,
        api_base_url: str,
        installation_id: int,
        entry: TokenCacheEntry,
    ) -> TokenCacheEntry:
        self._cache[(api_base_url, installation_id)] = entry
        return entry
