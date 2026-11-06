#!/usr/bin/env python3
"""README 이미지 합성. 글자는 넣지 않는다. 사용: make_assets.py <전체 폴더> <그림체시안 폴더> <출력 폴더>"""
import sys
from pathlib import Path
from PIL import Image

BG = (246, 243, 236)
HERO = ["g01_한도소진", "g05_워커스폰", "g09_커밋완료", "g14_키보드낮잠", "g17_야근", "g22_확인",
        "m001_프롬프트다듬기", "m010_서브에이전트회수", "m017_터미널탭40개", "m027_프롬프트인젝션", "m041_식빵자세", "m045_야옹회의",
        "m052_여름수박", "m054_겨울귤이불", "m058_붕어빵한입", "m065_비오는날우산", "m071_새벽우다다", "m081_네",
        "m088_대박", "m093_화이팅", "m096_일단커밋", "m106_슬픔", "m113_박수", "m115_엄지척"]

def fit(img, box):
    bb = img.getchannel("A").getbbox()
    if bb: img = img.crop(bb)
    s = min(box / img.width, box / img.height)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)

def grid(paths, cols, cell, pad, out, max_kb=500):
    rows = -(-len(paths) // cols)
    W, H = cols * cell + (cols + 1) * pad, rows * cell + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), BG)
    for i, p in enumerate(paths):
        im = fit(Image.open(p).convert("RGBA"), cell - 24)
        x = pad + (i % cols) * (cell + pad) + (cell - im.width) // 2
        y = pad + (i // cols) * (cell + pad) + (cell - im.height) // 2
        sheet.paste(im, (x, y), im)
    q = 90
    while True:
        sheet.save(out, "JPEG", quality=q, optimize=True)
        if out.stat().st_size <= max_kb * 1000 or q <= 60: break
        q -= 5
    print(out, sheet.size, out.stat().st_size // 1000, "KB q", q)

def main():
    full, alt, dst = map(Path, sys.argv[1:4])
    grid([full / f"{n}.png" for n in HERO], 6, 312, 16, dst / "hero-sheet.jpg")
    names = ["g05_워커스폰", "g14_키보드낮잠"]
    rows = []
    for n in names:
        rows += [full / f"{n}.png", alt / f"터미널_{n}.png", alt / f"흑백_{n}.png"]
    grid(rows, 3, 480, 16, dst / "style-compare.jpg")

main()
