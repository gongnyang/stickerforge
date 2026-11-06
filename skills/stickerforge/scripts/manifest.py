#!/usr/bin/env python3
"""manifest.jsonl 원장. 행 단위 추가만 한다. 같은 id는 마지막 행이 현재 상태.
CLI: manifest.py <projectDir>  현재 상태 요약 출력."""
import json, sys, time
from pathlib import Path


class Manifest:
    def __init__(self, project):
        self.path = Path(project) / "manifest.jsonl"

    def append(self, id, status, stage="", **extra):
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "id": id, "stage": stage, "status": status}
        row.update(extra)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
        return row

    def rows(self):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # 쓰다 끊긴 마지막 줄은 무시
        return out

    def latest(self):
        cur = {}
        for r in self.rows():
            cur[r["id"]] = r
        return cur

    def get(self, id):
        return self.latest().get(id)

    def done(self, id, status="done"):
        r = self.get(id)
        return bool(r and r["status"] == status)

    def attempts(self, id):
        return max([r.get("attempt", 0) for r in self.rows() if r["id"] == id] or [0])

    def thread_ids(self):
        return sorted({r["thread_id"] for r in self.rows() if r.get("thread_id")})


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    for i, r in Manifest(sys.argv[1]).latest().items():
        print(f"{i:20} {r['stage']:3} {r['status']:14} {r.get('note','')}")
