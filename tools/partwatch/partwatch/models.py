from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum


class Lifecycle(str, Enum):
    ACTIVE = "active"
    PRELIMINARY = "preliminary"
    NRND = "nrnd"          # not recommended for new designs
    LTB = "ltb"            # last time buy / EOL announced
    OBSOLETE = "obsolete"
    UNKNOWN = "unknown"

    @property
    def severity(self) -> int:
        return {"active": 0, "preliminary": 1, "unknown": 1, "nrnd": 2,
                "ltb": 3, "obsolete": 4}[self.value]


def normalize_lifecycle(raw: str | None) -> Lifecycle:
    """Map any distributor's lifecycle wording onto one vocabulary."""
    if not raw:
        return Lifecycle.UNKNOWN
    s = raw.strip().lower().replace("-", " ").replace("_", " ")
    if "discontinued at" in s:
        # e.g. DigiKey "Discontinued at Digi-Key": the distributor dropped it,
        # the manufacturer may still make it. Risky, but not proof of EOL.
        return Lifecycle.NRND
    if any(k in s for k in ("obsolete", "discontinued", "end of life reached", "eol reached",
                            "no longer manufactured", "inactive")):
        return Lifecycle.OBSOLETE
    if any(k in s for k in ("last time buy", "ltb", "end of life", "eol")):
        return Lifecycle.LTB
    if any(k in s for k in ("not recommended", "nrnd", "not for new design", "mature")):
        return Lifecycle.NRND
    if any(k in s for k in ("preliminary", "pre release", "prerelease", "new product",
                            "sampling", "coming soon", "introduction")):
        # Mouser labels freshly released parts "New Product": that is active, not risky.
        return Lifecycle.ACTIVE if "new product" in s else Lifecycle.PRELIMINARY
    if any(k in s for k in ("active", "production", "in production", "volume")):
        return Lifecycle.ACTIVE
    return Lifecycle.UNKNOWN


@dataclass
class PartRef:
    """One placed symbol found in a schematic."""
    unit: str            # brick name (Library/Block) or schematic path
    file: str
    reference: str
    lib_id: str
    value: str
    footprint: str
    mpn: str
    manufacturer: str
    alternates: list[str] = field(default_factory=list)
    dnp: bool = False
    in_bom: bool = True
    raw_mpn: str = ""        # field text before clean-up, when it differed
    problem: str = ""        # e.g. "incomplete MPN 'SiT9102AI-xx-...'"


@dataclass
class Offer:
    distributor: str
    stock: int
    lead_weeks: float | None = None
    authorized: bool = True
    url: str = ""


@dataclass
class SourceResult:
    """What one provider says about one MPN."""
    source: str
    found: bool
    mpn: str = ""
    manufacturer: str = ""
    lifecycle_raw: str = ""
    lifecycle: Lifecycle = Lifecycle.UNKNOWN
    offers: list[Offer] = field(default_factory=list)
    suggested_replacement: str = ""
    error: str = ""

    def to_json(self) -> dict:
        d = asdict(self)
        d["lifecycle"] = self.lifecycle.value
        return d

    @classmethod
    def from_json(cls, d: dict) -> "SourceResult":
        d = dict(d)
        d["lifecycle"] = Lifecycle(d.get("lifecycle", "unknown"))
        d["offers"] = [Offer(**o) for o in d.get("offers", [])]
        return cls(**d)


@dataclass
class PartStatus:
    """Merged view of an MPN across all providers, plus its score."""
    key: str
    mpn: str
    manufacturer: str
    lifecycle: Lifecycle
    total_stock: int
    distributors_in_stock: list[str]
    min_lead_weeks: float | None
    sources: list[SourceResult]
    used_in: dict[str, list[str]]           # unit -> references
    rating: str = "green"                   # green / amber / red / gray
    reasons: list[str] = field(default_factory=list)
    suggested_replacement: str = ""
    alternates: list[dict] = field(default_factory=list)
