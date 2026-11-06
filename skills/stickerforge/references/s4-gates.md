# S4 Gates

Contents: running, gate set, thresholds, folders, what gates cannot see

## Running

`scripts/run.py <project> --from S4` calls every `scripts/gates/g*.py` on `<project>/out/` (file name order, `_` files skipped). Contract, JSON output and exit codes: `scripts/gates/README.md`. Per-gate options: `python3 scripts/gates/<gate>.py --help`, set per project in `spec.json` under `gates`. Spec `transparent: false` skips the alpha, checker, margin and outline gates.

## Gate set (the folder is the truth)

| Gate | Fails when (code) |
|---|---|
| g01 size | Short side below `min_px` (`TOO_SMALL`, default 1024), or aspect ratio too wide (`BAD_RATIO`) |
| g02 alpha | No alpha channel (`NO_ALPHA`), no transparent pixel (`ALL_OPAQUE`), opaque corner (`CORNER_OPAQUE`) |
| g03 checker | Checkerboard painted into pixels (`FAKE_CHECKER`) |
| g04 margin | Content touches the edge (`TOUCHES_EDGE`) or margin below `--margin` px (`LOW_MARGIN`, default 8) |
| g05 outline | White die-cut border is broken (`OUTLINE_BROKEN`) |
| g06 dup | Another picture within `--max-dist` Hamming bits of 255 (`DUPLICATE`) |

Alpha cleanup (12 and below to 0, 240 and above to 255) is done at save time by `scripts/postprocess.py`, not by a gate. It never repairs a checkerboard; those fail.

## Folders and ledger

Passed files stay in `out/` with status `passed`. Failed files move to `qc/rejected/<id>.a<attempt>.png` with status `gate_failed` and the reason in the ledger. Only `passed` ids are exported. Thresholds live in the gate scripts and `spec.json`; do not raise a threshold to make a file pass.

## What gates cannot see

Wrong glyphs, a character that drifted from the reference, odd anatomy, off-concept poses. A separate reviewer samples `out/` for these. It is a sample, not a guarantee. Feed it the reference image, the style text, and the concept prompts; put two known-bad files in the sample, and if it misses them, discard its verdict.

Next: `s5-retry.md`.
