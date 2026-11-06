#!/usr/bin/env python3
"""생성 직후 후처리. 그림 위에 글자를 얹지 않는다. 하는 일은 알파 정리와 크로마키 제거뿐.
알파 12 이하는 0, 240 이상은 255. 알파 채널이 없으면 그대로 두고 게이트가 잡는다(가짜 투명 포함)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image


def clean_alpha(path):
    im = Image.open(path)
    if im.mode != "RGBA":
        return False
    a = np.array(im)
    al = a[..., 3]
    al[al <= 12] = 0
    al[al >= 240] = 255
    Image.fromarray(a, "RGBA").save(path)
    return True


def chroma_key(path, key=(0, 255, 0), tol=70, soft=40):
    """단색 배경(기본 #00FF00)을 알파로 바꾼다. 가장자리 초록 번짐은 제거."""
    im = Image.open(path).convert("RGB")
    a = np.array(im).astype(np.int32)
    d = np.sqrt(((a - np.array(key)) ** 2).sum(-1))
    alpha = np.clip((d - tol) / soft, 0, 1) * 255
    # 키 색 번짐 제거: 초록이 다른 채널보다 튀는 만큼 깎는다
    rgb = a.copy()
    spill = np.maximum(rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2]), 0)
    edge = (alpha > 0) & (alpha < 255)
    rgb[..., 1] = np.where(edge, rgb[..., 1] - spill, rgb[..., 1])
    out = np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(path)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    for p in sys.argv[1:]:
        print(p, clean_alpha(p))


def save_png(data, path):
    """API가 준 바이트(PNG/JPEG/WebP)를 PNG 파일로 저장."""
    import io
    Image.open(io.BytesIO(data)).save(path, "PNG")
