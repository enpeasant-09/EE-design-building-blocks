#!/usr/bin/env python3
"""eq2calc.py — formula screenshot -> calculator spec (JSON) + marimo cells.

Usage
-----
    python eq2calc.py shot.png --name vbus_div
    python eq2calc.py shot.png --name vbus_div --context "CP2102N VBUS divider, R in kOhm" --append design_block_template.py
    python eq2calc.py --spec eq/vbus_div.json            # re-verify / re-emit cells without calling the API

What it does
------------
1. Sends the screenshot (base64 image block) + the SAME prompt/schema used by the
   "New calculator from screenshot" box in design_block_doc.html to the Anthropic API.
2. Validates the returned JSON (names, ranges, python defines calc(...)).
3. Executes calc() at the default inputs in a fresh namespace and checks every output
   is a finite number.  NOTE: this runs model-written Python on your machine; read it
   first or use --no-exec.
4. Optional cross-check with sympy.parsing.latex.parse_latex (only if sympy + antlr4
   are installed; skipped otherwise).
5. Writes eq/<name>.json and prints a marimo cell pair (controls + result), or appends
   it to a notebook with --append (inserted before `if __name__ == "__main__":`).

Requirements: pip install anthropic   (reads ANTHROPIC_API_KEY from the environment)
"""
from __future__ import annotations

import argparse
import base64
import json
import keyword
import math
import os
import pathlib
import re
import sys

MODEL = "claude-sonnet-5-5"

# Keep this text identical to SAMPLE_PROMPT in design_block_doc.html.
PROMPT = r"""You convert an engineering formula screenshot (datasheet, application note or standard) into a live calculator for a hardware design document.
Return STRICT JSON only: one object, no markdown fences, no commentary. Schema:
{
  "id": "snake_case_identifier",
  "title": "short human title",
  "analysis_ref": "one of A1..A18 that fits best (A2 worst-case, A3 derating, A4 power, A5 thermal, A6 passives, A7 logic levels, A8 timing/reset, A9 clock, A10 signal integrity, A11 power integrity, A12 ESD, A13 EMC, A14 copper/creepage, A15 reliability) or empty string",
  "latex": "LaTeX of the equation(s) exactly as shown, without $ delimiters",
  "source": "document / page / equation number if visible in the image, else empty string",
  "inputs": [{"name": "python_identifier", "label": "display label (use _ for subscript, e.g. V_OUT)", "unit": "display unit, e.g. kΩ, mA, pF, V, °C", "min": 0, "max": 10, "step": 0.1, "value": 1, "tol_pct": 1, "desc": "meaning of the symbol"}],
  "outputs": [{"name": "python_identifier", "label": "display label", "unit": "display unit", "fmt": "python format spec such as .3f or .4g", "limit": {"min": 0}, "desc": "meaning"}],
  "python": "import math\n\ndef calc(a, b):\n    ...\n    return {\"out\": value}",
  "notes": "assumptions, validity range, symbols you could not read"
}
Rules:
- python must define def calc(...) with exactly the input names as keyword parameters and return a dict whose keys are exactly the output names, values plain floats.
- Use only the math module and numpy (import them in the source). No I/O, no randomness, no network, no prints.
- Inputs are given in their display units: convert to SI inside calc and convert results back to the output display units (be explicit with factors like 1e3, 1e-9).
- Identify every symbol in the image. Pick realistic electronics ranges for min/max/step and a default value (inside [min, max]) at which the formula evaluates without division by zero or domain errors.
- Use tol_pct only for inputs that are component values or supplies with a tolerance (e.g. resistors 1, capacitors 10, supply 5); omit otherwise.
- limit is optional; add it only when the image or common practice defines a pass/fail bound.
- If the image contains several related equations, implement all of them as outputs of one calc."""

MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESERVED = set(keyword.kwlist) | {"calc", "mo", "math", "np", "numpy"}


