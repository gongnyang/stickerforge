#!/usr/bin/env python3
"""g02 알파: 알파 채널 유무, 네 모서리 투명."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_rgba, res, run, safe  # noqa


@safe
def one(folder, f, corner, thr):
    im, a, ok = load_rgba(os.path.join(folder, f))
    if not ok:
        return res(f, False, "NO_ALPHA", f"알파 채널 없음(mode={im.mode})")
    al = a[:, :, 3]
    if al.min() > thr:
        return res(f, False, "ALL_OPAQUE", f"투명 픽셀이 하나도 없음(최소 알파 {int(al.min())})")
    c = min(corner, al.shape[0] // 2, al.shape[1] // 2)
    patches = {"좌상": al[:c, :c], "우상": al[:c, -c:], "좌하": al[-c:, :c], "우하": al[-c:, -c:]}
    bad = [k for k, p in patches.items() if p.max() > thr]
    if bad:
        return res(f, False, "CORNER_OPAQUE", f"모서리 불투명: {','.join(bad)}")
    return res(f, True, "OK", "알파 있음, 네 모서리 투명")


def check(folder, files, a):
    return [one(folder, f, a.corner, a.thr) for f in files]


if __name__ == "__main__":
    run("alpha", check, extra_args={
        "--corner": {"type": int, "default": 8, "help": "모서리 검사 한 변 px"},
        "--thr": {"type": int, "default": 12, "help": "투명으로 보는 알파 상한"}})
