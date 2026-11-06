#!/usr/bin/env python3
"""알파 정리: 알파 12 이하는 0(RGB도 0), 240 이상은 255로 만든다.

원본 폴더는 건드리지 않고 출력 폴더에 같은 이름으로 쓴다.
사용: python3 alpha_clean.py <입력폴더> <출력폴더>
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

LOW, HIGH = 12, 240


def clean(src, dst):
    im = Image.open(src)
    a = np.array(im.convert("RGBA"))
    al = a[:, :, 3]
    low = al <= LOW
    al[al >= HIGH] = 255
    al[low] = 0
    a[low, :3] = 0
    a[:, :, 3] = al
    Image.fromarray(a, "RGBA").save(dst, optimize=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src")
    ap.add_argument("dst")
    a = ap.parse_args(argv)
    s, d = os.path.realpath(a.src), os.path.realpath(a.dst)
    if s == d:
        print("입력과 출력 폴더가 같다. 원본 보호를 위해 중단.", file=sys.stderr)
        return 2
    os.makedirs(d, exist_ok=True)
    done, failed = [], []
    for f in sorted(os.listdir(s)):
        if not f.lower().endswith(".png"):
            continue
        try:
            clean(os.path.join(s, f), os.path.join(d, f))
            done.append(f)
        except Exception as e:  # noqa
            failed.append({"file": f, "error": f"{type(e).__name__}: {e}"})
    print(json.dumps({"cleaned": len(done), "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
