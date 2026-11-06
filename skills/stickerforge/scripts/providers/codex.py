"""Codex provider. codex exec --json 의 thread_id 로 세션 폴더를 특정해 PNG를 회수한다(시간 기준 회수 금지).
내장 image_gen 도구는 크기 인자가 없다. 결과는 1254~1536px 근처이고 투명은 transparent_background=true 로 요청한다.
앞단 모델 기본 gpt-6.1-terra, effort medium. 가벼운 모델은 프롬프트를 바꿔 전달해 품질이 떨어진다."""
import json, os, shutil, signal, subprocess, time
from pathlib import Path

DEFAULT_MODEL = "gpt-6.1-terra"


def codex_home():
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def instruction(prompt, transparent):
    t = ("Set transparent_background=true in the image_gen call. The background must be truly transparent (alpha channel), "
         "not a drawn checkerboard.\n" if transparent else "")
    return ("Use $imagegen (the built-in image_gen tool) to generate exactly ONE image.\n"
            "Pass the prompt below to the tool VERBATIM. Do not rewrite, shorten, translate or add to it.\n"
            + t +
            "Use every attached reference image as a reference (referenced_image_paths).\n"
            "After generation do NOT run any shell commands and do NOT move files. End your turn.\n"
            "=== PROMPT ===\n" + prompt)


def parse_log(path):
    tid, last, err = "", "", ""
    if not Path(path).exists():
        return tid, last, err
    for l in Path(path).read_text(errors="ignore").splitlines():
        try:
            e = json.loads(l)
        except Exception:
            continue
        if e.get("type") == "thread.started":
            tid = e.get("thread_id", tid)
        it = e.get("item", {})
        if e.get("type") == "item.completed" and it.get("type") == "agent_message":
            last = it.get("text", "")
        if e.get("type") in ("error", "turn.failed"):
            err = json.dumps(e, ensure_ascii=False)[:300]
    return tid, last, err


def find_pngs(tid):
    d = codex_home() / "generated_images" / tid
    return sorted(d.glob("*.png"), key=lambda x: x.stat().st_mtime) if tid and d.is_dir() else []


def generate(job, cfg):
    model = cfg.get("model") or DEFAULT_MODEL
    effort = cfg.get("effort") or "medium"
    timeout = int(cfg.get("timeout", 420))
    cmd = ["codex", "exec", "--json", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
           "-m", model, "-c", f"model_reasoning_effort={effort}", "-c", "web_search=disabled",
           instruction(job["prompt"], job["transparent"])]
    for r in job.get("refs", []):  # -i 는 프롬프트 뒤에 둔다
        cmd += ["-i", r]
    log = Path(job["log"]); log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(log, "w") as lf:
        p = subprocess.Popen(cmd, cwd=job.get("cwd") or None, stdin=subprocess.DEVNULL, stdout=lf, stderr=subprocess.STDOUT,
                             start_new_session=True)
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(10)
            except Exception:
                os.killpg(p.pid, signal.SIGKILL)
    tid, last, err = parse_log(log)
    pngs = find_pngs(tid)
    if not pngs and tid:  # 롤아웃 기록 지연 대비 짧게 한 번 더
        time.sleep(3); pngs = find_pngs(tid)
    if not pngs:
        return {"ok": False, "thread_id": tid, "error": ("timeout " if p.returncode in (None, -15, -9) else "") +
                "no-image " + (err or last[:200]), "note": f"{time.time()-t0:.0f}s"}
    Path(job["out"]).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pngs[-1]), job["out"])
    return {"ok": True, "thread_id": tid, "error": "", "note": f"{time.time()-t0:.0f}s"}


def ingest_latest(thread_id, out, skip=()):
    """내장 도구 순차 호출 모드: 바깥 스레드 자신의 폴더에서 아직 가져가지 않은 가장 새 PNG를 out으로 옮긴다."""
    pngs = [p for p in find_pngs(thread_id) if p.name not in skip]
    if not pngs:
        return False
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pngs[-1]), out)
    return True
