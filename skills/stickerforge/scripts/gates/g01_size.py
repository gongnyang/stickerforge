#!/usr/bin/env python3
"""g01 크기: 픽셀 크기와 300dpi 인쇄 가능 크기(cm)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import res, run, safe  # noqa
from PIL import Image  # noqa

DPI = 300


@safe
def one(folder, f, min_px, max_ratio):
    with Image.open(os.path.join(folder, f)) as im:
        w, h = im.size
    cm_w, cm_h = w / DPI * 2.54, h / DPI * 2.54
    d = f"{w}x{h}px, 300dpi {cm_w:.1f}x{cm_h:.1f}cm"
    if min(w, h) < min_px:
        return res(f, False, "TOO_SMALL", f"짧은 변 {min(w, h)}px < {min_px}px. {d}")
    if max(w, h) / min(w, h) > max_ratio:
        return res(f, False, "BAD_RATIO", f"가로세로 비율 {max(w, h) / min(w, h):.1f} > {max_ratio}. {d}")
    return res(f, True, "OK", d)


def check(folder, files, a):
    return [one(folder, f, a.min_px, a.max_ratio) for f in files]


if __name__ == "__main__":
    run("size", check, extra_args={
        "--min-px": {"type": int, "default": 1000, "help": "짧은 변 최소 px"},
        "--max-ratio": {"type": float, "default": 3.0, "help": "긴 변/짧은 변 상한"}})
