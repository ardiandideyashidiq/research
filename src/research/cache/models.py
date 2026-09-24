from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class CachedResponse:
    """Cached HTTP or web page response."""

    url: str
    status_code: int
    content: bytes = b""
    content_type: str = "text/html"
    headers: dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str | None = None
    from_cache: bool = True

    @property
    def text(self) -> str:
        """Decode response body as utf-8 string with fallback."""
        try:
            return self.content.decode("utf-8")
        except UnicodeDecodeError:
            return self.content.decode("latin-1", errors="replace")

    def json(self) -> Any:
        """Parse response body as JSON."""
        return json.loads(self.text)

    def is_expired(self) -> bool:
        """Check if cached response has passed its expiration time."""
        if not self.expires_at:
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return datetime.now(UTC) > exp
        except (ValueError, TypeError):
            return False


@dataclass
class CachePolicy:
    """Configurable cache duration and behavior policy."""

    enabled: bool = True
    default_ttl: float | None = None  # None = indefinite for immutable records
    negative_ttl: float = 21600.0  # 6 hours for failures/soft-paywalls
    dynamic_ttl: float = 86400.0  # 24 hours for volatile search queries
