import json
import os
import re
import subprocess
import time
import httpx
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Cache for discovered hosts
_hosts_cache: List[str] = []
_hosts_cache_time: float = 0
_HOSTS_CACHE_TTL = 60  # seconds


COMMON_OPENAI_COMPAT_PORTS = {
    11434: "ollama",
    1234: "lm-studio",
    5000: "text-generation-webui",
    5001: "koboldcpp",
    8000: "vllm",
    8080: "llama.cpp",
    30000: "sglang",
}


def _normalize_openai_base(value: str) -> str:
    """Return an OpenAI-compatible base URL.

    Bare host[:port] values get `/v1`; full URLs keep their path because some
    providers use a different OpenAI-compatible prefix, such as Gemini's
    `/v1beta/openai`.
    """
    raw = (value or "").strip().rstrip("/")
    if not raw:
        return ""
    if not re.match(r"^https?://", raw):
        raw = "http://" + raw
    for suffix in ("/chat/completions", "/completions", "/models", "/responses"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)].rstrip("/")
    parsed = urlparse(raw)
    if not parsed.path or parsed.path == "/":
        raw += "/v1"
    return raw


def _provider_guess(base: str, port: Optional[int] = None) -> str:
    host = (urlparse(base).hostname or "").lower()
    if "openrouter.ai" in host:
        return "openrouter"
    if "generativelanguage.googleapis.com" in host:
        return "gemini-openai"
    if "api.openai.com" in host:
        return "openai"
    if "anthropic.com" in host:
        return "anthropic"
    return COMMON_OPENAI_COMPAT_PORTS.get(port or 0, "openai-compatible")


def discover_tailscale_hosts() -> List[str]:
    """Discover online Tailscale peers, returning their IPv4 addresses."""
    global _hosts_cache, _hosts_cache_time

    now = time.time()
    if _hosts_cache and (now - _hosts_cache_time) < _HOSTS_CACHE_TTL:
        return list(_hosts_cache)

    hosts = []
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return hosts

        data = json.loads(result.stdout)

        # Add self
        self_ips = data.get("Self", {}).get("TailscaleIPs", [])
        for ip in self_ips:
            if "." in ip:  # IPv4 only
                hosts.append(ip)
                break

        # Add online peers (skip funnel-ingress-nodes and android devices)
        for peer in data.get("Peer", {}).values():
            if not peer.get("Online"):
                continue
            hostname = peer.get("HostName", "")
            if hostname == "funnel-ingress-node":
                continue
            os_name = peer.get("OS", "")
            if os_name == "android":
                continue
            peer_ips = peer.get("TailscaleIPs", [])
            for ip in peer_ips:
                if "." in ip:  # IPv4 only
                    hosts.append(ip)
                    break

        _hosts_cache = hosts
        _hosts_cache_time = now
        logger.info(f"Tailscale discovery found {len(hosts)} hosts: {hosts}")
    except FileNotFoundError:
        logger.debug("tailscale command not found")
    except Exception as e:
        logger.warning(f"Tailscale discovery failed: {e}")

    return hosts


class ModelDiscovery:
    def __init__(self, default_host: str, openai_api_key: Optional[str] = None):
        self.default_host = default_host
        self.openai_api_key = openai_api_key
        self.openai_compat_path = "/v1/chat/completions"

    def _configured_bases(self) -> List[str]:
        """LLM_ENDPOINTS accepts exact OpenAI-compatible base URLs.

        LLM_HOSTS remains backwards-compatible: values may be bare hosts,
        host:port pairs, or full URLs.
        """
        bases = []
        for env_name in ("LLM_ENDPOINTS", "LLM_HOSTS"):
            for item in os.getenv(env_name, "").split(","):
                item = item.strip()
                if not item:
                    continue
                if "/" in item or re.search(r":\d+$", item):
                    base = _normalize_openai_base(item)
                    if base and base not in bases:
                        bases.append(base)
        return bases

    def _get_hosts(self) -> List[str]:
        """Get all hosts to scan, using env override, Tailscale, or default."""
        # Manual override takes priority
        extra = os.getenv("LLM_HOSTS", "").strip()
        if extra:
            hosts = []
            for raw in extra.split(","):
                raw = raw.strip()
                if not raw:
                    continue
                parsed = urlparse(raw if re.match(r"^https?://", raw) else f"http://{raw}")
                if parsed.hostname and not parsed.port:
                    hosts.append(parsed.hostname)
            # Always include the default host too
            if self.default_host not in hosts:
                hosts.insert(0, self.default_host)
            return hosts

        # Try Tailscale discovery
        ts_hosts = discover_tailscale_hosts()
        if ts_hosts:
            # Ensure default_host is included
            if self.default_host not in ts_hosts:
                ts_hosts.insert(0, self.default_host)
            return ts_hosts

        # Fallback to single host
        return [self.default_host]

    def _check_base(self, base: str) -> Optional[Dict[str, Any]]:
        """Check a single OpenAI-compatible base URL for models."""
        base = _normalize_openai_base(base)
        parsed = urlparse(base)
        port = parsed.port
        try:
            r = httpx.get(f"{base}/models", timeout=3)
            if not r.is_success:
                return None
            data = r.json() or {}
            ids = [m.get("id") for m in (data.get("data") or []) if m.get("id")]
            if ids:
                return {
                    "host": parsed.hostname or "",
                    "port": port,
                    "provider": _provider_guess(base, port),
                    "base_url": base,
                    "url": f"{base}/chat/completions",
                    "models": ids,
                    "models_display": [i.lstrip("/") for i in ids]
                }
        except Exception:
            pass
        return None

    def _check_port(self, host: str, port: int) -> Optional[Dict[str, Any]]:
        """Check a single host:port for models."""
        return self._check_base(f"http://{host}:{port}/v1")

    def _targets(self, hosts: List[str]) -> List[str]:
        configured = self._configured_bases()
        targets = list(configured)
        ports = sorted(set(COMMON_OPENAI_COMPAT_PORTS) | set(range(8000, 8021)))
        for host in hosts:
            for port in ports:
                base = f"http://{host}:{port}/v1"
                if base not in targets:
                    targets.append(base)
        return targets

    def discover_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover available models from all reachable hosts."""
        hosts = self._get_hosts()
        items = []

        logger.info(f"Scanning {len(hosts)} hosts for models: {hosts}")

        targets = self._targets(hosts)

        seen_models = set()  # dedupe by (base, model_ids)

        with ThreadPoolExecutor(max_workers=50) as pool:
            futures = {pool.submit(self._check_base, base): base for base in targets}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    key = (result["base_url"], tuple(sorted(result["models"])))
                    if key not in seen_models:
                        seen_models.add(key)
                        items.append(result)

        # Sort by host then port for consistent ordering
        items.sort(key=lambda x: (x["host"], x.get("port") or 0, x["base_url"]))

        logger.info(f"Discovered {len(items)} model endpoints across {len(hosts)} hosts")
        return {"hosts": hosts, "items": items}

    def get_providers(self) -> Dict[str, Any]:
        """Get all available providers"""
        discovery = self.discover_models()
        items = discovery["items"]
        providers = [{"provider": "openai-compatible", "hosts": discovery["hosts"], "items": items}]

        if self.openai_api_key:
            openai_models = [
                "gpt-5.2-codex", "gpt-4o-mini", "gpt-image-1.5",
                "gpt-4o", "gpt-5.2", "gpt-5.2-pro",
            ]
            providers.append({
                "provider": "openai",
                "items": [{
                    "url": "https://api.openai.com/v1/chat/completions",
                    "models": openai_models
                }]
            })

        return {"providers": providers}
