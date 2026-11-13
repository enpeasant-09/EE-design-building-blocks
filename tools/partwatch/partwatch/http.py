"""Tiny JSON-over-HTTPS client (stdlib only) with rate limiting and 429 back-off."""
from __future__ import annotations

import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "partwatch/1.0 (+kicad design-block lifecycle checker)"


class HttpError(RuntimeError):
    def __init__(self, status: int, body: str, url: str):
        super().__init__(f"HTTP {status} from {url}: {body[:300]}")
        self.status, self.body, self.url = status, body, url


class RateLimiter:
    """Token bucket: at most `per_minute` calls per minute, `per_day` per run-day."""

    def __init__(self, per_minute: float = 60, per_day: int | None = None):
        self.interval = 60.0 / per_minute if per_minute else 0.0
        self.per_day = per_day
        self.used = 0
        self._next = 0.0
        self._lock = threading.Lock()

    def acquire(self):
        with self._lock:
            if self.per_day is not None and self.used >= self.per_day:
                raise QuotaExhausted(f"daily budget of {self.per_day} calls used")
            now = time.monotonic()
            if now < self._next:
                time.sleep(self._next - now)
            self._next = max(now, self._next) + self.interval
            self.used += 1


class QuotaExhausted(RuntimeError):
    pass


def request(method: str, url: str, *, headers=None, params=None, json_body=None, form=None,
            limiter: RateLimiter | None = None, retries: int = 4, timeout: float = 30.0):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"

    for attempt in range(retries + 1):
        if limiter:
            limiter.acquire()
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                wait = e.headers.get("Retry-After")
                try:
                    delay = float(wait) if wait else 2 ** attempt
                except ValueError:
                    delay = 2 ** attempt
                time.sleep(min(delay, 120) + random.random())
                continue
            raise HttpError(e.code, body, url) from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt + random.random())
                continue
            raise HttpError(0, str(e), url) from None
