"""게이트 공통 도구. 표준 라이브러리 + Pillow + numpy만 쓴다."""
import json
import os
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def list_pngs(folder):
    return sorted(f for f in os.listdir(folder)
                  if f.lower().endswith(".png") and os.path.isfile(os.path.join(folder, f)))


def has_alpha(im):
    return im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info


def load_rgba(path):
    im = Image.open(path)
    im.load()
    alpha_ok = has_alpha(im)
    rgba = np.array(im.convert("RGBA"))
    return im, rgba, alpha_ok


def res(file, ok, code, detail=""):
    return {"file": file, "pass": bool(ok), "code": code, "detail": detail}


def run(gate, check, argv=None, extra_args=None):
    """check(folder, files, opts) -> results 리스트. 실패가 있으면 exit 1."""
    import argparse
    ap = argparse.ArgumentParser(description=f"stickerforge 게이트: {gate}")
    ap.add_argument("folder")
    for name, kw in (extra_args or {}).items():
        ap.add_argument(name, **kw)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.folder):
        print(json.dumps({"gate": gate, "results": [res("", False, "NO_FOLDER", a.folder)]},
                         ensure_ascii=False))
        sys.exit(1)
    files = list_pngs(a.folder)
    results = check(a.folder, files, a)
    print(json.dumps({"gate": gate, "results": results}, ensure_ascii=False))
    sys.exit(1 if any(not r["pass"] for r in results) else 0)


def safe(fn):
    """파일 하나가 깨져도 게이트 전체가 죽지 않게 한다."""
    def wrap(folder, f, *a, **k):
        try:
            return fn(folder, f, *a, **k)
        except Exception as e:  # noqa
            return res(f, False, "UNREADABLE", f"{type(e).__name__}: {e}")
    return wrap
