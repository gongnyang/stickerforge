# S6 Export

Contents: final sheet, check C, export layout, print variants, wrap-up

## Final sheet

`run.py --from S6` builds `qc/sheet.jpg` and `qc/sheet.md` from the passed files in `out/` (`scripts/sheet.py`, `sheet_cols` in `spec.json`, default 6). The sheet has no text; `qc/sheet.md` lists row, column, file. Ids that ended `exhausted` are in `qc/failed.md`. The user sees the sheet and the list, not every file.

## Check C (human)

Show the sheet and counts: planned, passed, exhausted. The user may name ids to drop or redo; redo means editing the concept in `spec.json` and running S3 to S5 for those ids. Approve with `--approve C`.

## Export layout

```text
export/
  <name>_<id>.png   passed stickers, 300 dpi tag, no resampling
  DELIVERY.md       pixel size and 300 dpi print size per sticker
```

`<name>` is `name` from `spec.json`.

## Print variants

Only on request. Follow `print-guide.md`: white border, die-cut path, size at 300 dpi from actual pixel size. State the real printable size per sticker; do not upscale to claim a larger size.

## Wrap-up

- Run `python3 scripts/run.py <project> --cleanup` to delete this run's thread rollouts and empty image folders (`scripts/cleanup.py <project> --dry-run` shows what would go).
- Keep `manifest.jsonl` and `spec.json`.
- Report: counts, folder path, exhausted ids.
