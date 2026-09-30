import httpx
from typing import Optional

from .config import BOT_TOKEN

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
TIMEOUT = httpx.Timeout(20.0, connect=5.0)


async def _post(method: str, data: dict) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.post(f"{BASE}/{method}", json=data)
            j = r.json()
            return j if j.get("ok") else None
    except Exception:
        return None


async def send_message(chat_id, text: str, reply_markup: dict | None = None,
                       parse_mode: str = "HTML") -> Optional[dict]:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode,
               "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await _post("sendMessage", payload)


async def edit_message(chat_id, message_id: int, text: str,
                       reply_markup: dict | None = None, parse_mode: str = "HTML") -> Optional[dict]:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text,
               "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await _post("editMessageText", payload)


async def answer_callback(callback_id: str, text: str = "", alert: bool = False) -> Optional[dict]:
    return await _post("answerCallbackQuery",
                       {"callback_query_id": callback_id, "text": text, "show_alert": alert})


async def get_file(file_id: str) -> Optional[dict]:
    return await _post("getFile", {"file_id": file_id})


async def download_file(file_path: str) -> Optional[bytes]:
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(url)
            if r.status_code == 200:
                return r.content
    except Exception:
        pass
    return None


async def set_webhook(url: str, secret: str) -> Optional[dict]:
    return await _post("setWebhook", {"url": url, "secret_token": secret,
                                      "allowed_updates": ["message", "callback_query"]})


async def get_me() -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as c:
            r = await c.get(f"{BASE}/getMe")
            j = r.json()
            return j if j.get("ok") else None
    except Exception:
        return None