from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

DEFAULT_TAVILY_KEYS: list[str] = [
    "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",
    "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",
    "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",
]


@dataclass
class APIKeyStatus:
    key: str
    usage_count: int = 0
    is_exhausted: bool = False
    last_used_at: float = field(default_factory=time.time)
    error_count: int = 0

    @property
    def masked_key(self) -> str:
        if len(self.key) <= 12:
            return "***"
        return f"{self.key[:12]}...{self.key[-4:]}"


@dataclass
class TavilySearchResult:
    url: str
    title: str
    content: str
    score: float = 0.0
    raw_content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TavilySearchResponse:
    query: str
    results: list[TavilySearchResult] = field(default_factory=list)
    response_time: float = 0.0
    api_key_used: str = ""
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "response_time": self.response_time,
            "api_key_used": self.api_key_used,
            "request_id": self.request_id,
        }
