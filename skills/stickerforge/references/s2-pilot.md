# S2 Pilot

Contents: purpose, run, review, check B

## Purpose

Find style, transparency and text problems on a few stickers before spending quota on hundreds.

## Run

`run.py` generates `pilot_count` trial stickers (default 6; capped at the number of concepts), each a different concept. The concept named by `trial` in `spec.json` is always included; the rest are spread evenly across the concept list, so order the list to put the hard cases (a prop, hands, text, an extreme expression, a small detail, a wide pose) at different places. Set `pilot_count` to 1 for a single-sticker check. Same provider and settings as the batch.

Resume: a trial file already generated or passed is not made again. Only missing ones are generated, then the run stops at check B. Trial files stay in `out/` and count as part of S3.

Then run the gates from `s4-gates.md` on the trial files and look at them once. `scripts/sheet.py <pngFolder>` builds an unlabeled sheet; its `--md` order file maps row and column to file.

## Review

Check: character matches the reference, style respected, no checkerboard, edges clean on a dark background, text correct, pose matches the concept. Write findings as a short list.

## Check B (human)

Show the file or sheet and the findings. Choices: approve with `--approve B`; change `style` or the prompt and rerun S2; stop. Do not start S3 without approval. A changed `style` needs a new pilot.

Next: `s3-generate.md`.
