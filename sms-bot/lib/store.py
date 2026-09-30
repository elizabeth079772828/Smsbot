import httpx
from typing import Any, Optional

TIMEOUT = httpx.Timeout(8.0, connect=5.0)


async def rget(url: str, path: str = "") -> Optional[Any]:
    full = f"{url.rstrip('/')}/{path.strip('/')}.json" if path else f"{url.rstrip('/')}/.json"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(full)
            if r.status_code != 200:
                return None
            return r.json()
    except Exception:
        return None


async def rput(url: str, path: str, data: Any) -> bool:
    full = f"{url.rstrip('/')}/{path.strip('/')}.json"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.put(full, json=data)
            return r.status_code in (200, 204)
    except Exception:
        return False


async def rpush(url: str, path: str, data: Any) -> Optional[str]:
    full = f"{url.rstrip('/')}/{path.strip('/')}.json"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.post(full, json=data)
            if r.status_code != 200:
                return None
            return r.json().get("name")
    except Exception:
        return None


async def rpatch(url: str, path: str, data: Any) -> bool:
    full = f"{url.rstrip('/')}/{path.strip('/')}.json"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.patch(full, json=data)
            return r.status_code in (200, 204)
    except Exception:
        return False


async def rdelete(url: str, path: str) -> bool:
    full = f"{url.rstrip('/')}/{path.strip('/')}.json"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.delete(full)
            return r.status_code in (200, 204)
    except Exception:
        return False