# Design-block doc kit: one-time venv setup + self-test (Windows PowerShell)
# Run from this folder:   powershell -ExecutionPolicy Bypass -File .\setup_and_test.ps1
# Creates .venv here, installs the toolchain, checks the marimo template, exports a browser (WASM) build,
# and writes setup_report.txt so Claude can read the results back from this folder.

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot
$report = Join-Path $PSScriptRoot "setup_report.txt"
"Design-block doc kit setup report  $(Get-Date -Format s)" | Out-File $report -Encoding utf8
function Log($msg) { Write-Host $msg; $msg | Out-File $report -Append -Encoding utf8 }
function Run($label, [scriptblock]$cmd) {
    Log "`n=== $label ==="
    $out = & $cmd 2>&1 | Out-String
    Log $out.TrimEnd()
    Log ("exit code: " + $LASTEXITCODE)
}

# 1. Python + venv
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $base = "py"; $baseArgs = @("-3") } else { $base = "python"; $baseArgs = @() }
Run "python version" { & $base @baseArgs --version }
if (-not (Test-Path ".venv")) { Run "create venv" { & $base @baseArgs -m venv .venv } }
$vpy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Run "pip upgrade" { & $vpy -m pip install --upgrade pip }
Run "install packages" { & $vpy -m pip install marimo sympy "antlr4-python3-runtime==4.11.*" pint latex2sympy2_extended anthropic numpy matplotlib }
Run "versions" { & $vpy -c "import marimo,sympy,pint,numpy;print('marimo',marimo.__version__,'sympy',sympy.__version__,'pint',pint.__version__,'numpy',numpy.__version__)" }

# 2. Static + runtime checks on the marimo template
Run "marimo check" { & .venv\Scripts\marimo.exe check design_block_template.py }
Run "marimo check (WASM compat)" { & .venv\Scripts\marimo.exe check design_block_template.py --select MW }
# 'export html' executes every cell: any runtime error in a calculator shows up here
Run "execute notebook (export html)" { & .venv\Scripts\marimo.exe export html design_block_template.py -o build\template_static.html }

# 3. SymPy LaTeX parsing sanity check (used by eq2calc cross-check)
Run "sympy parse_latex" { & $vpy -c "from sympy.parsing.latex import parse_latex; e=parse_latex(r'V_{BUS}\frac{R_{2}}{R_{1}+R_{2}}'); print(e, e.free_symbols)" }
Run "latex2sympy2_extended" { & $vpy -c "from latex2sympy2_extended import latex2sympy; print(latex2sympy(r'\frac{1}{2\pi R C}'))" }

# 4. eq2calc CLI smoke test (no API call)
Run "eq2calc --help" { & $vpy eq2calc.py --help }

# 5. Browser build of the template (serve with: .venv\Scripts\python -m http.server -d dist)
Run "export html-wasm" { & .venv\Scripts\marimo.exe export html-wasm design_block_template.py -o dist --mode run --show-code }

Log "`nDone. Open the notebook with:  .venv\Scripts\marimo.exe edit design_block_template.py"
Log "Serve the browser build with:  .venv\Scripts\python.exe -m http.server -d dist   then open http://localhost:8000"
