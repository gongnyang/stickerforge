# S1 Concepts and duplicate check

Contents: concept line format, categories, writing rules, duplicate check, output

## Concept line

One line per sticker: `id | category | situation | pose or expression | text (or none)`. See `../templates/concept-lines.example.md`.

## Categories that work in practice

| Category | What it covers | Example situation |
|---|---|---|
| Work feelings | Small moments of a work day | waiting on a build, a meeting that could be a message, sending a file one minute before deadline |
| Daily life | Ordinary routines | first coffee, missing the bus, rain without umbrella |
| Reactions | Short replies used in chat | thanks, sorry, on it, no, okay, wait a moment |
| Subject mix | Character combined with an object or theme | the character holding a plant, riding a toy train, wearing a seasonal hat |

Aim for a spread: for 100 stickers, about 30 work feelings, 25 daily life, 30 reactions, 15 subject mix. Adjust to the user's use case.

## Writing rules

- One situation per sticker. If two ideas are needed, make two stickers.
- Name a concrete pose and a facial expression. Avoid abstract words like mood or vibe.
- Text is optional and short: one to three words. Set `text` to none for most.
- No brand, logo, real person, or trademarked character.
- Keep the character design fixed. Only pose, expression, and props change.
- Props must be simple shapes. Complex scenes make clutter at sticker size.

## Duplicate check

1. Normalize each line: lowercase, remove stop words, sort remaining words.
2. Compare every concept to the full list (all against all), not to the last few.
3. Drop or rewrite a concept when it shares the same situation and pose with another, or when the text is identical.
4. Compare also against concepts of earlier packs in the same project folder if `concepts/` has them.
5. Write the kept list and the dropped list with reason, then put the kept ones into `spec.json` as `concepts`.

`run.py` S1 also checks every pair of concepts (title plus prompt word overlap, threshold `dup_threshold`, default 0.8) and stops with exit 4 when a pair is too close. It is a floor, not a replacement for the steps above.

Variation inside one situation is fine when pose and expression differ clearly (for example happy thanks and tired thanks).

## Output

`concepts` in `spec.json` (and optionally `concepts.md` and `concepts-dropped.md` for your notes). Proceed to `s2-pilot.md`.
