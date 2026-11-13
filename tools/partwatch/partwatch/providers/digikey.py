"""DigiKey Product Information API v4.

Credentials: DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET from https://developer.digikey.com
(create a Production app subscribed to "ProductInformation V4"). Default quota is
about 1000 calls/day, so results are cached and calls are counted.
"""
from __future__ import annotations

import urllib.parse

from ..http import HttpError, request
from ..models import Lifecycle, Offer, SourceResult, normalize_lifecycle
from .base import OAuthClientCredentials, Provider

BASE = "https://api.digikey.com"


class DigiKeyProvider(Provider):
    name = "digikey"

    def __init__(self, cfg: dict):
        cfg = {"per_minute": 100, "per_day": 950, **cfg}
        super().__init__(cfg)
        self.client_id = self.env("DIGIKEY_CLIENT_ID")
        self.auth = OAuthClientCredentials(f"{BASE}/v1/oauth2/token", self.client_id,
                                           self.env("DIGIKEY_CLIENT_SECRET"))
        self.locale = {
            "X-DIGIKEY-Locale-Site": cfg.get("site", "IN"),
            "X-DIGIKEY-Locale-Language": cfg.get("language", "en"),
            "X-DIGIKEY-Locale-Currency": cfg.get("currency", "USD"),
        }

    def _headers(self):
        return {"X-DIGIKEY-Client-Id": self.client_id,
                "Authorization": f"Bearer {self.auth.token()}", **self.locale}

    def lookup(self, mpn, manufacturer):
        product = None
        try:
            data = request("GET", f"{BASE}/products/v4/search/"
                                  f"{urllib.parse.quote(mpn, safe='')}/productdetails",
                           headers=self._headers(), limiter=self.limiter)
            product = data.get("Product")
            if product and not self.pick(mpn, manufacturer, [product], _mpn, _mfr):
                product = None
        except HttpError as e:
            if e.status not in (400, 404):
                raise
        if product is None:
            data = request("POST", f"{BASE}/products/v4/search/keyword",
                           headers=self._headers(), limiter=self.limiter,
                           json_body={"Keywords": mpn, "Limit": 10, "Offset": 0})
            cands = (data.get("ExactMatches") or []) + (data.get("Products") or [])
            product = self.pick(mpn, manufacturer, cands, _mpn, _mfr)
        if not product:
            return SourceResult(self.name, False, mpn=mpn)
        return self._parse(product)

    def _parse(self, p: dict) -> SourceResult:
        status = p.get("ProductStatus")
        raw = status.get("Status", "") if isinstance(status, dict) else str(status or "")
        life = normalize_lifecycle(raw)
        if p.get("EndOfLife") and life.severity < Lifecycle.LTB.severity:
            life, raw = Lifecycle.LTB, raw + " (EndOfLife flag)"
        if p.get("Discontinued") and life.severity < Lifecycle.NRND.severity:
            life, raw = Lifecycle.NRND, raw + " (discontinued at DigiKey)"
        lead = p.get("ManufacturerLeadWeeks")
        try:
            lead = float(str(lead).split()[0]) if lead not in (None, "") else None
        except ValueError:
            lead = None
        return SourceResult(
            source=self.name, found=True, mpn=_mpn(p), manufacturer=_mfr(p),
            lifecycle_raw=raw, lifecycle=life,
            offers=[Offer("DigiKey", int(p.get("QuantityAvailable") or 0), lead, True,
                          p.get("ProductUrl", ""))])


def _mpn(p):
    return p.get("ManufacturerProductNumber") or p.get("ManufacturerPartNumber") or ""


def _mfr(p):
    m = p.get("Manufacturer")
    return m.get("Name", "") if isinstance(m, dict) else str(m or "")
