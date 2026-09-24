from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

WebSearchProvider = Literal["tavily", "ddgs", "all"]


def generate_web_cite_key(url: str, provider: str) -> str:
    """Generate deterministic cite_key for a web search result."""
    parsed = urlparse(url)
    domain = re.sub(r"[^a-zA-Z0-9]", "", parsed.netloc.replace("www.", ""))[:12]
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"web_{provider}_{domain}_{url_hash}"


@dataclass
class WebSearchResult:
    title: str
    url: str
    content: str
    provider: str
    query: str
    score: float = 0.0
    published_date: str | None = None
    source_domain: str = ""
    raw_content: str | None = None
    markdown_content: str | None = None
    cite_key: str = ""

    def __post_init__(self) -> None:
        if not self.source_domain and self.url:
            parsed = urlparse(self.url)
            self.source_domain = parsed.netloc.replace("www.", "")
        if not self.cite_key:
            self.cite_key = generate_web_cite_key(self.url, self.provider)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WebSearchResponse:
    query: str
    provider: WebSearchProvider
    total_results: int = 0
    results: list[WebSearchResult] = field(default_factory=list)
    response_time: float = 0.0
    indexed_documents: int = 0
    indexed_chunks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "provider": self.provider,
            "total_results": self.total_results,
            "results": [r.to_dict() for r in self.results],
            "response_time": self.response_time,
            "indexed_documents": self.indexed_documents,
            "indexed_chunks": self.indexed_chunks,
        }
