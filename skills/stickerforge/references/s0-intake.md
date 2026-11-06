# S0 Intake and style lock

Contents: inputs, questions, real people policy, style choice, spec, check A

## Inputs to collect

| Field | Rule |
|---|---|
| Reference image | One original character image. Keep the file path. If the user has several, pick one master. |
| Count | Target number of final stickers. Plan 20 to 30 percent extra concepts for rejects. |
| Use | Print, messenger emoji, or both. Print needs the checks in `print-guide.md`. |
| Style | One preset from `../styles/`. Default `original-match`. |
| Text on stickers | Allowed words list, or none. Short words only. Language of the words. |
| Banned content | Topics the user does not want. Brands and logos are always banned. |
| Runtime | Output of `scripts/doctor.py` (or `run.py <project> --doctor`). See `providers.md`. |

Ask only for what is missing. One round of questions, not an interview.

## Real people and public figures

- A real person's likeness is used only when that person (or the user, for themselves) gives consent. Ask once and keep the answer in the project notes.
- No sticker mocks, insults, or sexualizes a real person. Public figures are not a subject for ridicule.
- Do not add a real person's name as a text on a sticker.
- If a reference photo shows a real person, ask whether it is the user. If not, ask for consent evidence or stop.
- Do not replicate a specific existing comic, game, or studio style. Use a preset or describe shapes, line, and palette in neutral terms.

## Style choice

Show the six presets by name with one line each. Let the user pick one. For a custom look, write a short style block by copying the structure of a preset file. Lock it: line weight, palette, shading, outline, background rule. The style block is pasted into every prompt unchanged.

## Spec

Write `spec.json` in the project folder from `../templates/spec.example.json`; the schema is `../schemas/spec.schema.json`. Required: `name`, `ref` (original image, path relative to the project), `style` (the locked style text), `concepts`. Optional: `character`, `transparent`, `min_px`, `provider`, `parallel` (default 8, cap 10), `trial`, `codex`, `gates`. Record consent for real-person likeness in a project note; the runner does not read it.

## Check A (human)

Show: chosen style block, count, provider, expected time and quota use. Ask for approval, then run `run.py <project> --approve A`. Do nothing expensive before approval.

Next: `s1-concepts.md`.
