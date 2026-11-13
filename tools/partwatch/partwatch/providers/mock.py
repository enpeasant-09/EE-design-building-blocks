"""Offline provider backed by a JSON file. Used for tests and for parts no API covers
(customer-supplied parts, a manual "known EOL" list from manufacturer PCNs, ...).

File format: {"MPN": {"manufacturer": "...", "lifecycle": "Active",
                      "offers": [{"distributor": "LCSC", "stock": 1200, "lead_weeks": 8}],
                      "suggested_replacement": ""}}
"""
from __future__ import annotations

import json
from pathlib import Path

from ..models import Offer, SourceResult, normalize_lifecycle
from ..normalize import base, clean
from .base import Provider


class FileProvider(Provider):
    name = "file"

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.name = cfg.get("name", "file")
        path = Path(cfg["path"])
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.db = {clean(k): v for k, v in raw.items()}
        self.db_base = {base(k): v for k, v in raw.items()}

    def lookup(self, mpn, manufacturer):
        rec = self.db.get(clean(mpn)) or self.db_base.get(base(mpn))
        if rec is None:
            return SourceResult(self.name, False, mpn=mpn)
        if rec.get("error"):
            return SourceResult(self.name, False, mpn=mpn, error=rec["error"])
        return SourceResult(
            source=self.name, found=True, mpn=mpn,
            manufacturer=rec.get("manufacturer", manufacturer),
            lifecycle_raw=rec.get("lifecycle", ""), lifecycle=normalize_lifecycle(rec.get("lifecycle")),
            offers=[Offer(**o) for o in rec.get("offers", [])],
            suggested_replacement=rec.get("suggested_replacement", ""))