# --------------------------------------------------------------------------- API
def ask_claude(image: pathlib.Path, context: str, model: str, max_tokens: int) -> dict:
    """Send the screenshot + prompt; return the parsed JSON object."""
    try:
        import anthropic
    except ImportError:
        sys.exit("The 'anthropic' package is required: pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY in the environment.")
    media = MEDIA.get(image.suffix.lower())
    if not media:
        sys.exit(f"Unsupported image type {image.suffix} (use png/jpg/gif/webp)")
    data = base64.standard_b64encode(image.read_bytes()).decode("ascii")
    prompt = PROMPT + (f"\nContext from the engineer: {context.strip()}" if context.strip() else "")
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    return parse_json(text)


def parse_json(text: str) -> dict:
    """Parse the model reply, tolerating stray fences or prose around the object."""
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        i, j = t.find("{"), t.rfind("}")
        if i < 0 or j <= i:
            raise ValueError("No JSON object in the reply:\n" + text[:500])
        return json.loads(t[i:j + 1])


# --------------------------------------------------------------------------- validation
def _num(x, default):
    if isinstance(x, bool):
        return default
    if isinstance(x, (int, float)) and math.isfinite(x):
        return float(x)
    try:
        v = float(str(x))
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def validate_spec(o: dict) -> tuple[dict, list[str], list[str]]:
    """Mirror of validateSpec() in the HTML page. Returns (spec, errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(o, dict):
        return {}, ["reply is not a JSON object"], warnings
    spec: dict = {}
    spec["title"] = str(o.get("title") or "Untitled calculator")[:120]
    sid = re.sub(r"[^a-z0-9_]+", "_", str(o.get("id") or spec["title"]).lower()).strip("_")
    if not re.match(r"^[a-z_]", sid):
        sid = "c_" + sid
    spec["id"] = sid[:40] or "custom_calc"
    ref = str(o.get("analysis_ref") or "").strip()
    spec["analysis_ref"] = ref if re.fullmatch(r"A([1-9]|1[0-8])", ref) else ""
    for k in ("latex", "source", "notes", "python"):
        spec[k] = str(o.get(k) or "")
    spec["home"] = "s5"
    if not re.search(r"^\s*def\s+calc\s*\(", spec["python"], re.M):
        errors.append("python must define def calc(...)")
    ins, outs = o.get("inputs"), o.get("outputs")
    if not isinstance(ins, list) or not ins:
        errors.append("inputs must be a non-empty array")
        ins = []
    if not isinstance(outs, list) or not outs:
        errors.append("outputs must be a non-empty array")
        outs = []
    seen: set[str] = set()
    spec["inputs"] = []
    for n, i in enumerate(ins[:24]):
        i = i if isinstance(i, dict) else {}
        name = str(i.get("name") or "")
        if not IDENT.match(name) or name in RESERVED:
            errors.append(f'input {n + 1}: invalid name "{name}"')
        if name in seen:
            errors.append(f'duplicate name "{name}"')
        seen.add(name)
        lo, hi, val = _num(i.get("min"), 0.0), _num(i.get("max"), float("nan")), _num(i.get("value"), float("nan"))
        if math.isnan(val):
            val = 1.0 if math.isnan(hi) else (lo + hi) / 2
        if math.isnan(hi) or hi <= lo:
            hi = max(lo + 1, abs(val) * 10 or 10)
            warnings.append(f"input {name}: max fixed to {hi}")
        lo, hi = min(lo, val), max(hi, val)
        step = _num(i.get("step"), 0.0)
        if step <= 0:
            step = float(f"{(hi - lo) / 200:.2g}")
        r = {"name": name, "label": str(i.get("label") or name), "unit": str(i.get("unit") or ""),
             "min": lo, "max": hi, "step": step, "value": val}
        tol = _num(i.get("tol_pct"), 0.0)
        if 0 < tol <= 50:
            r["tol_pct"] = tol
        if i.get("desc"):
            r["desc"] = str(i["desc"])
        spec["inputs"].append(r)
    spec["outputs"] = []
    for n, q in enumerate(outs[:16]):
        q = q if isinstance(q, dict) else {}
        name = str(q.get("name") or "")
        if not IDENT.match(name):
            errors.append(f'output {n + 1}: invalid name "{name}"')
        fmt = str(q.get("fmt") or "")
        if not fmt or not re.fullmatch(r"[+\- ]?(\.\d{1,2})?[fegd%]?", fmt):
            fmt = ".4g"
        r = {"name": name, "label": str(q.get("label") or name), "unit": str(q.get("unit") or ""), "fmt": fmt}
        if isinstance(q.get("limit"), dict):
            lim = {k: _num(q["limit"].get(k), None) for k in ("min", "max", "warn_min", "warn_max")}
            lim = {k: v for k, v in lim.items() if v is not None}
            if lim:
                r["limit"] = lim
        if q.get("desc"):
            r["desc"] = str(q["desc"])
        spec["outputs"].append(r)
    m = re.search(r"def\s+calc\s*\(([^)]*)\)", spec["python"])
    if m and "**" not in m.group(1):
        params = [p.split("=")[0].split(":")[0].strip() for p in m.group(1).split(",") if p.strip()]
        for i in spec["inputs"]:
            if i["name"] not in params:
                errors.append(f'calc() has no parameter "{i["name"]}"')
    return spec, errors, warnings


# --------------------------------------------------------------------------- verification
def smoke_test(spec: dict) -> dict:
    """Run calc() at the defaults in a fresh namespace; return the outputs (raises on failure)."""
    ns: dict = {}
    exec(compile(spec["python"], f"<{spec['id']}>", "exec"), ns)
    kw = {i["name"]: i["value"] for i in spec["inputs"]}
    out = ns["calc"](**kw)
    if not isinstance(out, dict):
        raise TypeError(f"calc() returned {type(out).__name__}, expected dict")
    clean = {}
    for o in spec["outputs"]:
        if o["name"] not in out:
            raise KeyError(f"calc() did not return output '{o['name']}'")
        v = float(out[o["name"]])
        if not math.isfinite(v):
            raise ValueError(f"output '{o['name']}' is not finite at defaults: {v}")
        clean[o["name"]] = v
    return clean


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def sympy_crosscheck(spec: dict, outputs: dict) -> str:
    """Evaluate the LaTeX with sympy (if available) and compare with calc(). Informational only."""
    try:
        from sympy.parsing.latex import parse_latex
    except Exception:
        return "skipped (sympy not installed)"
    first = re.split(r"\\qquad|\\quad|;", spec["latex"])[0].strip().rstrip(",")
    try:
        expr = parse_latex(first)
    except Exception as e:  # antlr4 runtime missing or unsupported LaTeX
        return f"skipped (parse_latex failed: {type(e).__name__})"
    lhs = None
    if getattr(expr, "is_Relational", False):
        lhs, expr = expr.lhs, expr.rhs
    inputs = {_norm(i["name"]): i for i in spec["inputs"]}
    subs = {}
    for sym in expr.free_symbols:
        key = _norm(str(sym))
        if key not in inputs:
            return f"inconclusive (symbol {sym} not matched to an input name)"
        subs[sym] = inputs[key]["value"]
    try:
        val = float(expr.subs(subs).evalf())
    except Exception as e:
        return f"inconclusive ({type(e).__name__})"
    target = None
    if lhs is not None:
        target = next((o for o in spec["outputs"] if _norm(o["name"]) == _norm(str(lhs))), None)
    target = target or spec["outputs"][0]
    ref = outputs[target["name"]]
    if abs(val - ref) <= 1e-6 * max(abs(ref), 1e-30):
        return f"match: LaTeX gives {val:.6g} = calc() {target['name']}"
    ratio = val / ref if ref else float("inf")
    return (f"differs: LaTeX with raw input numbers gives {val:.6g}, calc() {target['name']} = {ref:.6g} "
            f"(ratio {ratio:.4g}); expected when calc() converts display units (kΩ, mA, ...)")


# --------------------------------------------------------------------------- marimo cells
def _pyraw(s: str, q: str) -> str:
    """Raw triple-quoted literal when safe, else repr()."""
    if q not in s and not s.endswith("\\") and q[0] * 3 not in s:
        return "r" + q + s + q
    return repr(s)


def _indent(s: str, n: int = 4) -> str:
    return "\n".join((" " * n + line) if line else line for line in s.split("\n"))


def marimo_cells(spec: dict) -> str:
    """Two marimo cells (controls, result): same structure as the page's 'Copy as marimo cell'."""
    v = re.sub(r"\W", "_", spec["id"])
    tols = {i["name"]: i["tol_pct"] for i in spec["inputs"] if i.get("tol_pct")}
    ret = [f"{v}_src", f"{v}_ui"] + ([f"{v}_wc"] if tols else [])
    head = f"\n### {spec['title']}\n\n$$\n{spec['latex']}\n$$\n" + (f"\n*Source: {spec['source']}*\n" if spec["source"] else "")
    src = spec["python"].rstrip() + "\n"
    disp = [f"mo.md({_pyraw(head, chr(34) * 3)})", f"{v}_ui"] + ([f"{v}_wc"] if tols else [])
    # String literals must not be re-indented (that would change their value), so cell 1 is built line by line.
    cell1 = ["@app.cell", "def _(mo):", f"    {v}_src = {_pyraw(src, chr(39) * 3)}", f"    {v}_ui = mo.ui.dictionary({{"]
    for i in spec["inputs"]:
        lbl = i["label"] + (f" [{i['unit']}]" if i["unit"] else "")
        cell1.append(f"        {i['name']!r}: mo.ui.slider({i['min']!r}, {i['max']!r}, step={i['step']!r}, value={i['value']!r}, "
                     f"label={json.dumps(lbl, ensure_ascii=False)}, show_value=True, include_input=True),")
    cell1.append("    })")
    if tols:
        cell1.append(f'    {v}_wc = mo.ui.switch(label="Worst-case (EVA corners)")')
    cell1 += [f"    mo.vstack([{', '.join(disp)}])", f"    return ({', '.join(ret)},)"]
    meta = "\n".join(f"    ({o['name']!r}, {json.dumps(o['label'], ensure_ascii=False)}, {json.dumps(o['unit'], ensure_ascii=False)}, "
                     f"{o['fmt']!r}, {o.get('limit', {})!r})," for o in spec["outputs"])
    wc_flag = f"{v}_wc.value" if tols else "False"
    body = f"""_ns = {{}}
exec({v}_src, _ns)
_kw = dict({v}_ui.value)
_r = _ns["calc"](**_kw)
_meta = [
{meta}
]
_tol = {tols!r}
_lo, _hi = {{}}, {{}}
if {wc_flag}:
    import itertools as _it
    for _signs in _it.product((-1.0, 1.0), repeat=len(_tol)):
        _k2 = dict(_kw)
        for (_n, _p), _sg in zip(_tol.items(), _signs):
            _k2[_n] = _kw[_n] * (1 + _sg * _p / 100.0)
        for _k, _x in _ns["calc"](**_k2).items():
            _lo[_k] = min(_lo.get(_k, _x), _x)
            _hi[_k] = max(_hi.get(_k, _x), _x)
_rows = []
for _k, _lbl, _u, _f, _lim in _meta:
    _v = float(_r[_k])
    _st = ""
    if _lim:
        _st = "PASS"
        if ("warn_min" in _lim and _v < _lim["warn_min"]) or ("warn_max" in _lim and _v > _lim["warn_max"]):
            _st = "WARN"
        if ("min" in _lim and _v < _lim["min"]) or ("max" in _lim and _v > _lim["max"]):
            _st = "FAIL"
    _wc = f" ({{_lo[_k]:{{_f}}}} … {{_hi[_k]:{{_f}}}})" if _k in _lo else ""
    _rows.append(f"| {{_lbl}} | `{{_v:{{_f}}}}`{{_wc}} | {{_u}} | {{_st}} |")
mo.vstack([
    mo.md("| Output | Value (EVA min … max) | Unit | Check |\\n|---|---|---|---|\\n" + "\\n".join(_rows)),
    mo.accordion({{"Show Python": mo.ui.code_editor(value={v}_src, language="python", disabled=True)}}),
])"""
    cell2 = f"@app.cell\ndef _({', '.join(sorted(['mo'] + ret))}):\n{_indent(body)}\n    return\n"
    return "\n".join(cell1) + "\n\n\n" + cell2


