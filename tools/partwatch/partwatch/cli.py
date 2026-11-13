"""partwatch command line.

  partwatch scan  [PATHS...]   list the parts found (no network)
  partwatch check [PATHS...]   look up lifecycle/stock, write STATUS.md/status.json/parts.csv
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from . import __version__, extract, report
from .cache import Cache
from .normalize import group
from .pipeline import build_providers, log, run
from .score import RANK, is_generic, rate_units

DEFAULT_CONFIG = "partwatch.toml"


def load_config(path: str | None) -> tuple[dict, Path]:
    p = Path(path or DEFAULT_CONFIG)
    if p.exists():
        with p.open("rb") as f:
            return tomllib.load(f), p.resolve().parent
    if path:
        sys.exit(f"config file not found: {path}")
    return {}, Path.cwd()


def _paths(args, cfg, base: Path) -> list[Path]:
    if args.paths:
        return [Path(p) for p in args.paths]
    inc = (cfg.get("paths") or {}).get("include") or ["."]
    return [base / p for p in inc]


def _extract(args, cfg, base):
    import fnmatch
    from .score import DEFAULT_RULES
    f = cfg.get("fields") or {}
    pats = {**DEFAULT_RULES, **(cfg.get("rules") or {})}["generic_ok"]
    refs = extract.extract(_paths(args, cfg, base), mpn_fields=f.get("mpn"),
                           mfr_fields=f.get("manufacturer"), alt_fields=f.get("alternates"),
                           include_dnp=f.get("include_dnp", False),
                           value_as_mpn=getattr(args, "value_as_mpn", False) or f.get("value_as_mpn", False),
                           generic=lambda lib_id: any(fnmatch.fnmatch(lib_id, p) for p in pats))
    if not refs:
        log("[partwatch] no symbols found; check the paths")
    return refs


def cmd_scan(args) -> int:
    cfg, base = load_config(args.config)
    refs = _extract(args, cfg, base)
    groups, missing = group(refs)
    rules = cfg.get("rules") or {}
    print(f"{len(refs)} placements in {len({r.unit for r in refs})} units, "
          f"{len(groups)} unique MPNs, {len(missing)} without MPN\n")
    for g in groups:
        alts = f"  alt: {', '.join(g.alternates)}" if g.alternates else ""
        print(f"{g.mpn:<26} {g.manufacturer[:20]:<20} x{len(g.refs):<3} "
              f"{', '.join(g.used_in)}{alts}")
    nongeneric = [m for m in missing if m.problem or not is_generic(m, rules)]
    if nongeneric:
        print(f"\nNo MPN ({len(nongeneric)} non-generic):")
        for m in sorted(nongeneric, key=lambda m: (m.unit, m.reference)):
            print(f"  {m.unit:<28} {m.reference:<8} {m.value[:18]:<18} {m.problem or m.lib_id}")
    return 0


def cmd_check(args) -> int:
    cfg, base = load_config(args.config)
    refs = _extract(args, cfg, base)
    groups, missing = group(refs)
    only = args.providers.split(",") if args.providers else None
    providers = build_providers(cfg, only)
    if not providers:
        log("[partwatch] no provider is configured (set API keys or enable [providers.file])")
        return 2
    ccfg = cfg.get("cache") or {}
    cache = None if args.no_cache else Cache(base / ccfg.get("path", ".partwatch/cache.sqlite"))
    ttl = float(args.ttl_hours if args.ttl_hours is not None else ccfg.get("ttl_hours", 72)) * 3600
    rules = cfg.get("rules") or {}

    statuses = run(groups, providers, cache, rules, ttl)
    units = rate_units(statuses, missing, rules)
    rcfg = cfg.get("report") or {}
    out = Path(args.out) if args.out else base / rcfg.get("dir", "reports")
    files = report.write(out, statuses, units, [p.name for p in providers],
                         title=rcfg.get("title", "Design block part status"))

    worst = max((u["rating"] for u in units.values()), key=RANK.get, default="green")
    counts = {k: sum(1 for p in statuses if p.rating == k) for k in RANK}
    print(f"{len(statuses)} parts: {counts['red']} red, {counts['amber']} amber, "
          f"{counts['green']} green, {counts['gray']} unknown -> {files['markdown']}")
    for p in sorted(statuses, key=lambda p: -RANK[p.rating]):
        if p.rating in ("red", "amber"):
            print(f"  {p.rating.upper():<5} {p.mpn:<26} {'; '.join(p.reasons)[:110]}")
    if args.fail_on and RANK[worst] >= RANK[args.fail_on]:
        return 1
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="partwatch", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"partwatch {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("scan", cmd_scan), ("check", cmd_check)):
        sp = sub.add_parser(name)
        sp.add_argument("paths", nargs="*", help=".kicad_sch files or folders (default: config paths)")
        sp.add_argument("-c", "--config", help=f"config file (default: ./{DEFAULT_CONFIG})")
        sp.add_argument("--value-as-mpn", action="store_true",
                        help="use the Value field as MPN when no MPN field exists (non-passives)")
        sp.set_defaults(fn=fn)
        if name == "check":
            sp.add_argument("-p", "--providers", help="comma list, e.g. octopart,digikey")
            sp.add_argument("-o", "--out", help="report folder")
            sp.add_argument("--ttl-hours", type=float, help="cache age to accept")
            sp.add_argument("--no-cache", action="store_true")
            sp.add_argument("--fail-on", choices=["amber", "red"],
                            help="exit 1 if any brick is at or above this level (for CI)")
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except BrokenPipeError:      # e.g. `partwatch scan | head`
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())
