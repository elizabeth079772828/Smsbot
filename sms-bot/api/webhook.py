import json
import asyncio
import sys
import os
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import handlers  # noqa: E402
from lib.config import WEBHOOK_SECRET  # noqa: E402


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class handler(BaseHTTPRequestHandler):
    def _reject(self, code=200):
        self.send_response(code)
        self.send_header("content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self._reject()

    def do_POST(self):
        if WEBHOOK_SECRET:
            hdr = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if hdr != WEBHOOK_SECRET:
                self.send_response(403)
                self.end_headers()
                return
        try:
            length = int(self.headers.get("content-length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            update = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        # ack immediately so telegram doesn't retry
        self.send_response(200)
        self.send_header("content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

        try:
            if "callback_query" in update:
                _run(handlers.handle_callback(update))
            elif "message" in update:
                _run(handlers.handle_message(update))
        except Exception:
            pass