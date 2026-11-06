# Concept lines example

Draft concepts as lines while planning, then copy them into `spec.json` as `concepts` entries (`id`, `title`, `prompt`).

Format: `id | category | situation | pose or expression | text`

```text
w001 | work   | waiting for a long build   | sitting with chin on hands, half-closed eyes | none
w002 | work   | sending a file at the last minute | one paw pressing a big button, wide eyes | none
w003 | work   | a meeting that could be a message | slumped on a chair, flat mouth | none
d001 | daily  | first coffee               | both paws around a mug, eyes closed, smile | none
d002 | daily  | rain without umbrella      | wet fur, tiny cloud above head | none
r001 | react  | thanks                     | small bow, closed happy eyes | thanks
r002 | react  | sorry                      | hands together, worried brows | sorry
r003 | react  | on it                      | one paw raised, determined face | on it
m001 | mix    | holding a small plant      | proud look, plant in both paws | none
m002 | mix    | riding a toy train         | leaning out, ears blowing back | none
```

The matching `spec.json` entry for `w001`:

```json
{ "id": "w001", "title": "waiting for a long build", "prompt": "Sitting with chin on hands, half-closed eyes." }
```

Duplicate example to drop: `w004 | work | waiting for build | sitting, chin on hands | none` repeats w001.