def append_to_notebook(nb: pathlib.Path, cells: str) -> None:
    text = nb.read_text(encoding="utf-8")
    marker = 'if __name__ == "__main__":'
    k = text.rfind(marker)
    if k < 0:
        sys.exit(f"{nb} does not look like a marimo notebook (no `{marker}`)")
    nb.write_text(text[:k].rstrip() + "\n\n\n" + cells.rstrip() + "\n\n\n" + text[k:], encoding="utf-8")


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Formula screenshot -> calculator spec + marimo cells")
    ap.add_argument("image", nargs="?", type=pathlib.Path, help="screenshot (png/jpg/gif/webp)")
    ap.add_argument("--name", help="calculator id / output file name (default: from the reply)")
    ap.add_argument("--context", default="", help="extra hint for the model (part, units, which equation)")
    ap.add_argument("--spec", type=pathlib.Path, help="use an existing JSON spec instead of calling the API")
    ap.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("eq"))
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--append", type=pathlib.Path, help="append the marimo cells to this notebook .py")
    ap.add_argument("--no-exec", action="store_true", help="do not execute the generated Python")
    a = ap.parse_args(argv)

    if a.spec:
        raw = json.loads(a.spec.read_text(encoding="utf-8"))
        raw = raw.get("spec", raw)          # accept eq/<name>.json written by this tool
    elif a.image:
        if not a.image.exists():
            sys.exit(f"{a.image} not found")
        raw = ask_claude(a.image, a.context, a.model, a.max_tokens)
    else:
        ap.error("give a screenshot or --spec")

    spec, errors, warnings = validate_spec(raw)
    if a.name:
        spec["id"] = re.sub(r"\W", "_", a.name)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    if errors:
        bad = a.out_dir / f"{spec.get('id') or 'reply'}.raw.json"
        bad.write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
        print("Spec problems:\n- " + "\n- ".join(errors), file=sys.stderr)
        print(f"Raw reply saved to {bad}; fix it and rerun with --spec.", file=sys.stderr)
        return 1
    for w in warnings:
        print("note:", w, file=sys.stderr)

    result = {"spec": spec, "verified": False}
    if a.no_exec:
        print("Smoke test skipped (--no-exec).", file=sys.stderr)
    else:
        try:
            outs = smoke_test(spec)
        except Exception as e:
            print(f"Smoke test FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            (a.out_dir / f"{spec['id']}.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
            return 2
        result.update(verified=True, defaults_out=outs, sympy=sympy_crosscheck(spec, outs))
        print("Smoke test OK at defaults: " + ", ".join(f"{k}={v:.6g}" for k, v in outs.items()), file=sys.stderr)
        print("sympy cross-check: " + result["sympy"], file=sys.stderr)

    path = a.out_dir / f"{spec['id']}.json"
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path}", file=sys.stderr)

    cells = marimo_cells(spec)
    if a.append:
        append_to_notebook(a.append, cells)
        print(f"Appended cells to {a.append}", file=sys.stderr)
    else:
        print(cells)
    return 0


if __name__ == "__main__":
    sys.exit(main())
