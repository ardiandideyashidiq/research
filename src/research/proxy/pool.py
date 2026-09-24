from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import httpx
from loguru import logger

from research.proxy.models import Proxy

ProxySource = list[Proxy] | list[str] | str


class ProxyPool:
    DEFAULT_VLESS_URL = (
        "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt"
    )

    def __init__(
        self,
        proxies: ProxySource | None = None,
        *,
        v2ray_bin: str | None = None,
    ) -> None:
        self.source = proxies
        self.proxies: list[Proxy] = []
        self._index: int = 0
        self._v2ray_bin = v2ray_bin or shutil.which("v2ray") or "/usr/bin/v2ray"
        self._v2ray_proc: asyncio.subprocess.Process | None = None
        self._v2ray_cfg_path: str | None = None
        self._active_socks_port: int | None = None

        if isinstance(proxies, list):
            for item in proxies:
                if isinstance(item, Proxy):
                    self.proxies.append(item)
                elif isinstance(item, str):
                    try:
                        self.proxies.append(Proxy.from_url(item))
                    except (ValueError, KeyError, IndexError) as exc:
                        logger.debug("Failed to parse proxy URL {}: {}", item, exc)

    def add(self, proxy: Proxy) -> None:
        if proxy not in self.proxies:
            self.proxies.append(proxy)

    def remove(self, proxy: Proxy) -> None:
        if proxy in self.proxies:
            self.proxies.remove(proxy)

    def next(self) -> Proxy | None:
        """Round-robin over loaded proxies."""
        if not self.proxies:
            return None
        proxy = self.proxies[self._index % len(self.proxies)]
        self._index = (self._index + 1) % len(self.proxies)
        return proxy

    async def load(self, source: ProxySource | None = None) -> None:
        """Load proxies from configured source, URL, or file."""
        src = source if source is not None else self.source
        if src is None:
            src = self.DEFAULT_VLESS_URL

        if isinstance(src, list):
            self.proxies = [
                p if isinstance(p, Proxy) else Proxy.from_url(p) for p in src
            ]
            logger.info("Loaded {} proxies from list", len(self.proxies))
            return

        lines: list[str] = []
        if isinstance(src, str):
            if src.startswith(("http://", "https://")):
                logger.info("Fetching proxy list from {}", src)
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(src)
                    resp.raise_for_status()
                    lines = resp.text.splitlines()
            else:
                path = Path(src)
                if path.exists():
                    text = await asyncio.to_thread(path.read_text, encoding="utf-8")
                    lines = text.splitlines()
                else:
                    logger.warning("Proxy source file not found: {}", src)

        loaded: list[Proxy] = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                loaded.append(Proxy.from_url(line))
            except (ValueError, KeyError, IndexError) as exc:
                logger.debug("Failed parsing proxy line: {} ({})", line[:40], exc)

        self.proxies = loaded
        logger.info("Successfully loaded {} proxies from source", len(self.proxies))

    def _build_v2ray_config(self, proxy: Proxy, local_port: int) -> dict[str, Any]:
        """Convert a VLESS proxy into a V2Ray JSON config with local SOCKS5 inbound."""
        raw_url = proxy.raw or proxy.url
        u = urllib.parse.urlsplit(raw_url)
        query = dict(urllib.parse.parse_qsl(u.query))
        uuid_str = urllib.parse.unquote(u.username or "")
        host = u.hostname or proxy.host
        port = int(u.port or proxy.port)
        net = query.get("type", "tcp")
        sec = query.get("security", "none")

        stream_settings: dict[str, Any] = {
            "network": net,
            "security": sec,
        }
        if net == "ws":
            ws_settings: dict[str, Any] = {"path": query.get("path", "/")}
            if query.get("host"):
                ws_settings["headers"] = {"Host": query["host"]}
            stream_settings["wsSettings"] = ws_settings
        elif net == "tcp" and query.get("headerType") == "http":
            stream_settings["tcpSettings"] = {
                "header": {
                    "type": "http",
                    "request": {
                        "headers": {
                            "Host": [query.get("host", host)]
                        } if query.get("host") else {}
                    },
                }
            }
        if sec == "tls":
            stream_settings["tlsSettings"] = {
                "serverName": query.get("sni", query.get("host", host)),
                "allowInsecure": True,
            }

        return {
            "log": {"loglevel": "none"},
            "inbounds": [
                {
                    "port": local_port,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "settings": {"auth": "noauth", "udp": False},
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": host,
                                "port": port,
                                "users": [
                                    {
                                        "id": uuid_str,
                                        "encryption": query.get("encryption", "none"),
                                        "level": 0,
                                    }
                                ],
                            }
                        ]
                    },
                    "streamSettings": stream_settings,
                }
            ],
        }

    async def start_v2ray_bridge(
        self,
        proxy: Proxy,
        *,
        local_port: int = 10850,
    ) -> str:
        """Start a local V2Ray SOCKS5 inbound bridge forwarding to a VLESS proxy."""
        if not os.path.exists(self._v2ray_bin):
            raise RuntimeError(f"V2Ray binary not found at {self._v2ray_bin}")

        await self._stop_v2ray()

        config = self._build_v2ray_config(proxy, local_port)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(config, tmp)
            self._v2ray_cfg_path = tmp.name

        self._v2ray_proc = await asyncio.create_subprocess_exec(
            self._v2ray_bin,
            "run",
            "-c",
            self._v2ray_cfg_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.sleep(0.3)

        if self._v2ray_proc.returncode is not None:
            self._cleanup_v2ray_files()
            raise RuntimeError("Failed to start V2Ray process (exited immediately)")

        self._active_socks_port = local_port
        socks_url = f"socks5://127.0.0.1:{local_port}"
        logger.info("V2Ray SOCKS5 bridge active at {}", socks_url)
        return socks_url

    async def _stop_v2ray(self) -> None:
        if self._v2ray_proc is not None:
            try:
                self._v2ray_proc.terminate()
                await asyncio.wait_for(self._v2ray_proc.wait(), timeout=2.0)
            except (TimeoutError, OSError):
                try:
                    self._v2ray_proc.kill()
                except OSError:
                    pass
            finally:
                self._v2ray_proc = None
        self._cleanup_v2ray_files()
        self._active_socks_port = None

    def _cleanup_v2ray_files(self) -> None:
        if self._v2ray_cfg_path and os.path.exists(self._v2ray_cfg_path):
            try:
                os.unlink(self._v2ray_cfg_path)
            except OSError:
                pass
            self._v2ray_cfg_path = None

    async def resolve_proxy_url(self, proxy: Proxy | None = None) -> str | None:
        """Resolve a usable proxy URL (HTTP, SOCKS5, or local V2Ray bridge for VLESS)."""
        target = proxy or self.next()
        if target is None:
            return None

        if target.protocol in ("http", "https", "socks4", "socks5", "socks5h"):
            return target.url

        if target.protocol == "vless":
            try:
                return await self.start_v2ray_bridge(target)
            except (TimeoutError, RuntimeError, OSError) as exc:
                logger.warning("Could not launch V2Ray bridge for {}: {}", target.host, exc)
                return None

        return target.url

    async def validate(
        self,
        target_url: str = "https://scholar.google.com",
        *,
        timeout: float = 5.0,
        sample_size: int = 10,
    ) -> list[Proxy]:
        """Validate a sample of proxies and retain only working ones."""
        valid_proxies: list[Proxy] = []
        candidates = self.proxies[:sample_size]

        async def _check(p: Proxy) -> bool:
            try:
                resolved = await self.resolve_proxy_url(p)
                if not resolved:
                    return False
                async with httpx.AsyncClient(proxy=resolved, timeout=timeout) as client:
                    res = await client.get(target_url)
                    return res.status_code == 200
            except (TimeoutError, httpx.HTTPError, OSError):
                return False

        results = await asyncio.gather(*[_check(p) for p in candidates], return_exceptions=True)
        for p, ok in zip(candidates, results, strict=False):
            if ok is True:
                valid_proxies.append(p)

        logger.info("Validated {}/{} proxies successfully", len(valid_proxies), len(candidates))
        return valid_proxies

    async def close(self) -> None:
        """Clean up proxy pool resources and terminate running bridge."""
        await self._stop_v2ray()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()