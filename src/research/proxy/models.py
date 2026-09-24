from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Self


@dataclass
class Proxy:
    host: str
    port: int
    protocol: str = "http"
    username: str | None = None
    password: str | None = None
    country: str | None = None
    anonymity: str | None = None
    raw: str | None = None

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

    @classmethod
    def from_url(cls, raw: str) -> Self:
        clean = raw.strip()
        parsed_raw = clean
        if "://" not in clean:
            clean = f"http://{clean}"
        u = urllib.parse.urlsplit(clean)
        protocol = u.scheme.lower() if u.scheme else "http"
        host = u.hostname or ""
        default_port = 443 if protocol in ("https", "vless") else 80
        port = u.port or default_port
        user = urllib.parse.unquote(u.username) if u.username else None
        pwd = urllib.parse.unquote(u.password) if u.password else None
        country = None
        if u.fragment:
            country = urllib.parse.unquote(u.fragment).strip()
        return cls(
            host=host,
            port=port,
            protocol=protocol,
            username=user,
            password=pwd,
            country=country,
            raw=parsed_raw,
        )