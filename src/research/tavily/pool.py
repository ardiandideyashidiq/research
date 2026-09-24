from __future__ import annotations

import threading
import time
from typing import Literal

from loguru import logger

from research.tavily.models import APIKeyStatus

LoadBalanceStrategy = Literal["round_robin", "least_used"]


class APIKeyPool:
    """Thread-safe API key pool with automated round-robin and least-used load balancing."""

    def __init__(
        self,
        api_keys: list[str],
        *,
        strategy: LoadBalanceStrategy = "round_robin",
    ) -> None:
        if not api_keys:
            msg = "At least one Tavily API key must be provided."
            raise ValueError(msg)

        self._keys: list[APIKeyStatus] = [APIKeyStatus(key=k.strip()) for k in api_keys if k.strip()]
        self.strategy = strategy
        self._index: int = -1
        self._lock = threading.Lock()

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    @property
    def active_keys(self) -> list[APIKeyStatus]:
        return [k for k in self._keys if not k.is_exhausted]

    def next_key(self) -> APIKeyStatus:
        """Select the next available API key according to the balancing strategy."""
        with self._lock:
            active = self.active_keys
            if not active:
                # If all exhausted, log warning and attempt recovery
                logger.warning("All Tavily API keys marked exhausted! Resetting exhausted status for retry.")
                for k in self._keys:
                    k.is_exhausted = False
                active = self._keys

            if self.strategy == "least_used":
                chosen = min(active, key=lambda k: k.usage_count)
            else:
                # Round-robin selection
                self._index = (self._index + 1) % len(active)
                chosen = active[self._index]

            chosen.usage_count += 1
            chosen.last_used_at = time.time()
            return chosen

    def mark_exhausted(self, key_str: str, reason: str = "") -> None:
        """Mark an API key as exhausted (e.g. 429 quota or rate limit exceeded)."""
        with self._lock:
            for k in self._keys:
                if k.key == key_str:
                    k.is_exhausted = True
                    k.error_count += 1
                    logger.warning(
                        f"Tavily key {k.masked_key} marked exhausted: {reason} "
                        f"({len(self.active_keys)} active keys remaining)"
                    )
                    break

    def record_error(self, key_str: str) -> None:
        with self._lock:
            for k in self._keys:
                if k.key == key_str:
                    k.error_count += 1
                    break

    def get_stats(self) -> list[dict[str, object]]:
        """Return load balancing telemetry for all keys."""
        with self._lock:
            return [
                {
                    "key": k.masked_key,
                    "usage_count": k.usage_count,
                    "is_exhausted": k.is_exhausted,
                    "error_count": k.error_count,
                    "last_used_at": k.last_used_at,
                }
                for k in self._keys
            ]
