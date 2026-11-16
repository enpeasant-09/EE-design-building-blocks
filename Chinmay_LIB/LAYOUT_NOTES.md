# Layout task hand-off (for a local Claude Code session on this PC)

**Task:** design PCB layouts for all watchdog design blocks and all oscillator design blocks. Set DRC to JLCPCB 2-layer rules and keep each layout tight. Show a picture in chat after each block.

## Blocks
- **Oscillators (9):** `<Documents>\Chinmay_XTAL\Chinmay_XTAL.kicad_blocks\XO_*.kicad_block`
- **Watchdogs (18):** `<Documents>\EE design blocks\WD and RST *.kicad_block`

## Tool
`<Documents>\Chinmay_LIB\tools\genlayout.py`. Run it with KiCad's Python:

```
"C:\Program Files\KiCad\10.0\bin\python.exe" "<Documents>\Chinmay_LIB\tools\genlayout.py" "<block folder>"
```

For each block it:
1. Exports the netlist.
2. Places parts.
3. Routes F.Cu/B.Cu, with a GND via at each GND pad.
4. Writes `<name>.kicad_pcb` into the block folder.
5. Runs DRC with `kicad-cli pcb drc` against a temporary B.Cu GND plane.
6. Writes `<name>_layout.svg` and `<name>_layout.json`.

**Status:** Placement and routing worked on `XO_25MHz_ECS2520MV`. The DRC step was rewritten to use kicad-cli and has not been run yet. Delete any stray `.kicad_pro` or `.kicad_prl` left in that block folder.

## Datasheet layout rules (applied as placement constraints)
- 100 nF decoupling cap next to the VDD pin, with a short VDD-to-GND loop. No long VDD traces (TPS382x: an LC ringing risk).
- Timing caps (CWD, CRST, SRT, SWT) right at their pins, with nothing routed under them. Use C0G for CWD on TPS3850/51. The MAX16056 SRT/SWT pins see ~240 nA ramp currents, so keep them away from leakage.
- RESET/WDO pull-ups close to their pins.
- The exposed pad (DFN/VSON) goes to GND with a via.
- Oscillator: cap at pin 4 (VDD), series R at the output pin, short output trace.
- JLC rules:
  - tracks 0.20 mm (0.30 mm for supplies), clearance 0.15 mm;
  - via 0.6/0.3 mm, annular ring at least 0.13 mm;
  - copper to edge 0.3 mm;
  - silkscreen 0.8 mm high, 0.15 mm lines.

## Footprint fixes (the script also writes them back to the block schematic)
- `Chinmay_Supervisor:` → `Chinmay_Footprints:`
- `PCM_SparkFun-Resistor:` → `Resistor_SMD:`
- TPS35 DDF and TPS3851 VSON-8 → the `Chinmay_Footprints` copies, which have STEP models.

## Picture
Convert the SVG to PNG, for example with `"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb render` for a 3D view, or any SVG-to-PNG tool. Show it in chat. Review the picture before moving to the next block, and fix any DRC errors or unrouted nets first.

## Afterwards
- Record progress: `python Chinmay_LIB\tools\workflow.py stage Chinmay_XTAL layout --status wip --note "..."`.
- Copy the new `.kicad_pcb` files into the `EE design blocks` repo copy.
- Ask before committing.
