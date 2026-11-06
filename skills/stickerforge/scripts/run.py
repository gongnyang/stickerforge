#!/usr/bin/env python3
"""stickerforge 단일 진입. 작업 폴더(spec.json 이 있는 곳)를 받아 S0~S6 을 순서대로 돈다.

진입 명령
  python3 run.py <projectDir>                    처음부터. 끝난 단계는 건너뜀(재개)
  python3 run.py <projectDir> --from S3          S3 부터 다시
  python3 run.py <projectDir> --approve A        사람 확인 A(스타일) 기록 후 이어서. B(시험 생성), C(최종)도 같음
  python3 run.py <projectDir> --yes              A,B,C 를 모두 승인한 것으로 처리(시험·자동화용)
  python3 run.py <projectDir> --status           현재 상태 표만 출력
  python3 run.py <projectDir> --doctor           환경 감지만
  python3 run.py <projectDir> --cleanup          이 프로젝트 codex 스레드 롤아웃 삭제
내장 도구 순차 호출 모드(분리 실행이 안 되는 Codex 단독용, 장마다 사람 또는 바깥 에이전트가 호출)
  python3 run.py <projectDir> --next                              다음 장의 프롬프트·참조·저장 경로를 JSON 으로
  python3 run.py <projectDir> --ingest <id> --file <png> [--thread-id T]   만든 PNG 를 원장에 등록

단계: S0 의뢰·스타일 고정(확인 A) / S1 컨셉 중복 검사 / S2 시험 생성(확인 B) / S3 양산 /
      S4 게이트 / S5 실패분 재시도(2회) / S6 시트·납품(확인 C)
exit code: 0 완료, 2 미지원 환경, 3 사람 확인 대기, 4 spec·컨셉 오류, 5 일부 장 최종 실패, 6 한도·인증 정지, 7 게이트 오류
작업 폴더 구조: spec.json manifest.jsonl out/ qc/ export/ logs/  (스킬 폴더 밖에 둔다)"""
import argparse, json, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import doctor, postprocess, sheet, cleanup  # noqa: E402
from manifest import Manifest  # noqa: E402
import providers  # noqa: E402

STAGES = ["S0", "S1", "S2", "S3", "S4", "S5", "S6"]
MAX_RETRY = 2
MAX_PARALLEL = 10


class Stop(Exception):
    def __init__(self, code, msg):
        self.code, self.msg = code, msg


class Ctx:
    pass


# ---------- 공통 ----------
def load_spec(project):
    p = project / "spec.json"
    if not p.exists():
        raise Stop(4, f"{p} 없음")
    spec = json.loads(p.read_text(encoding="utf-8"))
    miss = [k for k in ("name", "ref", "style", "concepts") if k not in spec]
    if miss:
        raise Stop(4, f"spec.json 필수 항목 없음: {miss} (schemas/spec.schema.json 참조)")
    ids = [c.get("id") for c in spec["concepts"]]
    if not spec["concepts"] or None in ids or len(set(ids)) != len(ids) or not all(re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids):
        raise Stop(4, "concepts 가 비었거나 id 가 없음, 중복, 허용 문자(영숫자 _ -) 위반")
    if any(not c.get("prompt") for c in spec["concepts"]):
        raise Stop(4, "prompt 가 빈 컨셉이 있음")
    return spec


def compose_prompt(spec, c):
    parts = [spec["style"].strip()]
    if spec.get("character"):
        parts.append("Character (match the attached reference image exactly): " + spec["character"].strip())
    parts.append("Pose and situation: " + c["prompt"].strip())
    parts.append("Die-cut sticker design: one single subject centered, clean bold outline. Keep the whole sticker, including its white border, inside the canvas with at least 6% empty margin on every side. "
                 "Include no text, letters or watermark unless the pose line above explicitly asks for specific text.")
    return "\n".join(parts)


def make_job(ctx, c):
    return {"id": c["id"], "prompt": compose_prompt(ctx.spec, c),
            "refs": [str(ctx.project / ctx.spec["ref"])] if ctx.spec.get("ref") else [],
            "out": str(ctx.project / "out" / f"{c['id']}.png"),
            "transparent": bool(ctx.spec.get("transparent", True)),
            "log": str(ctx.project / "logs" / f"{c['id']}.a{ctx.man.attempts(c['id'])+1}.jsonl"),
            "cwd": str(ctx.project)}


