# S3 Generate

Contents: prompt build, provider paths, concurrency, collection, cleanup, ledger, sequential mode

## Prompt build

`run.py` composes each prompt as: `style` + `character` (match the attached reference) + the concept `prompt` (pose and situation) + a fixed sticker rule. The rule asks for one centered subject, clean bold outline, the whole sticker including its white border inside the canvas with at least 6% empty margin on every side, and no text unless the pose line asks for specific text. The transparency flag is added by the provider. Write concept prompts as pose and situation only.

## Provider paths

| Path | How |
|---|---|
| Codex | One `codex exec --json` per sticker, front model gpt-6.1-terra at medium effort, prompt passed verbatim, original reference attached with `-i`. |
| OpenAI key | API script, one call per sticker. Chroma background and removal, then the alpha gate. |
| Gemini key | API script. Same post-processing. |

Details and unsupported cases: `providers.md`.

## Concurrency

`parallel` in `spec.json`, default 8, hard cap 10. A pool starts the next job when one ends. Quota, 401, 403 or 429 stops the pool (exit 6); finished files stay, rerun the same command to resume.

## Collection (Codex path)

The runner reads `thread_id` from the JSON events of each run and moves the PNG from `~/.codex/generated_images/<thread_id>/` to `out/<id>.png`, then cleans alpha. Never collect by modification time; parallel runs mix files.

## Cleanup

`run.py <project> --cleanup` (or `scripts/cleanup.py <project> [--dry-run]`) deletes only threads listed in `manifest.jsonl`: the rollout under `~/.codex/sessions` (about 10 MB each) and its empty image folder.

## Ledger

`manifest.jsonl` gets one row per event: `ts, id, stage, status`, plus attempt, provider, thread_id, path, note, error. Statuses: `generated`, `gen_failed`, `gate_failed`, `passed`, `exhausted`. Ids starting with `_` are stage and approval markers. Last row per id wins. A restart skips ids that already have `out/<id>.png`. `run.py <project> --status` prints the table.

## Sequential mode (no detached runner)

For Codex-only sessions where the outer turn cannot wait on a detached runner. The outer agent calls its own image tool once per sticker:

```text
run.py <project> --next                         JSON: id, prompt, refs, transparent_background
(pass the prompt verbatim to the image tool with the refs attached)
run.py <project> --ingest <id> --file <png> [--thread-id T]
repeat until --next prints done:true, then run.py <project> --from S4 --yes
```

No parallelism. A gate-failed sticker has its file moved to `qc/rejected/`, so `--next` offers it again. Details: `providers.md`.

## Not allowed

- Using a generated sticker as reference for the next.
- Adding or fixing text after generation.
- Dropping the model to a lighter one when slow.

Next: `s4-gates.md`.
