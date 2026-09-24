from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from research.db.models import PublicationRecord

SnowballDirection = Literal["both", "forward", "backward"]


@dataclass
class SnowballConfig:
    direction: SnowballDirection = "both"
    limit_forward: int = 25
    limit_backward: int = 25
    max_depth: int = 1
    email: str = "rdndds@gmail.com"
    timeout: float = 15.0
    concurrency: int = 4


@dataclass
class SnowballResult:
    seed_cite_key: str
    seed_title: str
    forward_count: int = 0
    backward_count: int = 0
    discovered_records: list[PublicationRecord] = field(default_factory=list)
    newly_indexed_count: int = 0
