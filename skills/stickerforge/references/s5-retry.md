# S5 Retry

Contents: limit, what a retry is, by reason, at the limit

## Limit

`run.py --from S5` regenerates every `gate_failed` or `gen_failed` id, in up to 2 rounds, and gates the new files. An id still failing after round 2 gets status `exhausted`, is listed in `qc/failed.md`, and is left out of the export. `run.py` then exits 5.

## What a retry is

The runner repeats the same prompt. To change the prompt, edit that concept's `prompt` in `spec.json` before running S5; the file is read again on every run. Keep `style` and `ref` unchanged.

| Reason | Edit to the concept prompt |
|---|---|
| `FAKE_CHECKER`, `NO_ALPHA` | Add: plain empty background, no pattern, no checkerboard. |
| Garbled or wrong text | Shorten the string to one word, or drop the text. Never overlay text. |
| `TOUCHES_EDGE`, `LOW_MARGIN` | Add: character fits within 80 percent of the canvas. |
| `DUPLICATE` | Rewrite pose and expression, not the style. |
| Off-reference character | Restate two or three identifying features in `character`. |
| Refusal | See `failure-playbook.md`. Rewrite the situation in neutral words. |
| Quota or auth error (429, 401, 403) | The run stops with exit 6 and no retry is spent. Fix, then rerun the same command. |

## At the limit

Report to the user: passed count, exhausted ids, top reason codes. Offer: drop them, replace with new concepts (add to `spec.json`, run S3 to S5 again), or accept the gap.

Next: `s6-export.md`.