def generate_one(ctx, c):
    prov = providers.get(ctx.provider)
    job = make_job(ctx, c)
    attempt = ctx.man.attempts(c["id"]) + 1
    res = prov.generate(job, ctx.spec.get(ctx.provider, {}))
    if res["ok"] and ctx.spec.get("transparent", True):
        postprocess.clean_alpha(job["out"])
    ctx.man.append(c["id"], "generated" if res["ok"] else "gen_failed", stage=ctx.cur, attempt=attempt,
                   provider=ctx.provider, thread_id=res.get("thread_id", ""), note=res.get("note", ""),
                   error=res.get("error", ""), path=f"out/{c['id']}.png" if res["ok"] else "")
    if res.get("note") == "stop":
        ctx.halt = res["error"]
    print(f"  {c['id']:12} {'ok ' if res['ok'] else 'FAIL'} a{attempt} {res.get('note','')} {res.get('error','')[:120]}", flush=True)
    return res["ok"]


def generate_many(ctx, concepts):
    if not concepts:
        return
    par = min(int(ctx.spec.get("parallel", 8)), MAX_PARALLEL)
    print(f"  생성 {len(concepts)}장, 동시 {par}, provider {ctx.provider}", flush=True)

    def work(c):
        if ctx.halt:
            return False
        return generate_one(ctx, c)
    with ThreadPoolExecutor(par) as ex:
        list(ex.map(work, concepts))
    if ctx.halt:
        raise Stop(6, f"한도·인증 오류로 정지: {ctx.halt}. 해결 후 같은 명령으로 재개")


def need_approval(ctx, key, what):
    if ctx.yes or key in ctx.approved or ctx.man.done(f"_approve_{key}", "ok"):
        ctx.man.append(f"_approve_{key}", "ok", stage=ctx.cur, note="yes" if ctx.yes else "")
        return
    raise Stop(3, f"사람 확인 {key} 대기: {what}\n승인: python3 run.py {ctx.project} --approve {key}")


# ---------- 게이트 ----------
def gate_files():
    d = SCRIPTS / "gates"
    return sorted(p for p in d.glob("*.py") if not p.name.startswith("_"))


def call_gate(p, args):
    r = subprocess.run([sys.executable, str(p)] + args, capture_output=True, text=True, timeout=600)
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
        j["results"]
    except Exception:
        raise Stop(7, f"게이트 {p.name} 출력이 규약 JSON 이 아님 (exit {r.returncode}): {r.stdout[-200:]} {r.stderr[-300:]}")
    if r.returncode not in (0, 1):
        raise Stop(7, f"게이트 {p.name} 자체 오류 exit {r.returncode}: {r.stderr[-300:]}")
    return j


def builtin_check(ctx, f):
    from PIL import Image
    import numpy as np
    try:
        im = Image.open(f); im.load()
    except Exception as e:
        return [f"열 수 없음: {e}"]
    why = []
    mn = int(ctx.spec.get("min_px", 1024))
    if min(im.size) < mn:
        why.append(f"크기 {im.size} 가 min_px {mn} 미만")
    if ctx.spec.get("transparent", True):
        if im.mode != "RGBA":
            why.append("알파 채널 없음(가짜 투명 의심)")
        else:
            a = np.array(im)[..., 3]
            if (a == 0).mean() < 0.05:
                why.append("투명 영역이 5% 미만")
    return why


def run_gates(ctx, ids):
    """out/ 폴더를 게이트마다 한 번씩 검사하고 ids 에 해당하는 불합격만 {id: [사유...]} 로 돌려준다."""
    fails = {}
    gates = gate_files()
    if not gates:
        ctx.man.append("_gates", "warn", stage=ctx.cur, note="scripts/gates 에 게이트 없음. 최소 검사만 수행")
        print("  경고: scripts/gates 에 게이트가 없어 최소 검사만 합니다", flush=True)
        for i in ids:
            why = builtin_check(ctx, ctx.project / "out" / f"{i}.png")
            if why:
                fails[i] = why
        return fails
    transparent = ctx.spec.get("transparent", True)
    for g in gates:
        if not transparent and re.search(r"alpha|checker|margin|outline", g.stem):
            continue  # 투명을 요구하지 않는 spec 은 알파 의존 게이트를 건너뜀
        extra = [str(x) for x in ctx.spec.get("gates", {}).get(re.sub(r"^g\d+_", "", g.stem), [])]
        if "size" in g.stem and "min_px" in ctx.spec and not extra:
            extra = ["--min-px", str(ctx.spec["min_px"])]
        j = call_gate(g, [str(ctx.project / "out")] + extra)
        for r in j["results"]:
            i = Path(r.get("file", "")).stem
            if i in ids and not r.get("pass"):
                fails.setdefault(i, []).append(f"{j.get('gate', g.stem)}/{r.get('code', '')}: {r.get('detail', '')}")
    return fails


