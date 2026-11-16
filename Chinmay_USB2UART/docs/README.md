# Design-block documentation kit

One documentation template per KiCad hierarchical design block (e.g. `Documents\Chinmay_USB2UART\USB2UART_CP2102N`). It covers the schematic and layout docs, analyses A1–A18, datasheet excerpts, and Python calculators you can see the code of.

| File | What it is |
|---|---|
| `design_block_doc.html` | The live template, as one self-contained page. It's prefilled with the **USB2UART CP2102N** worked example. Its calculators run real Python (Pyodide + numpy) and show the formula through MathJax. A screenshot box turns a formula into a calculator. It can export a marimo notebook and Markdown. |
| `design_block_template.py` | A marimo notebook with the same sections, made by the page's own exporter. It has slider calculators with a "Show Python" accordion, `mo.image("public/…")` slots, and a cell that compares the BOM against the calculators. |
| `eq2calc.py` | CLI that turns a formula screenshot into a calculator spec (`eq/<name>.json`) plus a marimo cell. It uses the Anthropic API and the same prompt and schema as the page. |

## Workflow

1. **Start a block doc.** Open the page (or its claude.ai artifact). You can keep the example as a guide or click **Clear example → blank template**. Edits are saved in this browser only (localStorage), so use the exports to keep the doc in git.
2. **Datasheet values.** Snip with **Win+Shift+S**, click an image slot (or a datasheet-excerpt card in §10), then press **Ctrl+V**. Fill in the caption fields and transcribe the key numbers. **Apply to…** pushes a value into a calculator input and records the citation.
3. **A formula becomes a calculator.** You have two routes:
   - **In the page:** paste the snip into **＋ New calculator from screenshot**, then click **Generate calculator**. Claude returns JSON and Python. The page validates the spec and smoke-tests it in Pyodide before adding it to §5. The manual form below that box always works, even when the AI path is unavailable.
   - **From the terminal:** `python eq2calc.py shot.png --name vbus_div --append design_block_template.py`. Use `--spec eq/vbus_div.json` to re-run without calling the API, and `--no-exec` to skip running the generated code.
4. **Export.** **Export marimo notebook** and **Export Markdown** open a modal with a Copy button, because downloads are blocked in the artifact sandbox. Save the result as `<block>.py` or `<block>.md` next to the KiCad library and commit it.

## KiCad 10 exports (kicad-cli)

```bat
:: schematic sheet as SVG (vector) or PDF
kicad-cli sch export svg -o export\ USB2UART_CP2102N.kicad_sch
kicad-cli sch export pdf -o export\USB2UART_CP2102N.pdf USB2UART_CP2102N.kicad_sch

:: BOM with all fields (Manufacturer, MPN1, MPN2, MFR2, Procurement, Procurement2, Cost, Derating)
kicad-cli sch export bom --fields "*" --ref-range-delimiter "" -o bom.csv USB2UART_CP2102N.kicad_sch
::   If your build rejects "*", list the fields:
::   --fields "Reference,Value,Footprint,Manufacturer,MPN1,MPN2,MFR2,Procurement,Procurement2,Cost,Derating,${QUANTITY}"

:: layout picture
kicad-cli pcb export svg --layers F.Cu,F.Silkscreen,Edge.Cuts -o export\layout.svg board.kicad_pcb
```

Put `bom.csv` next to the notebook. The BOM cell parses KiCad values (`22.1k`, `4k7`, `100nF`, `27R`) and expands grouped or ranged refs (`R201,R202`, `R201-R203`). It then flags any calculator input whose refdes value doesn't match the schematic (for example R201 ↔ `vbus_div.R1`).

## marimo

```bash
marimo edit design_block_template.py
marimo export html-wasm design_block_template.py -o dist --mode run --show-code
python -m http.server -d dist          # WASM exports must be served over HTTP, not opened via file://
```
Save images to `public/<slot>.png`. The slot names are shown in each image cell.

## Offline use

- The page loads Pyodide 0.27.7 and MathJax 3 from jsDelivr. Without them the prose, tables and image slots still work. Calculators then show "Python runtime unavailable", and equations appear as raw LaTeX.
- To run fully offline, download the Pyodide `full/` folder and `tex-svg.js` into a folder and serve it with `python -m http.server 8000`. Pyodide cannot load from `file://`. Then set `window.DBDOC_PYODIDE_URL = "http://localhost:8000/pyodide/"` and `window.DBDOC_MATHJAX_URL = "http://localhost:8000/tex-svg.js"` in a `<script>` placed before the main script.

## Notes

- Numbers tagged **verify** are illustrative until checked against the archived datasheet revision or your derating standard (ECSS-Q-ST-30-11, NASA EEE-INST-002, …). That covers derating factors, θJA/ΨJT, pin ratings, the USBLC6 clamp points and λb.
- Worst-case mode runs every EVA corner (2ⁿ, n ≤ 8), an RSS sensitivity estimate, and a Monte-Carlo run (N = 2000, Gaussian with tol = 3σ, clipped at ±tol). All of it runs in Python inside the page.

## Keeping project context (workflow.py)

Graphify cannot read KiCad schematics, so each project keeps its own context file instead: `<project>/docs/CONTEXT.md`, with a stage flowchart, a block map, open items and a decisions log. It is generated from `<project>/docs/workflow.json` and a scan of the KiCad files by `Chinmay_LIB/tools/workflow.py`. Update it at every stage so the history never has to be retold:

```bash
python Chinmay_LIB/tools/workflow.py stage Chinmay_USB2UART layout --status wip --note "CP2102N placed"
python Chinmay_LIB/tools/workflow.py log   Chinmay_USB2UART "Moved ESD array next to the connector"
python Chinmay_LIB/tools/workflow.py open  Chinmay_USB2UART "Check VBUS divider against rev C datasheet"
python Chinmay_LIB/tools/workflow.py refresh        # rescan KiCad files, rewrite every CONTEXT.md
```

Start every session by reading the repo-root `CONTEXT.md`, then the project's own. Export this kit's per-block analysis (Markdown or marimo) next to it and record the export with `log`.
