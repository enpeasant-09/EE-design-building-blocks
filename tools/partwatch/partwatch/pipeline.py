"""Glue: extracted parts -> cached provider lookups -> rated statuses."""
from __future__ import annotations

import sys

from .cache import Cache
from .models import PartStatus, SourceResult
from .normalize import PartGroup, clean
from .providers import REGISTRY, ProviderNotConfigured
from .providers.base import Provider
from .score import rate


def log(msg: str):
    print(msg, file=sys.stderr)


def build_providers(cfg: dict, only: list[str] | None = None) -> list[Provider]:
    out = []
    for name, pcfg in (cfg.get("providers") or {}).items():
        if only is not None and name not in only:
            continue
        if only is None and not pcfg.get("enabled", True):
            continue
        cls = REGISTRY.get(pcfg.get("type", name))
        if cls is None:
            log(f"[partwatch] unknown provider '{name}', skipped")
            continue
        try:
            out.append(cls({"name": name, **pcfg}))
        except ProviderNotConfigured as e:
            log(f"[partwatch] {name}: {e}; skipped")
    return out


def lookup(items: list[tuple[str, str]], providers: list[Provider], cache: Cache | None,
           ttl_s: float) -> dict[str, list[SourceResult]]:
    results: dict[str, list[SourceResult]] = {clean(m): [] for m, _ in items}
    for p in providers:
        todo = []
        for mpn, mfr in items:
            hit = cache.get(p.name, clean(mpn), ttl_s) if cache else None
            if hit:
                results[clean(mpn)].append(hit)
            else:
                todo.append((mpn, mfr))
        if todo:
            log(f"[partwatch] {p.name}: {len(todo)} lookups ({len(items) - len(todo)} cached)")
            fresh = p.lookup_many(todo)
            for mpn, _ in todo:
                res = fresh.get(clean(mpn)) or SourceResult(p.name, False, mpn=mpn, error="no answer")
                results[clean(mpn)].append(res)
                if cache:
                    cache.put(clean(mpn), res)
    return results


def run(groups: list[PartGroup], providers: list[Provider], cache: Cache | None,
        rules: dict, ttl_s: float) -> list[PartStatus]:
    found = lookup([(g.mpn, g.manufacturer) for g in groups], providers, cache, ttl_s)
    statuses = [rate(g, found[g.key], rules) for g in groups]

    # Second pass: alternates, only for parts that need one.
    alt_groups: dict[str, PartGroup] = {}
    for g, st in zip(groups, statuses):
        if st.rating in ("amber", "red"):
            for a in g.alternates:
                alt_groups.setdefault(clean(a), PartGroup(key=clean(a), mpn=a, manufacturer=""))
    if alt_groups:
        alt_found = lookup([(g.mpn, "") for g in alt_groups.values()], providers, cache, ttl_s)
        alt_status = {k: rate(g, alt_found[k], rules) for k, g in alt_groups.items()}
        for g, st in zip(groups, statuses):
            if st.rating not in ("amber", "red"):
                continue
            for a in g.alternates:
                s = alt_status[clean(a)]
                st.alternates.append({"mpn": a, "rating": s.rating, "lifecycle": s.lifecycle.value,
                                      "stock": s.total_stock, "reasons": s.reasons})
            good = [x["mpn"] for x in st.alternates if x["rating"] == "green"]
            if good:
                st.reasons.append("drop-in alternate available: " + ", ".join(good))

    if cache:
        for st in statuses:
            prev = cache.previous(st.key)
            if prev and (prev[0] != st.lifecycle.value or prev[1] != st.rating):
                st.reasons.insert(0, f"CHANGED since last run: {prev[0]}/{prev[1]} -> "
                                     f"{st.lifecycle.value}/{st.rating}")
            cache.record(st.key, st.lifecycle.value, st.total_stock, st.rating)
    return statuses
