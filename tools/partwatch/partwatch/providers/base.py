from __future__ import annotations

import os
import time

from ..http import QuotaExhausted, RateLimiter, request
from ..models import SourceResult
from ..normalize import base, clean, same_manufacturer, same_part


class ProviderNotConfigured(RuntimeError):
    pass


class Provider:
    name = "base"
    batch_size = 1

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.limiter = RateLimiter(cfg.get("per_minute", 60), cfg.get("per_day"))

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def env(*names: str) -> str:
        for n in names:
            v = os.environ.get(n, "").strip()
            if v:
                return v
        raise ProviderNotConfigured("missing environment variable " + " or ".join(names))

    @staticmethod
    def pick(mpn: str, manufacturer: str, candidates: list[dict], get_mpn, get_mfr):
        """Choose the candidate that is really our part (exact > base match, mfr agrees)."""
        exact = [c for c in candidates if clean(get_mpn(c)) == clean(mpn)]
        loose = [c for c in candidates if same_part(get_mpn(c), mpn)
                 or base(get_mpn(c)).startswith(base(mpn))]
        for pool in (exact, loose):
            ok = [c for c in pool if same_manufacturer(get_mfr(c), manufacturer)]
            if ok:
                return ok[0]
        return None

    # -- interface -------------------------------------------------------
    def lookup(self, mpn: str, manufacturer: str) -> SourceResult:
        raise NotImplementedError

    def lookup_many(self, items: list[tuple[str, str]]) -> dict[str, SourceResult]:
        out = {}
        fatal = ""
        for mpn, mfr in items:
            if fatal:
                out[clean(mpn)] = SourceResult(self.name, False, mpn=mpn, error=fatal)
                continue
            try:
                out[clean(mpn)] = self.lookup(mpn, mfr)
            except Exception as e:  # noqa: BLE001 - report, keep going
                out[clean(mpn)] = SourceResult(source=self.name, found=False, mpn=mpn, error=str(e))
                # Bad key, no network or quota gone: stop hammering this provider.
                if isinstance(e, QuotaExhausted) or getattr(e, "status", None) in (0, 401, 403):
                    fatal = f"{self.name} unavailable: {e}"
        return out


class OAuthClientCredentials:
    """Caches a client-credentials bearer token until shortly before it expires."""

    def __init__(self, token_url: str, client_id: str, client_secret: str, scope: str | None = None):
        self.token_url, self.client_id, self.client_secret, self.scope = (
            token_url, client_id, client_secret, scope)
        self._token, self._expires = "", 0.0

    def token(self) -> str:
        if self._token and time.time() < self._expires - 60:
            return self._token
        form = {"grant_type": "client_credentials", "client_id": self.client_id,
                "client_secret": self.client_secret}
        if self.scope:
            form["scope"] = self.scope
        data = request("POST", self.token_url, form=form)
        self._token = data["access_token"]
        self._expires = time.time() + float(data.get("expires_in", 600))
        return self._token
