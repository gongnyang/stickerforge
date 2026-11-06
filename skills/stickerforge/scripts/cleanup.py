#!/usr/bin/env python3
"""이 프로젝트가 만든 codex 스레드의 롤아웃과 빈 이미지 폴더만 지운다.
대상은 manifest.jsonl 에 기록된 thread_id 뿐이다. 다른 스레드 파일은 건드리지 않는다.
사용: cleanup.py <projectDir> [--dry-run] [--keep-minutes 2]"""
import os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import Manifest


def run(project, dry=False, keep_min=2.0):
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    ids = Manifest(project).thread_ids()
    n = nbytes = dirs = 0
    now = time.time()
    for t in ids:
        if not t or "/" in t or ".." in t:
            continue
        for r in (home / "sessions").glob(f"*/*/*/*{t}.jsonl"):
            if now - r.stat().st_mtime > keep_min * 60:  # 쓰는 중인 파일은 건너뛴다
                nbytes += r.stat().st_size; n += 1
                if not dry:
                    r.unlink()
        d = home / "generated_images" / t
        if d.is_dir() and now - d.stat().st_mtime > keep_min * 60:
            for p in list(d.glob("*")):
                nbytes += p.stat().st_size
                if not dry:
                    p.unlink()
            dirs += 1
            if not dry:
                d.rmdir()
    return {"threads": len(ids), "rollouts": n, "image_dirs": dirs, "mb": round(nbytes / 1e6, 1), "dry_run": dry}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    km = float(a[a.index("--keep-minutes") + 1]) if "--keep-minutes" in a else 2.0
    print(run(a[0], "--dry-run" in a, km))
