#!/usr/bin/env python3
"""환경 감지. 값은 출력하지 않고 설정 여부만 본다.
사용: doctor.py [--provider auto|codex|openai|gemini] [--json]
exit 0 = 생성 가능한 provider 있음, 2 = 미지원(사유 출력). 낮은 품질 경로로 조용히 바꾸지 않는다."""
import json, os, shutil, subprocess, sys

ORDER = ["codex", "openai", "gemini"]


def check_codex():
    exe = shutil.which("codex")
    if not exe:
        return False, "codex CLI 없음. 설치 후 codex login 필요"
    try:
        p = subprocess.run([exe, "login", "status"], capture_output=True, text=True, timeout=30)
    except Exception as e:
        return False, f"codex login status 실행 실패: {e}"
    txt = (p.stdout + p.stderr)
    if "Logged in using ChatGPT" in txt:
        return True, "codex ChatGPT 로그인 확인"
    if "Logged in" in txt:
        return False, "codex가 API 키 로그인 상태. 내장 이미지 도구는 ChatGPT 로그인이 필요. codex login 으로 다시 로그인"
    return False, "codex 로그인 안 됨. codex login 필요"


def check_key(name):
    if os.environ.get(name):
        return True, f"{name} 설정됨"
    return False, f"{name} 없음"


def detect():
    res = {}
    ok, why = check_codex(); res["codex"] = {"ok": ok, "why": why}
    ok, why = check_key("OPENAI_API_KEY"); res["openai"] = {"ok": ok, "why": why}
    ok, why = check_key("GEMINI_API_KEY"); res["gemini"] = {"ok": ok, "why": why}
    return res


def select(want="auto", res=None):
    """(provider, 사유). provider가 None이면 미지원."""
    res = res or detect()
    if want != "auto":
        if want not in res:
            return None, f"알 수 없는 provider: {want}"
        if res[want]["ok"]:
            return want, res[want]["why"]
        return None, f"지정한 provider {want} 사용 불가: {res[want]['why']}"
    for p in ORDER:
        if res[p]["ok"]:
            return p, res[p]["why"]
    return None, "생성 가능한 경로 없음. " + " / ".join(f"{p}: {res[p]['why']}" for p in ORDER) + \
        ". 해결: Codex 설치+ChatGPT 로그인, 또는 OPENAI_API_KEY, 또는 GEMINI_API_KEY 설정"


def main(argv):
    want = "auto"
    if "-h" in argv or "--help" in argv:
        print(__doc__); return 0
    if "--provider" in argv:
        want = argv[argv.index("--provider") + 1]
    res = detect()
    prov, why = select(want, res)
    if "--json" in argv:
        print(json.dumps({"selected": prov, "reason": why, "detail": res}, ensure_ascii=False, indent=1))
    else:
        for p in ORDER:
            print(f"{p:7} {'OK ' if res[p]['ok'] else 'NO '} {res[p]['why']}")
        print(f"선택: {prov or '없음'} ({why})")
    return 0 if prov else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
