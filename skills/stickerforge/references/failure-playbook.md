# Failure playbook

Contents: refusal, quota, garbled text, checkerboard, quality drop, nested Codex, other

Rule for all rows: stop on repeated failure, record the reason in the manifest, never hide it behind a silent fallback.

## Refusal (moderation)

| Sign | Action |
|---|---|
| Tool replies it cannot create the image, or returns no image | Log reason `refusal`. Rewrite the situation in neutral words and remove sensitive props. One retry. |
| Same concept refused twice | Leave it `exhausted` (see `s5-retry.md`). Offer a replacement concept. |
| Refusal on the reference itself | Stop. Ask the user for another reference. Do not try to bypass. |
| Real person likeness refused | Confirm consent per `s0-intake.md`; otherwise change to an original character. |

## Quota and rate limits

| Sign | Action |
|---|---|
| 429, usage limit, session invalidated | Stop the pool at once. Save remaining ids as pending. Report the count done and left. Do not retry in a loop. |
| Many failures right after start | Lower concurrency to 4 and run one job to test before resuming. |
| Account limit is per account | Raising concurrency does not raise quota. |

## Garbled or wrong text

- Shorten to one or two words, or no text.
- Use common words; avoid long or mixed-script strings.
- Regenerate. Overlaying text afterwards is not allowed.
- If a language repeatedly fails, switch that sticker to a text-free concept.

## Checkerboard (fake transparency)

The model draws a gray and white grid as pixels instead of real alpha.

- The gate rejects it. Do not clean it by color keying.
- Edit the concept prompt as in `s5-retry.md`, then run S5.
- If the provider has no true alpha (OpenAI image-2 path, Gemini), use the chroma background path and removal; gate the result for halos.
- If most of a batch has it, stop and rerun the pilot (S2) with the changed prompt.

## Quality drop mid-batch

| Sign | Action |
|---|---|
| Character drifts from the reference | Check that every call still uses the original reference and the same style block. Check the model is still the pinned one. |
| Style looks different from the pilot | A lighter model or changed prompt crept in. Restore and regenerate the affected ids. |
| Many near-duplicates | Return to S1 and rewrite concepts. |

## Nested Codex runs fail

- Workspace-write permission: the inner `codex exec` fails with a read-only file system. Use full permission or generate directly with the built-in tool, one sticker per call.
- The outer turn ends before inner runs finish: launch the runner detached and keep the outer turn waiting until it exits. Survival after the turn ends is not confirmed. Details and the sequential fallback in `providers.md`.

## Other

| Sign | Action |
|---|---|
| Image folder missing for a thread | Wait a few seconds, check once more, then count it as transport error. Never grab the newest folder. |
| Disk filling | Rollouts are about 10 MB each; delete finished threads' rollouts only. |
| Output smaller than minimum size | Reject (`TOO_SMALL`). Do not upscale. |
