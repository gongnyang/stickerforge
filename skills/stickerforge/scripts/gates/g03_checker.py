#!/usr/bin/env python3
"""g03 체크무늬 가짜 투명 탐지.

모델이 투명 배경 대신 회색/흰색 체크무늬를 그려 넣은 경우를 잡는다.
알파가 있어도(불투명 체크무늬) 알파가 없어도 검사한다.
네 모서리 패치마다 (1) 밝기가 두 값으로 나뉘고 (2) 한 타일 옮기면 반전,
두 타일 옮기면 동일 (3) 세로로도 같은 규칙인지 본다. 2개 이상 모서리가 맞으면 실패.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_rgba, res, run, safe  # noqa


def _runs(b):
    """각 행의 같은 값 연속 구간 길이들."""
    out = []
    for row in b:
        idx = np.flatnonzero(np.diff(row.astype(np.int8))) + 1
        edges = np.concatenate(([0], idx, [len(row)]))
        out.extend(np.diff(edges)[1:-1].tolist())  # 양 끝 조각은 잘려 있으므로 제외
    return out


def patch_is_checker(g, min_contrast=6.0):
    """g: 2D 밝기(float). 체크무늬 타일 크기를 돌려주고 아니면 0."""
    lo, hi = float(g.min()), float(g.max())
    for _ in range(8):  # 2-means
        mid = (lo + hi) / 2
        m = g > mid
        if m.all() or (~m).all():
            return 0
        lo, hi = float(g[~m].mean()), float(g[m].mean())
    if hi - lo < min_contrast:
        return 0
    b = g > (lo + hi) / 2
    frac = b.mean()
    if frac < 0.25 or frac > 0.75:
        return 0
    runs = [r for r in _runs(b) if r >= 4]
    if len(runs) < 6:
        return 0
    t = int(np.median(runs))
    if t < 6 or t > g.shape[1] // 3:
        return 0
    h, w = b.shape
    if h < 2 * t + 1 or w < 3 * t:
        return 0
    flip_x = (b[:, :-t] != b[:, t:]).mean()
    same_x = (b[:, :-2 * t] == b[:, 2 * t:]).mean()
    flip_y = (b[:-t, :] != b[t:, :]).mean()
    same_y = (b[:-2 * t, :] == b[2 * t:, :]).mean()
    # 타일 크기 추정이 한두 px 어긋나도 통과하도록 t-1..t+1 중 최고를 쓴다
    best = 0
    for dt in (-1, 0, 1):
        tt = t + dt
        if tt < 4 or h < 2 * tt + 1 or w < 3 * tt:
            continue
        fx = (b[:, :-tt] != b[:, tt:]).mean()
        sx = (b[:, :-2 * tt] == b[:, 2 * tt:]).mean()
        fy = (b[:-tt, :] != b[tt:, :]).mean()
        sy = (b[:-2 * tt, :] == b[2 * tt:, :]).mean()
        best = max(best, min(fx, sx, fy, sy))
    return t if best >= 0.9 else 0


@safe
def one(folder, f, patch, need):
    im, a, ok = load_rgba(os.path.join(folder, f))
    p = min(patch, a.shape[0] // 2, a.shape[1] // 2)
    corners = {"좌상": a[:p, :p], "우상": a[:p, -p:], "좌하": a[-p:, :p], "우하": a[-p:, -p:]}
    hits, tiles = [], []
    for k, c in corners.items():
        if (c[:, :, 3] >= 250).mean() < 0.9:  # 진짜 투명이면 체크무늬 아님
            continue
        g = c[:, :, :3].astype(float).mean(axis=2)
        t = patch_is_checker(g)
        if t:
            hits.append(k)
            tiles.append(t)
    if len(hits) >= need:
        return res(f, False, "FAKE_CHECKER",
                   f"체크무늬 배경 의심: 모서리 {','.join(hits)}, 타일 약 {int(np.median(tiles))}px")
    return res(f, True, "OK", "체크무늬 없음")


def check(folder, files, a):
    return [one(folder, f, a.patch, a.need) for f in files]


if __name__ == "__main__":
    run("checker", check, extra_args={
        "--patch": {"type": int, "default": 128, "help": "모서리 패치 한 변 px"},
        "--need": {"type": int, "default": 2, "help": "실패로 보는 최소 모서리 수"}})
