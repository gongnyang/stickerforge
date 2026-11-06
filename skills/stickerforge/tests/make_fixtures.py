#!/usr/bin/env python3
"""게이트 시험용 합성 이미지를 만든다. 이미지는 레포에 두지 않고 실행 때마다 새로 생성한다.

사용: python3 make_fixtures.py <출력폴더>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

SZ = 1280
SS = 2  # 슈퍼샘플링으로 가장자리를 부드럽게


def _mask(draw_fn, size=SZ):
    m = Image.new("L", (size * SS, size * SS), 0)
    draw_fn(ImageDraw.Draw(m), SS)
    return m.resize((size, size), Image.LANCZOS)


def sticker(kind="ellipse", color=(70, 120, 220), offset=(0, 0), broken=False, size=SZ):
    """흰 테두리가 있는 스티커. 투명 배경 RGBA."""
    cx, cy = size // 2 + offset[0], size // 2 + offset[1]
    r = size * 0.30

    def shape(d, s, grow=0.0):
        rr = (r + grow) * s
        if kind == "ellipse":
            d.ellipse([cx * s - rr, cy * s - rr * 0.85, cx * s + rr, cy * s + rr * 0.85], fill=255)
        elif kind == "rect":
            d.rounded_rectangle([cx * s - rr, cy * s - rr * 0.7, cx * s + rr, cy * s + rr * 0.7],
                                radius=60 * s, fill=255)
        else:  # tri
            d.polygon([(cx * s, cy * s - rr), (cx * s + rr, cy * s + rr * 0.8),
                       (cx * s - rr, cy * s + rr * 0.8)], fill=255)

    outer = _mask(lambda d, s: shape(d, s, 22), size)
    inner = _mask(lambda d, s: shape(d, s, 0), size)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    white = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    img.paste(white, mask=outer)
    col = Image.new("RGBA", (size, size), color + (255,))
    img.paste(col, mask=inner)
    # 눈 두 개로 그림에 구조를 준다
    d = ImageDraw.Draw(img)
    for dx, rad in ((-0.12, 22), (0.07, 34)):
        x, y = cx + dx * size, cy - 0.04 * size
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(20, 20, 20, 255))
    d.line([cx - 0.15 * size, cy + 0.10 * size, cx + 0.02 * size, cy + 0.14 * size], fill=(20, 20, 20, 255), width=14)
    if broken:
        # 오른쪽 윤곽 위로 색이 흰 테두리를 덮고 바깥 경계까지 나간다
        bx = cx + r + 22
        patch = _mask(lambda d, s: d.ellipse([(bx - 50) * s, (cy - 70) * s, (bx + 8) * s, (cy + 70) * s], fill=255), size)
        img.paste(col, mask=patch)
    return img


def checker_bg(size=SZ, tile=20, a=253, b=222):
    yy, xx = np.mgrid[0:size, 0:size]
    v = np.where(((yy // tile) + (xx // tile)) % 2 == 0, a, b).astype(np.uint8)
    return Image.fromarray(np.stack([v, v, v], axis=2), "RGB")


def build(out):
    os.makedirs(out, exist_ok=True)
    good_a = sticker("ellipse", (70, 120, 220))
    good_b = sticker("rect", (220, 90, 90))
    good_c = sticker("tri", (60, 170, 90))
    good_a.save(os.path.join(out, "good_a.png"))
    good_b.save(os.path.join(out, "good_b.png"))
    good_c.save(os.path.join(out, "good_c.png"))

    # 체크무늬 가짜 투명: 알파 없음(RGB)과 알파 있으나 전부 불투명(RGBA) 두 종류
    bg = checker_bg().convert("RGBA")
    bg.alpha_composite(sticker("ellipse", (200, 140, 40)))
    bg.convert("RGB").save(os.path.join(out, "bad_checker_rgb.png"))
    bg.save(os.path.join(out, "bad_checker_rgba.png"))

    # 잘림: 내용이 오른쪽 가장자리를 넘어감
    sticker("ellipse", (150, 80, 200), offset=(int(SZ * 0.32), 0)).save(os.path.join(out, "bad_cropped.png"))

    # 알파 없음: 흰 배경 RGB
    flat = Image.new("RGB", (SZ, SZ), (255, 255, 255))
    flat.paste(sticker("rect", (40, 150, 150)).convert("RGB"), mask=sticker("rect", (40, 150, 150)).split()[3])
    flat.save(os.path.join(out, "bad_noalpha.png"))

    # 중복: good_a에 아주 작은 잡음만 얹음
    arr = np.array(good_a).astype(int)
    rng = np.random.default_rng(1)
    arr[:, :, :3] = np.clip(arr[:, :, :3] + rng.integers(-3, 4, arr[:, :, :3].shape), 0, 255)
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(os.path.join(out, "z_bad_dup_of_a.png"))

    # 테두리 끊김
    sticker("tri", (230, 170, 30), broken=True).save(os.path.join(out, "bad_outline_broken.png"))

    # 너무 작음
    sticker("ellipse", (90, 90, 90), size=480).save(os.path.join(out, "bad_small.png"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("사용: make_fixtures.py <출력폴더>")
    build(sys.argv[1])
    print("ok")
