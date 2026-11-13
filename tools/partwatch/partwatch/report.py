"""STATUS.md, status.json and parts.csv writers."""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from .models import PartStatus
from .score import RANK

BADGE = {"green": "🟢 OK", "amber": "🟡 Watch", "red": "🔴 Act", "gray": "⚪ Unknown"}


def _esc(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def _lead(p: PartStatus) -> str:
    return f"{p.min_lead_weeks:.0f} wk" if p.min_lead_weeks is not None else "–"


def _used(p: PartStatus, limit=4) -> str:
    items = [f"{u} ({', '.join(r)})" for u, r in p.used_in.items()]
    more = len(items) - limit
    return "<br>".join(items[:limit]) + (f"<br>+{more} more" if more > 0 else "")


def markdown(parts: list[PartStatus], units: dict, providers: list[str], title: str) -> str:
    order = sorted(parts, key=lambda p: (-RANK[p.rating], p.key))
    count = {k: sum(1 for p in parts if p.rating == k) for k in RANK}
    ucount = {k: sum(1 for u in units.values() if u["rating"] == k) for k in RANK}
    L = [f"# {title}", "",
         f"Checked {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} via {', '.join(providers) or 'no providers'}.",
         "",
         f"**Bricks:** {ucount['red']} 🔴 · {ucount['amber']} 🟡 · {ucount['green']} 🟢  ",
         f"**Parts:** {count['red']} 🔴 · {count['amber']} 🟡 · {count['green']} 🟢 · {count['gray']} ⚪",
         "", "## Bricks", "", "| Brick | Status | Parts | No MPN | Worst |", "|---|---|---:|---:|---|"]
    for name, u in sorted(units.items(), key=lambda kv: (-RANK[kv[1]["rating"]], kv[0])):
        nomp = sum(1 for m in u["missing"] if not m["generic"])
        L.append(f"| `{_esc(name)}` | {BADGE[u['rating']]} | {len(u['parts'])} | {nomp or ''} | "
                 f"{_esc(u['worst'])} |")

    attention = [p for p in order if p.rating in ("red", "amber", "gray")]
    if attention:
        L += ["", "## Needs attention", "",
              "| MPN | Manufacturer | Status | Lifecycle | Stock | Distributors | Lead | Why | Used in |",
              "|---|---|---|---|---:|---|---|---|---|"]
        for p in attention:
            why = list(p.reasons)
            if p.suggested_replacement:
                why.append(f"suggested replacement: {p.suggested_replacement}")
            for a in p.alternates:
                why.append(f"alt {a['mpn']}: {a['rating']} ({a['lifecycle']}, {a['stock']} pcs)")
            L.append(f"| `{_esc(p.mpn)}` | {_esc(p.manufacturer)} | {BADGE[p.rating]} | "
                     f"{p.lifecycle.value} | {p.total_stock:,} | {len(p.distributors_in_stock)} | "
                     f"{_lead(p)} | {_esc('; '.join(why))} | {_used(p)} |")

    L += ["", "## All parts", "",
          "| MPN | Manufacturer | Status | Lifecycle | Stock | In stock at | Sources |",
          "|---|---|---|---|---:|---|---|"]
    for p in order:
        srcs = ", ".join(f"{s.source}{'' if s.found else ' ✗'}" for s in p.sources)
        L.append(f"| `{_esc(p.mpn)}` | {_esc(p.manufacturer)} | {BADGE[p.rating]} | {p.lifecycle.value} | "
                 f"{p.total_stock:,} | {_esc(', '.join(p.distributors_in_stock[:5]))} | {srcs} |")

    missing = [(n, m) for n, u in units.items() for m in u["missing"] if not m["generic"]]
    if missing:
        L += ["", "## Placements without a usable MPN", "",
              "Add an `MPN` and `Manufacturer` field to these symbols.", "",
              "| Brick | Ref | Value | Symbol | Problem |", "|---|---|---|---|---|"]
        for n, m in missing:
            L.append(f"| `{_esc(n)}` | {_esc(m['reference'])} | {_esc(m['value'])} | "
                     f"`{_esc(m['lib_id'])}` | {_esc(m.get('problem') or 'no MPN field')} |")
    generic = sum(1 for u in units.values() for m in u["missing"] if m["generic"])
    if generic:
        L += ["", f"_{generic} generic passives without an MPN were not checked "
                  f"(see `rules.generic_ok`)._"]
    return "\n".join(L) + "\n"


def to_json(parts: list[PartStatus], units: dict, providers: list[str]) -> dict:
    return {
        "checked": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "providers": providers,
        "units": units,
        "parts": [{
            "mpn": p.mpn, "manufacturer": p.manufacturer, "rating": p.rating,
            "lifecycle": p.lifecycle.value, "total_stock": p.total_stock,
            "distributors_in_stock": p.distributors_in_stock, "min_lead_weeks": p.min_lead_weeks,
            "reasons": p.reasons, "suggested_replacement": p.suggested_replacement,
            "alternates": p.alternates, "used_in": p.used_in,
            "sources": [s.to_json() for s in p.sources],
        } for p in sorted(parts, key=lambda p: p.key)],
    }


def write(out_dir: Path, parts, units, providers, title="Part status") -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md, js, cs = out_dir / "STATUS.md", out_dir / "status.json", out_dir / "parts.csv"
    md.write_text(markdown(parts, units, providers, title), encoding="utf-8")
    js.write_text(json.dumps(to_json(parts, units, providers), indent=2), encoding="utf-8")
    with cs.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mpn", "manufacturer", "rating", "lifecycle", "total_stock",
                    "distributors_in_stock", "min_lead_weeks", "reasons", "used_in"])
        for p in sorted(parts, key=lambda p: (-RANK[p.rating], p.key)):
            w.writerow([p.mpn, p.manufacturer, p.rating, p.lifecycle.value, p.total_stock,
                        len(p.distributors_in_stock), p.min_lead_weeks or "",
                        "; ".join(p.reasons),
                        "; ".join(f"{u}:{','.join(r)}" for u, r in p.used_in.items())])
    return {"markdown": md, "json": js, "csv": cs}
