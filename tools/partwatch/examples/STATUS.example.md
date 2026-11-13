# Design block part status

Checked 2026-11-12 15:01 UTC via demo.

**Bricks:** 1 🔴 · 1 🟡 · 1 🟢  
**Parts:** 1 🔴 · 2 🟡 · 2 🟢 · 0 ⚪

## Bricks

| Brick | Status | Parts | No MPN | Worst |
|---|---|---:|---:|---|
| `Interface/USB_UART_CP2104` | 🔴 Act | 2 |  | CP2104-F03-GMR |
| `Power/BUCK_12V-5V_3A` | 🟡 Watch | 2 | 1 | SRP7028A-100M |
| `Power/LDO_ADJ` | 🟢 OK | 2 |  |  |

## Needs attention

| MPN | Manufacturer | Status | Lifecycle | Stock | Distributors | Lead | Why | Used in |
|---|---|---|---|---:|---|---|---|---|
| `CP2104-F03-GMR` | Silicon Labs | 🔴 Act | obsolete | 0 | 0 | – | lifecycle obsolete (Obsolete); no stock at any distributor | Interface/USB_UART_CP2104 (U1) |
| `SRP7028A-100M` | Bourns | 🟡 Watch | active | 900 | 1 | 20 wk | single source: only Mouser has stock | Power/BUCK_12V-5V_3A (L1) |
| `TPS54331DR` | Texas Instruments | 🟡 Watch | nrnd | 28,000 | 2 | 6 wk | lifecycle nrnd (Not Recommended for New Designs); drop-in alternate available: TPS54332DDA; alt TPS54332DDA: green (active, 12000 pcs) | Power/BUCK_12V-5V_3A (U1) |

## All parts

| MPN | Manufacturer | Status | Lifecycle | Stock | In stock at | Sources |
|---|---|---|---|---:|---|---|
| `CP2104-F03-GMR` | Silicon Labs | 🔴 Act | obsolete | 0 |  | demo |
| `SRP7028A-100M` | Bourns | 🟡 Watch | active | 900 | Mouser | demo |
| `TPS54331DR` | Texas Instruments | 🟡 Watch | nrnd | 28,000 | DigiKey, Mouser | demo |
| `GRM188R61A106KE69D` | Murata | 🟢 OK | active | 1,900,000 | DigiKey, LCSC | demo |
| `LM1117IMPX-ADJ/NOPB` | TI | 🟢 OK | active | 80,000 | DigiKey, Mouser | demo |

## Placements without a usable MPN

Add an `MPN` and `Manufacturer` field to these symbols.

| Brick | Ref | Value | Symbol | Problem |
|---|---|---|---|---|
| `Power/BUCK_12V-5V_3A` | D1 | B340 | `Diode:B340` | no MPN field |

_2 generic passives without an MPN were not checked (see `rules.generic_ok`)._
