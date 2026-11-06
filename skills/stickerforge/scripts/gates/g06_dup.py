#!/usr/bin/env python3
"""g06 이미지 중복: pHash(내용 영역 64x64 DCT 저주파 16x16) 해밍 거리로 거른다.

파일명 순서상 먼저 나온 것을 남기고, 뒤에 나온 중복본을 실패로 표시한다.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import res, run  # noqa

N = 64  # 줄이는 크기
K = 16  # 쓰는 저주파 계수 한 변(256비트)


def _dct_matrix(n):
    k = np.arange(n)[:, None]
    i = np.arange(n)[None, :]
    m = np.cos(np.pi * (2 * i + 1) * k / (2 * n))
    m[0] *= 1 / np.sqrt(2)
    return m * np.sqrt(2 / n)


_D = _dct_matrix(N)


def phash(path):
    """내용 영역(알파>12)을 잘라 흰 배경에 얹고 64x64 DCT 저주파 16x16의 부호를 비트로 쓴다.
    같은 캐릭터 스티커끼리는 실루엣이 비슷하므로 8x8 pHash보다 비트를 늘리고 내용 영역만 본다."""
    im = Image.open(path).convert("RGBA")
    al = np.asarray(im)[:, :, 3]
    ys, xs = np.where(al > 12)
    if len(ys):
        im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    side = max(im.size)
    bg = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    bg.alpha_composite(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2))
    g = bg.convert("L").resize((N, N), Image.LANCZOS)
    d = _D @ np.asarray(g, dtype=np.float64) @ _D.T
    low = d[:K, :K].flatten()[1:]
    return (low > np.median(low)).astype(np.uint8)


def check(folder, files, a):
    hashes = {}
    for f in files:
        try:
            hashes[f] = phash(os.path.join(folder, f))
        except Exception as e:  # noqa
            hashes[f] = None
            hashes[("err", f)] = f"{type(e).__name__}: {e}"
    out = []
    kept = []
    for f in files:
        h = hashes[f]
        if h is None:
            out.append(res(f, False, "UNREADABLE", hashes[("err", f)]))
            continue
        dup = None
        for g in kept:
            dist = int((h != hashes[g]).sum())
            if dist <= a.max_dist:
                dup = (g, dist)
                break
        if dup:
            out.append(res(f, False, "DUPLICATE", f"{dup[0]} 와 같은 그림(해밍 거리 {dup[1]}/255)"))
        else:
            kept.append(f)
            out.append(res(f, True, "OK", "중복 없음"))
    return out


if __name__ == "__main__":
    run("dup", check, extra_args={
        "--max-dist": {"type": int, "default": 12, "help": "중복으로 보는 최대 해밍 거리(255비트 중)"}})
