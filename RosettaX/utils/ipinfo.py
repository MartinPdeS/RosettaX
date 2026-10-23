"""Small cached client for IPinfo enrichment."""

import json
import logging
import os
import threading
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
_CACHE: dict[str, dict[str, str]] = {}
_LOCK = threading.Lock()


def lookup(ip_address: str) -> dict[str, str]:
    """Return persisted visit fields from IPinfo, or N/A fallbacks."""
    ip_address = str(ip_address or "").strip()
    if not ip_address:
        return {"location": "N/A", "organization": "N/A"}
    with _LOCK:
        if ip_address in _CACHE:
            return _CACHE[ip_address]
    query = {}
    token = os.getenv("ROSETTAX_IPINFO_TOKEN", "").strip()
    if token:
        query["token"] = token
    url = f"https://ipinfo.io/{ip_address}/json"
    if query:
        url += "?" + urlencode(query)
    result = {"location": "N/A", "organization": "N/A"}
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, dict):
            parts = [str(payload.get(key, "")).strip() for key in ("city", "region", "country")]
            result["location"] = ", ".join(part for part in parts if part) or "N/A"
            result["organization"] = str(payload.get("org") or payload.get("as_name") or "N/A").strip()
    except Exception:
        logger.warning("IPinfo lookup failed for %r", ip_address)
    with _LOCK:
        _CACHE[ip_address] = result
    return result
