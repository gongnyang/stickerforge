"""Gemini 이미지 provider (REST generateContent, 표준 라이브러리 urllib). GEMINI_API_KEY 필요.
엔드포인트: POST https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent
응답의 candidates[0].content.parts[].inlineData.data (base64) 가 이미지. 투명 배경 미지원이므로 초록 단색 배경 후 크로마키.
이 모듈은 이 PC에 키가 없어 실제 호출 시험을 하지 못했다(PROVIDER_STATUS.md 참조)."""
import base64, json, mimetypes, os, sys
import urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import postprocess

DEFAULT_MODEL = "gemini-2.5-flash-image"
CHROMA_NOTE = " Background: a single flat solid pure green (#00FF00) fill, no shadow, no gradient, no green anywhere on the subject."


def generate(job, cfg):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return {"ok": False, "thread_id": "", "error": "GEMINI_API_KEY 없음", "note": ""}
    model = cfg.get("model") or DEFAULT_MODEL
    chroma = job["transparent"]
    parts = [{"text": job["prompt"] + (CHROMA_NOTE if chroma else "")}]
    for r in job.get("refs", []):
        parts.append({"inline_data": {"mime_type": mimetypes.guess_type(r)[0] or "image/png",
                                      "data": base64.b64encode(Path(r).read_bytes()).decode()}})
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"]}}
    base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    req = urllib.request.Request(f"{base}/models/{model}:generateContent", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=int(cfg.get("timeout", 420))) as r:
            resp = json.load(r)
        img = None
        for p in resp["candidates"][0]["content"]["parts"]:
            d = p.get("inlineData") or p.get("inline_data")
            if d:
                img = base64.b64decode(d["data"]); break
        if img is None:
            return {"ok": False, "thread_id": "", "error": "응답에 이미지 없음 " + json.dumps(resp)[:200], "note": ""}
    except urllib.error.HTTPError as e:
        return {"ok": False, "thread_id": "", "error": f"HTTP {e.code} {e.read().decode(errors='ignore')[:300]}",
                "note": "stop" if e.code in (401, 403, 429) else ""}
    except Exception as e:
        return {"ok": False, "thread_id": "", "error": f"{type(e).__name__}: {e}", "note": ""}
    out = Path(job["out"]); out.parent.mkdir(parents=True, exist_ok=True)
    postprocess.save_png(img, str(out))
    if chroma:
        postprocess.chroma_key(str(out))
    return {"ok": True, "thread_id": "", "error": "", "note": "chroma-key" if chroma else ""}
