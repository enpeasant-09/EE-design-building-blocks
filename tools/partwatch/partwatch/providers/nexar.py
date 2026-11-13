"""Octopart data via the Nexar GraphQL API (multi-distributor, the Findchips-style view).

Credentials: NEXAR_CLIENT_ID / NEXAR_CLIENT_SECRET from https://portal.nexar.com
(create an app with the Supply scope). Every part *returned* counts against the
app's part limit, so this asks for one part per MPN and batches MPNs.
"""
from __future__ import annotations

from ..http import request
from ..models import Offer, SourceResult, normalize_lifecycle
from ..normalize import clean
from .base import OAuthClientCredentials, Provider

TOKEN_URL = "https://identity.nexar.com/connect/token"
API_URL = "https://api.nexar.com/graphql"

QUERY = """
query PartwatchMatch($queries: [SupPartMatchQuery!]!, $country: String!, $currency: String!) {
  supMultiMatch(queries: $queries, country: $country, currency: $currency) {
    reference
    hits
    parts {
      mpn
      manufacturer { name }
      totalAvail
      octopartUrl
      specs { attribute { shortname } displayValue }
      sellers(authorizedOnly: false) {
        company { name }
        isAuthorized
        offers { inventoryLevel factoryLeadDays clickUrl }
      }
    }
  }
}
"""


class NexarProvider(Provider):
    name = "octopart"
    batch_size = 20

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.auth = OAuthClientCredentials(
            TOKEN_URL, self.env("NEXAR_CLIENT_ID"), self.env("NEXAR_CLIENT_SECRET"),
            scope="supply.domain")
        self.country = cfg.get("country", "IN")
        self.currency = cfg.get("currency", "USD")
        self.authorized_only = cfg.get("authorized_only", True)

    def lookup(self, mpn, manufacturer):
        return self.lookup_many([(mpn, manufacturer)])[clean(mpn)]

    def lookup_many(self, items):
        out: dict[str, SourceResult] = {}
        for i in range(0, len(items), self.batch_size):
            chunk = items[i:i + self.batch_size]
            queries = []
            for n, (mpn, mfr) in enumerate(chunk):
                # Manufacturer is checked locally (names differ between sources);
                # `candidates` > 1 costs more parts but survives same-MPN collisions.
                queries.append({"mpn": mpn, "limit": self.cfg.get("candidates", 1),
                                "reference": str(n)})
            try:
                data = request("POST", API_URL, limiter=self.limiter,
                               headers={"Authorization": f"Bearer {self.auth.token()}"},
                               json_body={"query": QUERY, "variables": {
                                   "queries": queries, "country": self.country,
                                   "currency": self.currency}})
            except Exception as e:  # noqa: BLE001
                for mpn, _ in chunk:
                    out[clean(mpn)] = SourceResult(self.name, False, mpn=mpn, error=str(e))
                continue
            if data.get("errors") and not data.get("data"):
                msg = "; ".join(err.get("message", "") for err in data["errors"])
                for mpn, _ in chunk:
                    out[clean(mpn)] = SourceResult(self.name, False, mpn=mpn, error=msg)
                continue
            matches = (data.get("data") or {}).get("supMultiMatch") or []
            by_ref = {m.get("reference"): m for m in matches}
            for n, (mpn, mfr) in enumerate(chunk):
                m = by_ref.get(str(n)) or (matches[n] if n < len(matches) else {})
                out[clean(mpn)] = self._parse(mpn, mfr, m.get("parts") or [])
        return out

    def _parse(self, mpn, mfr, parts) -> SourceResult:
        part = self.pick(mpn, mfr, parts, lambda p: p.get("mpn", ""),
                         lambda p: (p.get("manufacturer") or {}).get("name", ""))
        if not part:
            return SourceResult(self.name, False, mpn=mpn)
        life_raw = ""
        for s in part.get("specs") or []:
            if (s.get("attribute") or {}).get("shortname") in ("lifecyclestatus", "lifecycle_status"):
                life_raw = s.get("displayValue", "")
        offers: dict[str, Offer] = {}
        for seller in part.get("sellers") or []:
            auth = bool(seller.get("isAuthorized"))
            if self.authorized_only and not auth:
                continue
            name = (seller.get("company") or {}).get("name", "?")
            stock, lead, url = 0, None, ""
            for o in seller.get("offers") or []:
                lvl = o.get("inventoryLevel") or 0
                stock = max(stock, lvl if lvl > 0 else 0)
                if o.get("factoryLeadDays"):
                    d = o["factoryLeadDays"] / 7.0
                    lead = d if lead is None else min(lead, d)
                url = url or o.get("clickUrl") or ""
            prev = offers.get(name)
            if not prev or stock > prev.stock:
                offers[name] = Offer(name, stock, lead, auth, url)
        return SourceResult(
            source=self.name, found=True, mpn=part.get("mpn", mpn),
            manufacturer=(part.get("manufacturer") or {}).get("name", ""),
            lifecycle_raw=life_raw, lifecycle=normalize_lifecycle(life_raw),
            offers=list(offers.values()))
