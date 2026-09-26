# Read, verify and reproduce

All commands below start in `research/cgb_ecosystem`, the folder containing the report and notebook. This folder can also be copied out of the repository: the experiment imports its included model snapshot, not a separately installed or newer version of the parent project.

## Read the existing experiment

Open [REPORT.md](../REPORT.md) or [simulation-results.ipynb](../simulation-results.ipynb). The notebook loads saved tables and plots; running its cells does not retrain anything. Use a notebook environment such as Jupyter with IPython available. The report uses vector equation images in ordinary Markdown, with LaTeX preserved in SVG metadata and [source.json](../equations/source.json). Keep the asset folders beside the report.

## Verify the saved artifacts

The recorded execution used Python 3.12.3. Use an isolated environment and install the tested numerical dependencies:

```sh
python -m pip install -r requirements-tested.txt
python -m simulation.verify_bundle
python -m simulation.verify_simulation
```

`verify_bundle` reads the manifest, verifies every inventoried file hash, detects missing or unexpected deliverable files and checks the archived model against all frozen deployments. Ignored Python caches and optional installed renderer dependencies are excluded from the inventory. `verify_simulation` checks the synthetic measurement, valuation, probability, accounting and replay identities and rewrites its verification record. It reads the included example notebook; no original Downloads path is required.

## Generate a new experiment without replacing this one

The completed directory is protected by `COMPLETE.json`. In PowerShell, choose a new output directory outside this saved study:

```powershell
$env:CGB_SIMULATION_OUTPUT = Join-Path (Get-Location) '..\cgb_ecosystem-rerun'
python -m simulation.structured_simulation
```

The command generates the declared 11 experiments using the included model source and protocol. It does not rerun the unrelated supplied RFQ notebook. After generation, copy the saved reference and its original audit into the new directory to make the report's reference comparison available:

```powershell
Copy-Item -LiteralPath 'reference' -Destination $env:CGB_SIMULATION_OUTPUT -Recurse
Copy-Item -LiteralPath 'example-audit' -Destination $env:CGB_SIMULATION_OUTPUT -Recurse
Copy-Item -LiteralPath 'source-register.json' -Destination $env:CGB_SIMULATION_OUTPUT
python -m simulation.verify_simulation
python -m simulation.simulation_report
python -m simulation.report_narrative
npm install --prefix simulation
node simulation/render_report_math.cjs
Remove-Item Env:CGB_SIMULATION_OUTPUT
```

This rebuilds experiment outputs, scientific plots and the Markdown report in the new directory. The delivered notebook, original screenshots, historical archive and packaging manifest are records of the original study; this command sequence does not regenerate those publication artifacts. Narrative links to the original archive/notebook refer to this published bundle and should be updated if publishing a separate report. Do not copy a prior manifest onto newly generated results and imply its hashes still apply.

The source snapshot and seeds support reproducibility of calculations. UUIDs, runtimes, gzip metadata and numerical-library/platform differences can prevent byte-identical reruns. Compare scientific outputs using appropriate tolerances. The recorded dependency versions and per-fit source hashes provide the reference environment.

## Regenerate this report's presentation only

With `CGB_SIMULATION_OUTPUT` unset, the following use existing saved results and overwrite their presentation files:

```sh
python -m simulation.simulation_report
python -m simulation.report_narrative
npm install --prefix simulation
node simulation/render_report_math.cjs
```

The narrative step emits LaTeX display equations. The renderer checks them with KaTeX and converts them with MathJax to SVG images. Run both narrative and renderer in sequence to restore the delivered appearance. Presentation changes invalidate affected hashes until the manifest is deliberately rebuilt with `python -m simulation.verify_bundle --write`. Writing a new manifest records current contents; it is not a substitute for reviewing changes or rerunning the scientific checks.

To repeat the light/dark preview audit, install the renderer dependencies, install a Playwright Chromium browser from the `simulation` directory with `npx playwright install chromium`, then run `node simulation/verify_report.cjs` from this study folder. Alternatively, set `BROWSER_EXECUTABLE` to an existing compatible browser's full executable path. The audit creates PNG screenshots and a JSON check record, rendering the Markdown in memory without saving an HTML file. Node.js 20 or newer is required by these optional presentation dependencies.