def apply_gate_result(ctx, ids):
    fails = run_gates(ctx, ids)
    for i in ids:
        if i in fails:
            att = ctx.man.attempts(i)
            src = ctx.project / "out" / f"{i}.png"
            dst = ctx.project / "qc" / "rejected" / f"{i}.a{att}.png"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.move(str(src), dst)
            ctx.man.append(i, "gate_failed", stage=ctx.cur, attempt=att, note="; ".join(fails[i])[:300])
            print(f"  {i:12} 불합격 {'; '.join(fails[i])[:140]}", flush=True)
        else:
            ctx.man.append(i, "passed", stage=ctx.cur, attempt=ctx.man.attempts(i), path=f"out/{i}.png")
    return fails


# ---------- 단계 ----------
def s0(ctx):
    want = ctx.args.provider or ctx.spec.get("provider", "auto")
    prov, why = doctor.select(want)
    if not prov:
        raise Stop(2, "미지원 환경: " + why)
    ref = ctx.project / ctx.spec["ref"]
    if not ref.exists():
        raise Stop(4, f"참조 이미지 없음: {ref}")
    ctx.provider = prov
    print(f"  provider {prov} ({why}), 참조 {ref.name}, 컨셉 {len(ctx.spec['concepts'])}개, 투명 {ctx.spec.get('transparent', True)}")
    ctx.man.append("_S0", "done", stage="S0", provider=prov, note=why)  # 먼저 기록해 provider 를 고정
    need_approval(ctx, "A", f"스타일 문구와 참조를 확인: {ctx.spec['style'][:80]}")


def toks(c):
    return set(re.findall(r"[\w가-힣]+", (c.get("title", "") + " " + c["prompt"]).lower()))


def s1(ctx):
    cs = ctx.spec["concepts"]
    bad = []
    for a in range(len(cs)):
        for b in range(a + 1, len(cs)):
            ta, tb = toks(cs[a]), toks(cs[b])
            j = len(ta & tb) / max(1, len(ta | tb))
            if j >= float(ctx.spec.get("dup_threshold", 0.8)):
                bad.append((cs[a]["id"], cs[b]["id"], round(j, 2)))
    if bad:
        raise Stop(4, f"컨셉 중복 의심 {bad}. spec.json 의 concepts 를 고치세요")
    print(f"  컨셉 {len(cs)}개 중복 없음")


