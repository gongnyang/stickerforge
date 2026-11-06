#!/usr/bin/env python3
"""게이트 시험. 합성 불량본을 만들어 게이트마다 불량은 잡고 정상은 통과시키는지 본다.

사용: python3 run_tests.py            (임시 폴더에 생성 후 삭제)
      python3 run_tests.py --real <폴더>   실제 폴더에 전 게이트를 돌려 개수만 출력(읽기 전용)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
GATES = os.path.join(SKILL, "scripts", "gates")
sys.path.insert(0, HERE)
import make_fixtures  # noqa

GOOD = ["good_a.png", "good_b.png", "good_c.png"]
# 게이트: 이 게이트에서 실패해야 하는 파일 -> 코드. 나머지는 통과해야 한다.
EXPECT = {
    "g01_size.py": {"bad_small.png": "TOO_SMALL"},
    "g02_alpha.py": {"bad_noalpha.png": "NO_ALPHA", "bad_checker_rgb.png": "NO_ALPHA",
                     "bad_checker_rgba.png": "ALL_OPAQUE"},
    "g03_checker.py": {"bad_checker_rgb.png": "FAKE_CHECKER", "bad_checker_rgba.png": "FAKE_CHECKER"},
    "g04_margin.py": {"bad_cropped.png": "TOUCHES_EDGE", "bad_noalpha.png": "NO_ALPHA",
                      "bad_checker_rgb.png": "NO_ALPHA"},
    "g05_outline.py": {"bad_outline_broken.png": "OUTLINE_BROKEN", "bad_noalpha.png": "NO_ALPHA",
                       "bad_checker_rgb.png": "NO_ALPHA"},
    "g06_dup.py": {"z_bad_dup_of_a.png": "DUPLICATE"},
}


def run_gate(script, folder):
    p = subprocess.run([sys.executable, os.path.join(GATES, script), folder],
                       capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)["results"]


def synthetic():
    tmp = tempfile.mkdtemp(prefix="sf_fx_", dir=os.environ.get("SF_TMP") or None)
    fails = 0
    try:
        make_fixtures.build(tmp)
        files = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
        for script, exp in EXPECT.items():
            rc, results = run_gate(script, tmp)
            by = {r["file"]: r for r in results}
            errs = []
            for f in files:
                r = by.get(f)
                if f in exp:
                    if r is None or r["pass"] or r["code"] != exp[f]:
                        errs.append(f"{f}: 불량을 못 잡음 {r and r['code']}")
                elif f.startswith("good_") and (r is None or not r["pass"]):
                    errs.append(f"{f}: 정상인데 실패 {r and r['code']}")
            if (rc == 1) != any(not r["pass"] for r in results):
                errs.append("exit 코드가 결과와 다름")
            print(("PASS " if not errs else "FAIL ") + script + ("" if not errs else " " + "; ".join(errs)))
            fails += bool(errs)
        # alpha_clean 시험
        out = tempfile.mkdtemp(prefix="sf_clean_", dir=os.environ.get("SF_TMP") or None)
        try:
            import numpy as np
            from PIL import Image
            src = tempfile.mkdtemp(prefix="sf_src_", dir=os.environ.get("SF_TMP") or None)
            a = np.zeros((40, 40, 4), np.uint8)
            a[:, :, :3] = 100
            a[:10, :, 3] = 5
            a[10:20, :, 3] = 120
            a[20:, :, 3] = 245
            Image.fromarray(a, "RGBA").save(os.path.join(src, "t.png"))
            before = open(os.path.join(src, "t.png"), "rb").read()
            p = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "alpha_clean.py"), src, out],
                               capture_output=True, text=True)
            b = np.array(Image.open(os.path.join(out, "t.png")))
            ok = (p.returncode == 0 and (b[:10, :, 3] == 0).all() and (b[10:20, :, 3] == 120).all()
                  and (b[20:, :, 3] == 255).all() and open(os.path.join(src, "t.png"), "rb").read() == before)
            same = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "alpha_clean.py"), src, src],
                                  capture_output=True, text=True).returncode == 2
            print(("PASS " if ok and same else "FAIL ") + "alpha_clean.py")
            fails += not (ok and same)
            shutil.rmtree(src)
        finally:
            shutil.rmtree(out)
    finally:
        shutil.rmtree(tmp)
    return fails


def pilot_test():
    """S2 시험 생성: 더미 provider 로 pilot_count 장을 서로 다른 컨셉으로 뽑고, 재개 시 다시 만들지 않으며 B 에서 멈추는지."""
    import types
    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    import run as R
    from manifest import Manifest
    from pathlib import Path
    calls = []

    def fake_generate(job, cfg):
        calls.append(job["id"])
        make_fixtures.sticker().save(job["out"])
        return {"ok": True, "thread_id": "", "error": "", "note": ""}
    sys.modules["providers.dummy"] = types.SimpleNamespace(generate=fake_generate)
    tmp = tempfile.mkdtemp()
    fails = 0
    try:
        def ctx_for(n, trial=None, count=None):
            proj = Path(tmp) / f"p{n}"
            (proj / "out").mkdir(parents=True, exist_ok=True)
            spec = {"name": "t", "ref": "", "style": "s", "parallel": 2,
                    "concepts": [{"id": f"c{i}", "prompt": f"p{i}"} for i in range(8)]}
            if trial:
                spec["trial"] = trial
            if count is not None:
                spec["pilot_count"] = count
            c = R.Ctx(); c.project, c.spec, c.yes = proj, spec, False
            c.man = Manifest(proj); c.halt = ""; c.approved = set(); c.cur = "S2"; c.provider = "dummy"
            return c
        def run_s2(c):
            try:
                R.s2(c); return 0
            except R.Stop as e:
                return e.code
        checks = []
        c = ctx_for(1)  # 기본 6장, 서로 다른 컨셉, B 에서 멈춤
        rc = run_s2(c); checks.append(("기본 6장 생성 후 B 대기", rc == 3 and len(calls) == 6 and len(set(calls)) == 6))
        calls.clear(); c.man = Manifest(c.project)
        rc = run_s2(c); checks.append(("재개 시 재생성 없음", rc == 3 and calls == []))
        c.approved = {"B"}; rc = run_s2(c); checks.append(("승인 후 통과", rc == 0 and calls == []))
        calls.clear(); c = ctx_for(2, count=20)
        run_s2(c); checks.append(("컨셉 수 초과 시 컨셉 수로 제한", len(calls) == 8 and len(set(calls)) == 8))
        calls.clear(); c = ctx_for(3, count=1)
        rc = run_s2(c); checks.append(("pilot_count 1", rc == 3 and calls == ["c0"]))
        calls.clear(); c = ctx_for(4, trial="c5", count=3)
        run_s2(c); checks.append(("trial 포함 3장", "c5" in calls and len(set(calls)) == 3))
        calls.clear(); c = ctx_for(5, count=0)
        checks.append(("pilot_count 0 은 spec 오류", run_s2(c) == 4))
        for name, ok in checks:
            print(("PASS " if ok else "FAIL ") + "pilot: " + name)
            fails += not ok
    finally:
        shutil.rmtree(tmp)
    return fails


def real(folder):
    summary = {}
    for script in EXPECT:
        rc, results = run_gate(script, folder)
        codes = {}
        for r in results:
            if not r["pass"]:
                codes[r["code"]] = codes.get(r["code"], 0) + 1
        summary[script] = {"total": len(results), "fail": sum(codes.values()), "codes": codes}
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--real":
        real(sys.argv[2])
    else:
        n = synthetic() + pilot_test()
        print("전체 통과" if n == 0 else f"실패 {n}건")
        sys.exit(1 if n else 0)
