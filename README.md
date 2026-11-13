# EE design building blocks

Chinmay's KiCad 10 design-block library: proven circuit bricks that are placed as sheets with clear inputs and outputs, plus the parts, tools and checks behind them.

## Contents

```
EE design blocks/                 KiCad design-block library (point KiCad at this folder)
  WD and RST TPS3823.kicad_block  Chinmay's original watchdog + reset block (the template)
  WD and RST <IC>.kicad_block     17 generated variants, one per supervisor IC
library/
  Chinmay_Supervisor.kicad_sym    symbols for the supervisor ICs that KiCad does not ship
  Chinmay_Supervisor.pretty/      ADI WLCSP-6 footprint for the ADM8613
projects/Chinmay_WD_RST/          test project: one sheet per IC, ERC clean, PDF included
tools/wdgen/                      generator for the WD/RST bricks + independent net checker
tools/partwatch/                  lifecycle / stock checker (Octopart, DigiKey, Mouser)
partwatch.toml                    partwatch config for this repo
.github/workflows/partwatch.yml   weekly EOL/stock check, opens an issue when a brick goes red
```

## Watchdog + reset bricks

Every brick copies the circuit of `WD and RST TPS3823`:

1. **Supervisor**, chosen per brick.
2. **74LVC1G32 OR gate** with a PROG bypass: a solder jumper to 3V3 plus a 10K pull-down, so the watchdog does not reset the MCU while you flash it.
3. **74LVC1G07 open-drain buffer** driving `nRST`.
4. **MR push button** with an ESD9B3.3 diode.

Sheet pins: `WDI` (input) and `nRST` (output).

| Group | Package / pinout | Bricks |
|---|---|---|
| 1 | SOT-23-5, MAX823 pinout (WDI, ~MR, ~RESET) | TPS3823, TPS3828, STM6822, STM6823, MCP1316, MCP1316M, MCP1320 |
| 2 | SOT-23-5, MAX824 pinout (no MR; button drives nRST) | TPS3824, STM6824, MCP1318, MCP1321 |
| - | SOT-23-THN-8, pinout option C | TPS35 |
| - | VSON-8 / VSON-10 | TPS3851, TPS3850 (window watchdog: 800-1600 ms) |
| - | TDFN-8 3x3 | MAX16056 (39 nF = 200 ms reset, 330 nF = 1.7 s watchdog) |
| - | WLCSP-6 | ADM8613 (standard part trips at 2.32 V) |
| - | SOT-23-8 | MAX6369 (watchdog only, no voltage monitor) |

### Part data on every symbol

| Field | Content |
|---|---|
| `MPN1`, `Manufacturer` | Primary part |
| `MPN2`-`MPN4`, `MFR2`-`MFR4` | Three alternates for each passive. Supervisors list their pin-compatible alternates in `MPN2` |
| `IPN` | Internal part number. The same value, rating and operating voltage always get the same MPN |
| `Procurement` / `Procurement2` | DigiKey India / Mouser India search links for `MPN1` |
| `Derating` | Pass/fail summary. The full table is printed on each sheet |

**Derating rules:** 85 °C ambient and a 3.3 V rail +5 %.
- **Ceramic capacitors:** applied voltage ≤ 50 % of rated, and the dielectric's maximum temperature ≥ ambient + 20 °C.
- **Resistors:** power ≤ 50 % of the rating after temperature derating, and voltage ≤ 80 % of maximum working voltage.

All passives inside the bricks pass. The 10 µF X5R bulk capacitor on the test project's root sheet fails the temperature rule. It exists only to anchor the test bench and is not part of any brick.

## Using a brick

1. In KiCad, go to **Preferences > Manage Design Block Libraries** and add the `EE design blocks` folder.
2. Add `library/Chinmay_Supervisor.kicad_sym` and `library/Chinmay_Supervisor.pretty` to your symbol and footprint library tables.
3. In the schematic, open the Design Blocks panel, tick **Place as sheet** and place the brick.

## Regenerating / checking

```bash
python3 tools/wdgen/gen_wd.py      # rewrites projects/Chinmay_WD_RST, the 17 generated blocks and library/
python3 tools/wdgen/verify.py      # independent connectivity check against the generator's intent
PYTHONPATH=tools/partwatch python3 -m partwatch check   # needs DigiKey / Mouser / Nexar keys
```

The generator reads the original `WD and RST TPS3823` block as its template and never writes to it.

## Before release

- Confirm these order codes are released, then run `partwatch check`: TPS35CA40KAGDDFR, TPS3851G33SDRBR, the MCP13xx `-29LE/OT` codes, and STM6822TWY6F.
- Check the MAX16056 footprint against Maxim land pattern 90-0059, and the ADM8613 WLCSP footprint against the datasheet drawing.
