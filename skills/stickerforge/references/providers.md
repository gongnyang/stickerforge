# Providers and runtime matrix

Contents: detection, matrix, Codex path, API paths, unsupported handling

## Detection

`scripts/doctor.py` checks, without printing secrets:
1. `codex` on PATH and login status.
2. `OPENAI_API_KEY` set or not (presence only).
3. `GEMINI_API_KEY` set or not (presence only).
4. Pillow and numpy importable.
Usage: `doctor.py [--provider auto|codex|openai|gemini] [--json]`, or `run.py <project> --doctor`. Exit 0 means a provider can generate; exit 2 means unsupported, with the reason printed. Auto order: codex, openai, gemini. A provider named in `spec.json` that is unusable ends with exit 2; it is never swapped.

## Matrix

| Environment | Generate | Transparency | Size control | Parallel |
|---|---|---|---|---|
| Codex only (ChatGPT login) | Built-in image tool | Tool argument, gate the alpha | None, about 1254 to 1536 px | Sequential mode (`--next`, `--ingest`), or `codex exec` pool |
| Claude Code with Codex | Runner spawns `codex exec` | Same | None | Pool of 8 (`parallel`), cap 10 |
| Claude Code with `OPENAI_API_KEY` | Image API | Native only on older image models; otherwise chroma background plus removal | Yes (`openai.size`) | Script pool; untested, see `scripts/providers/PROVIDER_STATUS.md` |
| Claude Code with `GEMINI_API_KEY` | Image API | Post-processing | Model default | Script pool; untested, see `scripts/providers/PROVIDER_STATUS.md` |
| Claude Code only | None | none | none | none |

Models and limits change. Treat this table as a starting point and let the 1-sticker smoke test decide.

## Codex path

- Front model: gpt-6.1-terra at medium effort. Pass the stickerforge prompt verbatim.
- Image tool arguments seen in practice: prompt, referenced image paths, `transparent_background`. No size or output path. Settings: `codex.model`, `codex.effort`, `codex.timeout` in `spec.json`.
- Output lands in the thread's session folder under `~/.codex/generated_images/`. Find it from the `thread_id` in `codex exec --json` output.
- A nested `codex exec` needs full permission; with workspace-write it fails read-only. The outer session must run with `--dangerously-bypass-approvals-and-sandbox`.
- Detached run measured once: the outer `codex exec` started `setsid nohup python3 scripts/run.py <project> --yes > runner.log 2>&1 < /dev/null &` and polled `runner.log` and `run.py <project> --status` every 20 seconds. Three stickers finished in 3 min 18 s.
- Survival after the outer turn ends is not confirmed. In an earlier test the inner threads vanished without images when the outer turn ended after 10 seconds, and plain `nohup` did not help. The outer agent must keep waiting until the runner exits; do not end the turn after launching it.
- `--yes` approves checks A, B and C at once. To keep the human checks, leave it out; `run.py` exits 3 at each check, ask the user, then continue with `--approve A|B|C`.
- If the environment cannot wait or detach, use sequential mode in `s3-generate.md`: the outer agent calls its own image tool per sticker. Verified with stand-in PNGs; a full run with real image calls was not done.
- Subscription limits are shared with text work and count per account.

## API paths

- Use a script provider; model tokens are not needed for generation.
- Ask for the model by name in `spec.json`. If the chosen model lacks real alpha, say so before the run and use the chroma path.
- Never switch model silently. Ask the user.

## Unsupported handling

| Case | Behavior |
|---|---|
| No Codex, no key | Stop. Print the two fixes: log in to Codex, or set a key. |
| Transparency not available and chroma path fails the gate | Stop for that sticker; report. No opaque output labelled transparent. |
| Size below minimum | Reject, no upscaling. |
| Parallel not possible (permission) | Run sequentially, or ask for permission change. State the slower time. |

Smoke test: generate one sticker with the real settings, run gates, then proceed.
