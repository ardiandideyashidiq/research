from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DDGSTopic = Literal["general", "news"]


@dataclass
class DDGSSearchResult:
    title: str
    url: str
    body: str
    date: str | None = None
    source: str | None = None
    raw_content: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DDGSSearchResponse:
    query: str
    topic: DDGSTopic
    results: list[DDGSSearchResult] = field(default_factory=list)
    response_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "topic": self.topic,
            "results": [r.to_dict() for r in self.results],
            "response_time": self.response_time,
        }
