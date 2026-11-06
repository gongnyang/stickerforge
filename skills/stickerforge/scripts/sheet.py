#!/usr/bin/env python3
"""글자 없는 격자 시트(JPG)와 순서 md 를 만든다. 시트에는 번호도 이름도 그리지 않는다.
사용: sheet.py <pngFolder> [--cols 6] [--out 시트.jpg] [--md 순서.md] [--titles spec.json]
순서 md 는 'N행 M열: 파일' 로 적는다(--titles 를 주면 컨셉 제목도)."""
import json, sys
from pathlib import Path
from PIL import Image


def make(folder, cols=6, out=None, md=None, titles=None, cell=430):
    d = Path(folder)
    fs = sorted(f for f in d.glob("*.png") if not f.name.startswith("_"))
    if not fs:
        return 0
    rows = (len(fs) + cols - 1) // cols
    s = Image.new("RGB", (cols * cell, rows * cell), (226, 226, 226))
    for i, f in enumerate(fs):
        im = Image.open(f).convert("RGBA"); im.thumbnail((cell - 16, cell - 16))
        s.paste(im, ((i % cols) * cell + (cell - im.width) // 2, (i // cols) * cell + (cell - im.height) // 2), im)
    s.thumbnail((2600, 2600))
    out = Path(out or d / "_sheet.jpg"); out.parent.mkdir(parents=True, exist_ok=True)
    s.save(out, quality=85)
    tm = {}
    if titles:
        tm = {c["id"]: c.get("title", "") for c in json.loads(Path(titles).read_text(encoding="utf-8")).get("concepts", [])}
    lines = [f"{i//cols+1}행 {i%cols+1}열: {f.name}" + (f" {tm[f.stem]}" if f.stem in tm else "") for i, f in enumerate(fs)]
    Path(md or out.with_suffix(".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(fs)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    g = lambda k, dflt=None: a[a.index(k) + 1] if k in a else dflt
    print(make(a[0], int(g("--cols", 6)), g("--out"), g("--md"), g("--titles")))
