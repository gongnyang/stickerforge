"""OpenAI Images API provider (표준 라이브러리 urllib). OPENAI_API_KEY 필요.
엔드포인트: POST /v1/images/generations, 참조 이미지가 있으면 POST /v1/images/edits (multipart).
투명: gpt-image-2 는 background=transparent 미지원. 몰래 다른 모델로 바꾸지 않고, 초록(#00FF00) 단색 배경으로 그리게 한 뒤
크로마키로 알파를 만든다. 네이티브 투명은 spec 에서 model 을 gpt-image-1.5 로 직접 지정했을 때만 쓴다.
이 모듈은 이 PC에 키가 없어 실제 호출 시험을 하지 못했다(PROVIDER_STATUS.md 참조)."""
import base64, json, mimetypes, os, sys, uuid
import urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import postprocess

DEFAULT_MODEL = "gpt-image-2"
NATIVE_TRANSPARENT = {"gpt-image-1.5", "gpt-image-1"}
CHROMA_NOTE = " Background: a single flat solid pure green (#00FF00) fill, no shadow, no gradient, no green anywhere on the subject."


def _multipart(fields, files):
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, path in files:
        mt = mimetypes.guess_type(path)[0] or "application/octet-stream"
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{Path(path).name}"\r\n'
                     f'Content-Type: {mt}\r\n\r\n'.encode() + Path(path).read_bytes() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={b}"


def generate(job, cfg):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return {"ok": False, "thread_id": "", "error": "OPENAI_API_KEY 없음", "note": ""}
    model = cfg.get("model") or DEFAULT_MODEL
    size = cfg.get("size") or "1024x1024"
    native = job["transparent"] and model in NATIVE_TRANSPARENT
    chroma = job["transparent"] and not native
    prompt = job["prompt"] + (CHROMA_NOTE if chroma else "")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    fields = {"model": model, "prompt": prompt, "n": "1", "size": size, "output_format": "png"}
    if native:
        fields["background"] = "transparent"
    refs = job.get("refs", [])
    try:
        if refs:
            data, ct = _multipart(fields, [("image[]", r) for r in refs])
            req = urllib.request.Request(base + "/images/edits", data=data, headers={"Content-Type": ct})
        else:
            req = urllib.request.Request(base + "/images/generations", data=json.dumps(fields).encode(),
                                         headers={"Content-Type": "application/json"})
        req.add_header("Authorization", "Bearer " + key)
        with urllib.request.urlopen(req, timeout=int(cfg.get("timeout", 420))) as r:
            body = json.load(r)
        img = base64.b64decode(body["data"][0]["b64_json"])
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="ignore")[:300]
        stop = e.code in (401, 429)  # 한도/인증이면 호출자가 재시도 폭주 없이 멈춘다
        return {"ok": False, "thread_id": "", "error": f"HTTP {e.code} {msg}", "note": "stop" if stop else ""}
    except Exception as e:
        return {"ok": False, "thread_id": "", "error": f"{type(e).__name__}: {e}", "note": ""}
    out = Path(job["out"]); out.parent.mkdir(parents=True, exist_ok=True)
    postprocess.save_png(img, str(out))
    if chroma:
        postprocess.chroma_key(str(out))
    return {"ok": True, "thread_id": "", "error": "", "note": "chroma-key" if chroma else "native"}
