"""Mouser Search API (part-number search, up to 10 MPNs per call).

Credentials: MOUSER_API_KEY (the *Search* API key, not the Order key) from
https://www.mouser.com/api-search/. Limits: 30 calls/min, 1000 calls/day.
"""
from __future__ import annotations

import re

from ..http import request
from ..models import Lifecycle, Offer, SourceResult, normalize_lifecycle
from ..normalize import clean
from .base import Provider

URL = "https://api.mouser.com/api/v1/search/partnumber"


class MouserProvider(Provider):
    name = "mouser"
    batch_size = 10

    def __init__(self, cfg: dict):
        cfg = {"per_minute": 28, "per_day": 950, **cfg}
        super().__init__(cfg)
        self.key = self.env("MOUSER_API_KEY", "MOUSER_PART_API_KEY")

    def lookup(self, mpn, manufacturer):
        return self.lookup_many([(mpn, manufacturer)])[clean(mpn)]

    def lookup_many(self, items):
        out: dict[str, SourceResult] = {}
        for i in range(0, len(items), self.batch_size):
            chunk = items[i:i + self.batch_size]
            try:
                data = request("POST", URL, params={"apiKey": self.key}, limiter=self.limiter,
                               json_body={"SearchByPartRequest": {
                                   "mouserPartNumber": "|".join(m for m, _ in chunk),
                                   "partSearchOptions": self.cfg.get("match", "Exact")}})
            except Exception as e:  # noqa: BLE001
                for mpn, _ in chunk:
                    out[clean(mpn)] = SourceResult(self.name, False, mpn=mpn, error=str(e))
                continue
            errs = data.get("Errors") or []
            parts = (data.get("SearchResults") or {}).get("Parts") or []
            for mpn, mfr in chunk:
                p = self.pick(mpn, mfr, parts, lambda x: x.get("ManufacturerPartNumber", ""),
                              lambda x: x.get("Manufacturer", ""))
                if p:
                    out[clean(mpn)] = self._parse(p)
                else:
                    msg = "; ".join(e.get("Message", "") for e in errs) if errs else ""
                    out[clean(mpn)] = SourceResult(self.name, False, mpn=mpn, error=msg)
        return out

    def _parse(self, p: dict) -> SourceResult:
        raw = p.get("LifecycleStatus") or ""
        # Mouser leaves LifecycleStatus empty for ordinary production parts and
        # fills it in for "New Product", "Not Recommended for New Designs", "End of Life"...
        life = normalize_lifecycle(raw) if raw else Lifecycle.ACTIVE
        if str(p.get("IsDiscontinued", "")).lower() == "true":
            life, raw = Lifecycle.OBSOLETE, (raw + " (IsDiscontinued)").strip()
        stock = _int(p.get("AvailabilityInStock")) or _int(p.get("Availability"))
        lead = None
        m = re.search(r"(\d+)\s*(day|week)", str(p.get("LeadTime") or ""), re.I)
        if m:
            lead = int(m.group(1)) / (7.0 if m.group(2).lower() == "day" else 1.0)
        return SourceResult(
            source=self.name, found=True, mpn=p.get("ManufacturerPartNumber", ""),
            manufacturer=p.get("Manufacturer", ""), lifecycle_raw=raw or "(none reported)",
            lifecycle=life, offers=[Offer("Mouser", stock, lead, True, p.get("ProductDetailUrl", ""))],
            suggested_replacement=p.get("SuggestedReplacement") or "")


def _int(v) -> int:
    m = re.search(r"[\d,]+", str(v or ""))
    return int(m.group(0).replace(",", "")) if m else 0
