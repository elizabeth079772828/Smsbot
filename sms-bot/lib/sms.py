import time
from typing import List, Dict, Any

from .config import SEND_PATH
from .store import rpush


def normalize_number(raw: str) -> str | None:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return None
    while digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) != 10:
        return None
    if digits[0] not in "6789":
        return None
    return f"+91{digits}"


def compose_message(template: str, code: str | None, link: str | None) -> str:
    body = template or ""
    if code:
        if "{code}" in body:
            body = body.replace("{code}", code)
        else:
            body = f"{body}\n{code}" if body else code
    if link:
        if "{link}" in body:
            body = body.replace("{link}", link)
        else:
            body = f"{body}\n{link}" if body else link
    return body.strip()


async def enqueue_sms_batch(devices: List[Dict[str, Any]],
                            numbers: List[str],
                            codes: List[str],
                            template: str,
                            link: str | None,
                            base_delay_ms: int = 500) -> Dict[str, Any]:
    if not devices:
        return {"queued": 0, "errors": ["no online devices"]}
    if not numbers:
        return {"queued": 0, "errors": ["no numbers"]}

    now_ms = int(time.time() * 1000)
    queued, errors = 0, []
    n = len(devices)
    codes_len = len(codes)

    for i, num in enumerate(numbers):
        dev = devices[i % n]
        code = codes[i % codes_len] if codes_len else None
        body = compose_message(template, code, link)
        payload = {
            "to": num,
            "body": body,
            "code": code or "",
            "scheduled_at": now_ms + i * base_delay_ms,
            "status": "queued",
            "created_at": now_ms,
            "from_panel": "tg-bot",
        }
        name = await rpush(dev["url"], f"{SEND_PATH}/{dev['id']}", payload)
        if name:
            queued += 1
        else:
            errors.append(f"{dev['url']}::{dev['id']}")
    return {"queued": queued, "errors": errors[:5]}