def pilot_concepts(spec):
    """시험 생성 대상. trial 로 지정한 컨셉을 먼저, 나머지는 전체에 고르게 퍼뜨려 서로 다른 컨셉으로 뽑는다."""
    cs = spec["concepts"]
    n = spec.get("pilot_count", 6)
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise Stop(4, f"pilot_count 는 1 이상 정수여야 함: {n!r}")
    n = min(n, len(cs))
    trial = spec.get("trial")
    picked = []
    if trial:
        c = next((x for x in cs if x["id"] == trial), None)
        if not c:
            raise Stop(4, f"trial id {trial} 가 concepts 에 없음")
        picked.append(c)
    for k in range(n):  # 균등 간격 후보를 앞에서부터 채운다
        c = cs[(k * len(cs)) // n]
        if len(picked) < n and c not in picked:
            picked.append(c)
    for c in cs:  # 간격 후보가 겹쳐 모자라면 순서대로 채움
        if len(picked) >= n:
            break
        if c not in picked:
            picked.append(c)
    return picked[:n]


def s2(ctx):
    pilot = pilot_concepts(ctx.spec)
    todo = []
    for c in pilot:
        st = ctx.man.get(c["id"])
        done = st and st["status"] in ("generated", "passed") and (ctx.project / "out" / f"{c['id']}.png").exists()
        if not done:
            todo.append(c)
    print(f"  시험 {len(pilot)}장 중 새로 생성 {len(todo)}장 (이미 있는 시험본은 건너뜀)")
    generate_many(ctx, todo)
    miss = [c["id"] for c in pilot if not (ctx.project / "out" / f"{c['id']}.png").exists()]
    if miss:
        raise Stop(5, f"시험 생성 실패({miss}). logs/ 확인 후 재실행")
    files = ", ".join(f"{ctx.project}/out/{c['id']}.png" for c in pilot)
    need_approval(ctx, "B", f"시험 생성 확인({len(pilot)}장): {files}")


def pending(ctx):
    out = []
    for c in ctx.spec["concepts"]:
        st = ctx.man.get(c["id"])
        has = (ctx.project / "out" / f"{c['id']}.png").exists()
        if not has and not (st and st["status"] == "exhausted") and ctx.man.attempts(c["id"]) == 0:
            out.append(c)
    return out


def s3(ctx):
    generate_many(ctx, pending(ctx))


def to_gate(ctx):
    return [c["id"] for c in ctx.spec["concepts"]
            if (ctx.project / "out" / f"{c['id']}.png").exists()
            and (ctx.man.get(c["id"]) or {}).get("status") in ("generated", "passed", None)]


def s4(ctx):
    ids = to_gate(ctx)
    f = apply_gate_result(ctx, ids)
    print(f"  검사 {len(ids)}장, 불합격 {len(f)}장")


def retryable(ctx):
    return [c for c in ctx.spec["concepts"]
            if (ctx.man.get(c["id"]) or {}).get("status") in ("gate_failed", "gen_failed")
            and ctx.man.attempts(c["id"]) <= MAX_RETRY]


def s5(ctx):
    for rnd in range(1, MAX_RETRY + 1):
        todo = retryable(ctx)
        if not todo:
            break
        print(f"  재시도 {rnd}회차 {len(todo)}장")
        generate_many(ctx, todo)
        apply_gate_result(ctx, [c["id"] for c in todo if (ctx.project / "out" / f"{c['id']}.png").exists()])
    left = [c["id"] for c in ctx.spec["concepts"]
            if (ctx.man.get(c["id"]) or {}).get("status") in ("gate_failed", "gen_failed")]
    for i in left:
        ctx.man.append(i, "exhausted", stage="S5", attempt=ctx.man.attempts(i), note="재시도 상한 도달")
    ctx.exhausted = left
    if left:
        (ctx.project / "qc").mkdir(exist_ok=True)
        (ctx.project / "qc" / "failed.md").write_text("재시도 상한 도달, 납품 제외:\n" + "\n".join(f"- {i}" for i in left) + "\n", encoding="utf-8")
        print(f"  최종 실패 {left}")


def s6(ctx):
    from PIL import Image
    out = ctx.project / "out"
    passed = [c["id"] for c in ctx.spec["concepts"] if (ctx.man.get(c["id"]) or {}).get("status") == "passed"]
    qc = ctx.project / "qc"; qc.mkdir(exist_ok=True)
    # 시트는 통과분만: 임시 폴더에 링크하지 않고 out 에 통과분만 남아 있음(불합격은 qc/rejected 로 이동됨)
    n = sheet.make(out, int(ctx.spec.get("sheet_cols", 6)), qc / "sheet.jpg", qc / "sheet.md", ctx.project / "spec.json")
    print(f"  시트 {n}장 -> qc/sheet.jpg, 순서 qc/sheet.md")
    need_approval(ctx, "C", f"최종 시트 확인: {qc}/sheet.jpg")
    ex = ctx.project / "export"; ex.mkdir(exist_ok=True)
    rows = []
    for i in passed:
        im = Image.open(out / f"{i}.png")
        im.save(ex / f"{ctx.spec['name']}_{i}.png", dpi=(300, 300))
        rows.append(f"| {i} | {im.size[0]}x{im.size[1]} | {im.size[0]/300*2.54:.1f} x {im.size[1]/300*2.54:.1f} cm |")
    (ex / "DELIVERY.md").write_text(
        f"# {ctx.spec['name']} 납품\n\n납품 {len(passed)}장, 제외 {len(getattr(ctx, 'exhausted', []))}장\n\n"
        "내장 이미지 도구는 크기 인자가 없어 장당 1254~1536px 근처입니다. 300dpi 인쇄 크기는 아래 표와 같고, 더 크게 뽑으면 해상도가 떨어집니다. 임의 업스케일은 하지 않았습니다.\n\n"
        "| id | 픽셀 | 300dpi 인쇄 크기 |\n|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"  납품 {len(passed)}장 -> export/")


FUNCS = {"S0": s0, "S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5, "S6": s6}


# ---------- 내장 도구 순차 호출 모드 ----------
def cmd_next(ctx):
    for c in ctx.spec["concepts"]:
        st = ctx.man.get(c["id"])
        if not (ctx.project / "out" / f"{c['id']}.png").exists() and not (st and st["status"] == "exhausted"):
            j = make_job(ctx, c)
            print(json.dumps({"done": False, "id": c["id"], "prompt": j["prompt"], "refs": j["refs"],
                              "transparent_background": j["transparent"], "ingest_with":
                              f"python3 {Path(__file__)} {ctx.project} --ingest {c['id']} --file <생성된 PNG 경로>"},
                             ensure_ascii=False, indent=1))
            return 0
    print(json.dumps({"done": True, "next": f"python3 {Path(__file__)} {ctx.project} --from S4 --yes"}))
    return 0


def cmd_ingest(ctx, i, file, tid):
    if not any(c["id"] == i for c in ctx.spec["concepts"]):
        raise Stop(4, f"{i} 는 concepts 에 없음")
    src = Path(file)
    if not src.exists():
        raise Stop(4, f"파일 없음: {src}")
    dst = ctx.project / "out" / f"{i}.png"; dst.parent.mkdir(exist_ok=True)
    shutil.move(str(src), dst)
    if ctx.spec.get("transparent", True):
        postprocess.clean_alpha(str(dst))
    ctx.man.append(i, "generated", stage="S3", attempt=ctx.man.attempts(i) + 1, provider="codex-inline",
                   thread_id=tid or "", path=f"out/{i}.png", note="내장 도구 순차 호출")
    print(f"등록 {i}")
    return 0


# ---------- 메인 ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--from", dest="frm", choices=STAGES)
    ap.add_argument("--approve", default="")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--provider")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--doctor", action="store_true")
    ap.add_argument("--cleanup", action="store_true")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--ingest")
    ap.add_argument("--file")
    ap.add_argument("--thread-id")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    try:
        if SKILL_DIR in project.parents or project == SKILL_DIR:
            raise Stop(4, "작업 폴더는 스킬 폴더 밖에 두세요")
        if a.doctor:
            return doctor.main([])
        ctx = Ctx(); ctx.project, ctx.args, ctx.yes = project, a, a.yes
        ctx.man = Manifest(project); ctx.halt = ""; ctx.exhausted = []
        ctx.approved = {x.strip().upper() for x in a.approve.split(",") if x.strip()}
        for k in ctx.approved:
            ctx.man.append(f"_approve_{k}", "ok", stage="", note="cli")
        ctx.spec = load_spec(project)
        s0row = ctx.man.get("_S0")
        ctx.provider = (s0row or {}).get("provider", "")
        if a.status:
            for i, r in ctx.man.latest().items():
                print(f"{i:16} {r['stage']:3} {r['status']:12} a{r.get('attempt','')} {r.get('note','')[:80]}")
            return 0
        if a.cleanup:
            print(cleanup.run(project)); return 0
        if a.next:
            return cmd_next(ctx)
        if a.ingest:
            return cmd_ingest(ctx, a.ingest, a.file, a.thread_id)
        start = STAGES.index(a.frm) if a.frm else 0
        for st in STAGES[start:]:
            ctx.cur = st
            forced = a.frm is not None and STAGES.index(st) >= start
            if not forced and ctx.man.done(f"_{st}", "done") and st != "S0":
                print(f"[{st}] 완료됨, 건너뜀"); continue
            if st != "S0" and not ctx.provider:
                raise Stop(4, "S0 가 끝나지 않았습니다. --from S0 으로 실행")
            print(f"[{st}]", flush=True)
            FUNCS[st](ctx)
            ctx.man.append(f"_{st}", "done", stage=st, provider=ctx.provider)
        left = getattr(ctx, "exhausted", [])
        print("완료" + (f", 최종 실패 {len(left)}장 {left}" if left else ""))
        return 5 if left else 0
    except Stop as e:
        print(e.msg, file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
