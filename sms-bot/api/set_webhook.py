import os
import sys
import asyncio
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import telegram_api as tg  # noqa: E402
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
    def _serve(self):
        qs = parse_qs(urlparse(self.path).query)
        url = (qs.get("url") or [""])[0].strip()
        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"missing ?url=")
            return
        result = _run(tg.set_webhook(url, WEBHOOK_SECRET))
        me = _run(tg.get_me())
        body = json.dumps({"setWebhook": result, "me": me}, indent=2).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._serve()

    def do_POST(self):
        self._serve()