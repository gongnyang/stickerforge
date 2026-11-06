#!/usr/bin/env python3
"""g04 여백: 내용(알파>12)이 캔버스 가장자리에 닿거나 여백이 부족하면 실패(칼선 위험)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_rgba, res, run, safe  # noqa


@safe
def one(folder, f, margin, thr):
    im, a, ok = load_rgba(os.path.join(folder, f))
    if not ok:
        return res(f, False, "NO_ALPHA", "알파 없음, 여백 판단 불가")
    m = a[:, :, 3] > thr
    if not m.any():
        return res(f, False, "EMPTY", "내용 없음")
    ys, xs = np.where(m)
    h, w = m.shape
    gaps = {"위": int(ys.min()), "아래": int(h - 1 - ys.max()),
            "왼": int(xs.min()), "오른": int(w - 1 - xs.max())}
    worst = min(gaps.values())
    d = "여백 " + ", ".join(f"{k} {v}px" for k, v in gaps.items())
    if worst <= 1:
        return res(f, False, "TOUCHES_EDGE", f"내용이 가장자리에 닿음. {d}")
    if worst < margin:
        return res(f, False, "LOW_MARGIN", f"여백 {worst}px < {margin}px. {d}")
    return res(f, True, "OK", d)


def check(folder, files, a):
    return [one(folder, f, a.margin, a.thr) for f in files]


if __name__ == "__main__":
    run("margin", check, extra_args={
        "--margin": {"type": int, "default": 8, "help": "최소 여백 px"},
        "--thr": {"type": int, "default": 12, "help": "내용으로 보는 알파 하한"}})
