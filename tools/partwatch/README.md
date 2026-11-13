# partwatch

Lifecycle (EOL / NRND / LTB) and stock checker for a KiCad design-block library.
It reads the part numbers out of every brick, asks Octopart, DigiKey and Mouser
about them, and writes a per-brick status report. Run it on demand or weekly from
GitHub Actions.

Pure Python standard library (3.11+), nothing to install beyond the package itself.

```
partwatch scan                       # what parts do my bricks use? (no network)
partwatch check                      # look them up, write reports/STATUS.md
partwatch check --fail-on red        # exit 1 if any brick is red (CI)
partwatch check path/to/project/     # works on ordinary schematics too
```

## Where it lives

Put this folder in the bricks repo as `tools/partwatch/`. Copy `partwatch.toml` and
`.github/workflows/partwatch.yml` to the repo root:

```
kicad-bricks/
├── blocks/                     # *.kicad_blocks libraries
├── partwatch.toml
├── reports/STATUS.md           # written by partwatch, committed by CI
├── tools/partwatch/            # this folder
└── .github/workflows/partwatch.yml
```

Install with `pip install ./tools/partwatch`, or run `python -m partwatch` from inside `tools/partwatch`.

## Part fields in your bricks

For each symbol, partwatch reads these fields (names are configurable in `partwatch.toml`):

| Field | Example | Notes |
|---|---|---|
| `MPN` | `TPS54331DR` | Manufacturer part number. Required for non-passives. |
| `Manufacturer` | `Texas Instruments` | Short names like TI, ADI, ST and SiLabs are understood. |
| `MPN_ALT` | `TPS54332DDA, MP2451DT` | Optional. Checked when the main part goes amber or red. |

The parser handles some common mistakes:
- A messy field like `TDK TCE1210U-900-4P (90 Ohm)` is tidied to MPN `TCE1210U-900-4P` with manufacturer `TDK`.
- Placeholders like `SiT9102AI-xx-33E` are reported as incomplete and are not looked up.
- Generic passives (`*:R`, `*:C`, `*:L` and similar) are allowed to have no MPN.
- If your library keeps part numbers in Value, set `value_as_mpn = true`.

Also skipped:
- power symbols;
- DNP parts;
- symbols excluded from the BOM;
- the second unit of a multi-unit part.

## Data sources and keys

Keys are read from environment variables, or from GitHub secrets in CI. Any source without keys is skipped.

| Source | Variables | Get keys | What it adds |
|---|---|---|---|
| Octopart (Nexar) | `NEXAR_CLIENT_ID`, `NEXAR_CLIENT_SECRET` | portal.nexar.com: create an app with the Supply scope | Lifecycle, plus stock across all authorized distributors (the Findchips-style view) |
| DigiKey | `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET` | developer.digikey.com: Production app subscribed to Product Information V4 | Product status, stock, lead time |
| Mouser | `MOUSER_API_KEY` | mouser.com/api-search (the Search key) | Lifecycle, stock, lead time, suggested replacement |
| File | (none) | `partwatch_overrides.json` | Your own data: PCN notices, LCSC stock, customer-supplied parts |

Windows PowerShell, for a local run:

```powershell
$env:DIGIKEY_CLIENT_ID="..."; $env:DIGIKEY_CLIENT_SECRET="..."; $env:MOUSER_API_KEY="..."
partwatch check
```

**Quotas.** The Nexar free plan returns a lifetime total of 100 parts with a personal email signup, or 1000 with a business email. That allowance does not reset monthly. Each MPN costs one part (`candidates = 1`). DigiKey and Mouser allow about 1000 calls per day, and partwatch stops at 950. Answers are cached in `.partwatch/cache.sqlite` for 72 hours (`ttl_hours`). Repeat runs and CI runs (the cache is restored between them) only query new or expired parts. Failed lookups are never cached.

**Findchips.** Findchips has no API. Its owner, Supplyframe, offers data only through enterprise contracts. Scraping its pages breaks whenever the site changes and goes against its terms, so partwatch doesn't do it. Octopart covers the same multi-distributor view.

## How a part is rated

All sources are merged:
- **Lifecycle:** the most pessimistic known state wins. Disagreements between sources are listed.
- **Stock:** summed over distinct distributors. The same distributor seen through two sources is counted once.

| Rating | When |
|---|---|
| 🔴 red | Obsolete or last-time-buy; no stock anywhere; or MPN unknown to every source |
| 🟡 amber | NRND, preliminary, or unknown lifecycle; stock below `max(min_total_stock, refs × build_qty)`; long lead time while stock is short; only one distributor with stock |
| 🟢 green | Everything else |
| ⚪ gray | Every source errored (bad key, quota). Retried next run |

A brick takes the rating of its worst part. A non-generic symbol with no MPN makes its brick amber (`require_mpn`).
The report notes:
- a working alternate from `MPN_ALT` ("drop-in alternate available");
- Mouser's suggested replacement;
- any change since the previous run ("CHANGED since last run").

## Output

- `reports/STATUS.md`: bricks table, parts needing attention, all parts, and missing MPNs. Readable on GitHub.
- `reports/status.json`: everything, including raw per-source answers, for scripts and dashboards.
- `reports/parts.csv`: opens in a spreadsheet.

## CI

`.github/workflows/partwatch.yml` runs every Monday at 07:47 IST, on demand, and on PRs that touch `blocks/`. It:
1. restores the cache;
2. runs `partwatch check --fail-on red`;
3. puts STATUS.md in the job summary;
4. commits `reports/`;
5. opens an issue, or comments on the open one, when a brick is red.

A PR that adds a red part fails the check.

## Tests

`python -m pytest tests` covers extraction, field tidy-up, the lifecycle vocabulary, every provider adapter against recorded-style responses, scoring, caching and the CLI. The tests are offline.

## Extending

A new source is one class in `partwatch/providers/`: subclass `Provider`, implement `lookup()`, or `lookup_many()` for batch APIs, return `SourceResult`, and register it in `providers/__init__.py`. Element14/Farnell, LCSC and TI's own store API would fit this pattern.
