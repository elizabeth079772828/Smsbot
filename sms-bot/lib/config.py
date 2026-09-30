import os
from pathlib import Path

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "").strip()
STATE_URL = os.environ.get("STATE_URL", "").rstrip("/")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "changeme")

DEVICE_PATHS = [
    p.strip() for p in os.environ.get(
        "DEVICE_PATHS",
        "devices,Device,devices_list,online,onlineDevices,users,clients,sms_devices,panels,List,Sms,all_devices"
    ).split(",") if p.strip()
]

SEND_PATH = os.environ.get("SEND_PATH", "sms_queue").strip()

STATE_ROOT = "smsbot_state"


def load_firebase_urls():
    p = Path(__file__).resolve().parent.parent / "data" / "firebase_urls.txt"
    if not p.exists():
        return []
    seen, out = set(), []
    for line in p.read_text(encoding="utf-8").splitlines():
        u = line.strip().rstrip("/")
        if not u or not u.startswith("http"):
            continue
        if not (u.endswith(".firebaseio.com") or u.endswith(".firebasedatabase.app")):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


FIREBASE_URLS = load_firebase_urls()