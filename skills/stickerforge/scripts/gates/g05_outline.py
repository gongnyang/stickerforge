#!/usr/bin/env python3
"""g05 흰 다이컷 테두리 연속성.

스티커 바깥 윤곽 안쪽 띠(기본 6px)가 계속 흰색이어야 한다. 윤곽을 따라
흰색이 끊긴 곳(캐릭터 색이 바깥 경계까지 닿음)이 있으면 실패한다.
속도를 위해 짧은 변 400px 안팎으로 줄여서 본다.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_rgba, res, run, safe  # noqa

N4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def shift(m, dy, dx, fill=False):
    out = np.full_like(m, fill)
    h, w = m.shape
    ys, yd = (slice(dy, h), slice(0, h - dy)) if dy >= 0 else (slice(0, h + dy), slice(-dy, h))
    xs, xd = (slice(dx, w), slice(0, w - dx)) if dx >= 0 else (slice(0, w + dx), slice(-dx, w))
    out[ys, xs] = m[yd, xd]
    return out


def dilate(m, fill=False):
    o = m.copy()
    for dy, dx in N4:
        o |= shift(m, dy, dx, fill)
    return o


def erode(m, n):
    for _ in range(n):
        o = m.copy()
        for dy, dx in N4:
            o &= shift(m, dy, dx, False)
        m = o
    return m


def exterior(m):
    """m이 아닌 픽셀 중 가장자리와 이어진 것(바깥 배경)."""
    free = ~m
    ext = np.zeros_like(m)
    ext[0, :] = free[0, :]
    ext[-1, :] = free[-1, :]
    ext[:, 0] |= free[:, 0]
    ext[:, -1] |= free[:, -1]
    for _ in range(max(m.shape) * 4):
        nxt = dilate(ext) & free
        if (nxt == ext).all():
            break
        ext = nxt
    return ext


def analyze(rgba, band_px=6, white_min=215, target=400, sat_max=40):
    h, w = rgba.shape[:2]
    s = max(1, min(h, w) // target)
    if s > 1:
        hh, ww = h // s, w // s
        r = rgba[:hh * s, :ww * s].reshape(hh, s, ww, s, 4).astype(np.float32)
        a = r[..., 3].max(axis=(1, 3))
        rgb = (r[..., :3] * (r[..., 3:4] + 1)).sum(axis=(1, 3)) / ((r[..., 3:4] + 1).sum(axis=(1, 3)))
    else:
        a = rgba[..., 3].astype(np.float32)
        rgb = rgba[..., :3].astype(np.float32)
    m = a > 200
    band = max(2, int(round(band_px / s)))
    ext = exterior(m)
    edge = m & dilate(ext)  # 바깥과 맞닿은 내용 픽셀
    inner = m & ~erode(m, band)  # 윤곽 안쪽 띠
    # 바깥 윤곽에서 band 거리 안의 띠: 외부와 이어진 가장자리에서 band만큼 확장
    reach = edge.copy()
    skip = edge.copy()  # 가장자리 안티앨리어싱 1px는 제외
    for _ in range(band + 1):
        reach = dilate(reach) & m
    ring = reach & ~skip & inner
    n_ring = int(ring.sum())
    if n_ring == 0:
        return None
    white = (rgb.min(axis=2) >= white_min) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= sat_max)
    bad = ring & ~white
    # 1~2 스케일 px짜리 잡티는 무시: 침식 후 남는 덩어리만 끊김으로 본다
    gap = erode(bad, 1)
    return n_ring, int(bad.sum()), int(gap.sum()), s


@safe
def one(folder, f, band, white_min, max_bad, max_gap):
    im, a, ok = load_rgba(os.path.join(folder, f))
    if not ok:
        return res(f, False, "NO_ALPHA", "알파 없음, 테두리 판단 불가")
    r = analyze(a, band, white_min)
    if r is None:
        return res(f, False, "EMPTY", "내용 없음")
    n, bad, gap, s = r
    frac = bad / n
    d = f"테두리 띠 비흰색 {frac * 100:.1f}%, 끊김 픽셀 {gap}"
    if frac > max_bad or gap > max_gap:
        return res(f, False, "OUTLINE_BROKEN", d)
    return res(f, True, "OK", d)


def check(folder, files, a):
    return [one(folder, f, a.band, a.white_min, a.max_bad, a.max_gap) for f in files]


if __name__ == "__main__":
    run("outline", check, extra_args={
        "--band": {"type": int, "default": 6, "help": "윤곽 안쪽 검사 띠 두께 px"},
        "--white-min": {"type": int, "default": 215, "help": "흰색으로 보는 최소 채널값"},
        "--max-bad": {"type": float, "default": 0.03, "help": "띠에서 비흰색 허용 비율"},
        "--max-gap": {"type": int, "default": 0, "help": "허용 끊김 픽셀 수(축소 기준)"}})
