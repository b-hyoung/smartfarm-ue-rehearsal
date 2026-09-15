"""보존 데이터셋을 작업본으로 복원 — 원커맨드.

    py -m src.pipeline.restore vane25     # 진짜 CFD (4방향 25° 측면취출) ← 기준
    py -m src.pipeline.restore vert       # 구버전 CFD (수직취출)

하는 일
    data/archive/<이름>/{frames,jets,slices,probes.csv} -> data/ 복사
    -> 웹 미리보기(out/web/index.html) 재생성
    -> UE 재빌드 명령 안내 (에디터가 떠 있어야 함)

[SF 갱신](임시 수식)으로 화면을 덮은 뒤 진짜 CFD 로 되돌릴 때 쓴다.
2026-09-15 "지금 화면이 뭐냐" 혼선의 재발 방지책: manifest.json 의
source 필드가 항상 출처를 말해준다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVE = os.path.join(REPO, "data", "archive")


def restore(name):
    src = os.path.join(ARCHIVE, name)
    if not os.path.isdir(src):
        names = ", ".join(sorted(os.listdir(ARCHIVE))) if os.path.isdir(ARCHIVE) else "-"
        raise SystemExit("데이터셋 '%s' 없음. 보유: %s" % (name, names))

    for d in ("frames", "jets", "slices"):
        sp = os.path.join(src, d)
        if not os.path.isdir(sp):
            print("  (%s 없음 — 건너뜀)" % d)
            continue
        dp = os.path.join(REPO, "data", d)
        os.makedirs(dp, exist_ok=True)
        n = 0
        for f in os.listdir(sp):
            shutil.copy2(os.path.join(sp, f), os.path.join(dp, f))
            n += 1
        print("  %s: %d개 복사" % (d, n))
    pp = os.path.join(src, "probes.csv")
    if os.path.isfile(pp):
        shutil.copy2(pp, os.path.join(REPO, "data", "probes.csv"))
        print("  probes.csv 복사")

    man = os.path.join(REPO, "data", "frames", "manifest.json")
    source = json.load(open(man, encoding="utf-8")).get("source", "?")
    print("복원 완료 — source: %s" % source)

    print("웹 재생성 중...")
    subprocess.run([sys.executable, "-m", "src.pipeline.make_web"], cwd=REPO, check=True)

    print("\nUE 반영 (에디터 켠 상태에서):")
    print("  py ue/ue_exec.py -f ue/sf_sequencer2.py     # 30배속 (data/_seq.json 확인)")
    print("  또는 툴바 [SF 갱신] 은 임시 수식이니 누르면 다시 덮인다는 것 주의")


if __name__ == "__main__":
    restore(sys.argv[1] if len(sys.argv) > 1 else "vane25")
