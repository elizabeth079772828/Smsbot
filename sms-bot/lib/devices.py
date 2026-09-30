import asyncio
import time
from typing import List, Dict, Any

from .config import FIREBASE_URLS, DEVICE_PATHS
from .store import rget

ONLINE_KEYS_TRUE = {"online", "is_online", "active", "isActive", "is_active", "connected"}
STATUS_ONLINE = {"online", "active", "connected", "on", "true"}
RECENT_SECONDS = 120


def _is_online(node: Dict[str, Any]) -> bool:
    if not isinstance(node, dict):
        return False
    for k in ONLINE_KEYS_TRUE:
        v = node.get(k)
        if v is True:
            return True
        if isinstance(v, str) and v.lower() in STATUS_ONLINE:
            return True
    st = node.get("status") or node.get("state")
    if isinstance(st, str) and st.lower() in STATUS_ONLINE:
        return True
    for lk in ("last_seen", "lastSeen", "last_active", "lastActive", "updated_at", "timestamp", "ts"):
        v = node.get(lk)
        if isinstance(v, (int, float)):
            secs = v / 1000 if v > 10_000_000_000 else v
            if time.time() - secs < RECENT_SECONDS:
                return True
    return False


async def _scan_one(url: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    results = await asyncio.gather(*[rget(url, p) for p in DEVICE_PATHS], return_exceptions=True)
    for path, data in zip(DEVICE_PATHS, results):
        if not isinstance(data, dict):
            continue
        for dev_id, node in data.items():
            if _is_online(node):
                out.append({
                    "url": url,
                    "path": path,
                    "id": dev_id,
                    "info": node if isinstance(node, dict) else {},
                })
    seen, uniq = set(), []
    for d in out:
        k = (d["url"], d["id"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(d)
    return uniq


async def scan_all_devices() -> List[Dict[str, Any]]:
    if not FIREBASE_URLS:
        return []
    chunks = await asyncio.gather(*[_scan_one(u) for u in FIREBASE_URLS], return_exceptions=True)
    pool: List[Dict[str, Any]] = []
    for c in chunks:
        if isinstance(c, list):
            pool.extend(c)
    return pool