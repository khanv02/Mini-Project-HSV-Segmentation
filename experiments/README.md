# Reproducible HSV experiments

This directory retains ten source images, two settings per image, immutable run artifacts,
and exact environment metadata. From the repository root, recreate evidence in an empty
`experiments/runs/` directory with:

```powershell
uv run python scripts/generate_experiment_evidence.py
```

The generator refuses to write when the runs directory is nonempty. This prevents existing
UUID-named evidence from being silently replaced. Each complete run contains `record.json`,
`mask.png`, and `result.png`; a directory without `record.json` is incomplete and must not be
reported as successful.

Use `manifest.json` to locate each source, verify its SHA-256, and apply the documented broad
and narrow threshold sets. Use `environment.json` to reproduce Python, Tcl/Tk, package, build,
and platform details. Run the automated replay with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_experiment_reproduction.py -q
```

`report.md` compares original/mask/result artifacts and explains broad-versus-narrow tradeoffs
without claiming ground-truth accuracy. Eight inputs are licensed SimpleCube++ photographs with
natural, artificial, or mixed illumination metadata. The remaining two are the fixed real scene
`main_experiment120` from the MIT CSAIL Multi-Illumination Dataset under directional lights 0
and 24. Both sources permit reuse with attribution; exact provenance, permission and hashes are
recorded in `manifest.json`.
