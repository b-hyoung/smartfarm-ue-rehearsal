"""OpenFOAM probes 원본 → A/B/C/D 지점 온도 시계열.

이게 **실측과 맞대볼 기준값**이다. 화면의 색은 셀 평균을 거친 값이지만,
probes 는 솔버가 그 좌표에서 직접 뽑은 값이라 중간 가공이 없다.

    A  UE(4.0, 2.0)   에어컨 바로 아래
    B  UE(7.5, 0.8)   평벽 쪽 오른쪽
    C  UE(4.0, 4.5)   반원 안쪽 (정체 구역)
    D  UE(0.5, 0.8)   평벽 쪽 왼쪽 (B 와 대칭)

    높이 0.1 / 1.1 / 1.7 m — 1.1 m 가 기본(서 있을 때 몸통 높이)

입력  data/_probes_T.raw, _probes_U.raw   (wsl 케이스에서 복사)
출력  data/probes.csv                     t, 지점, 높이, T(℃), |U|(m/s)

실행  py -m src.pipeline.make_probes
"""
from __future__ import annotations

import csv
import math
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KELVIN = 273.15
X_SHIFT = 4.0          # CFD x + 4.0 = UE x

# CFD 좌표 -> 지점 이름
NAMES = {(0.0, 2.0): "A", (3.5, 0.8): "B", (0.0, 4.5): "C", (-3.5, 0.8): "D"}


def parse_header(path):
    """# Probe i (x y z) 줄에서 좌표를 읽는다."""
    cols = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"):
                break
            m = re.match(r"#\s*Probe\s+(\d+)\s+\(([^)]*)\)", line)
            if m:
                x, y, z = (float(v) for v in m.group(2).split())
                cols.append((int(m.group(1)), x, y, z))
    return cols


def read_scalar(path):
    """시각 -> [프로브별 값]. 헤더(#)는 건너뛴다."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.split()
            if len(p) < 2:
                continue
            out.append((float(p[0]), [float(v) for v in p[1:]]))
    return out


def read_vector(path):
    """U 는 (ux uy uz) 튜플이 나열된다 → 크기로 환산."""
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            nums = [float(v) for v in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?",
                                                 line)]
            if len(nums) < 4:
                continue
            t, rest = nums[0], nums[1:]
            mags = [math.sqrt(rest[i] ** 2 + rest[i + 1] ** 2 + rest[i + 2] ** 2)
                    for i in range(0, len(rest) - 2, 3)]
            out.append((t, mags))
    return out


def main():
    tp = os.path.join(REPO, "data", "_probes_T.raw")
    up = os.path.join(REPO, "data", "_probes_U.raw")
    cols = parse_header(tp)
    Ts = read_scalar(tp)
    Us = read_vector(up) if os.path.isfile(up) else []
    umap = {round(t, 3): m for t, m in Us}

    out = os.path.join(REPO, "data", "probes.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "point", "ue_x", "ue_y", "z", "T_C", "U_mag"])
        for t, vals in Ts:
            mags = umap.get(round(t, 3), [])
            for (i, x, y, z) in cols:
                name = NAMES.get((round(x, 3), round(y, 3)))
                if name is None or i >= len(vals):
                    continue
                u = mags[i] if i < len(mags) else ""
                w.writerow(["%.2f" % t, name, "%.2f" % (x + X_SHIFT),
                            "%.2f" % y, "%.2f" % z,
                            "%.3f" % (vals[i] - KELVIN),
                            "%.4f" % u if u != "" else ""])

    # 요약 — 1.1 m 기준
    print("지점별 1.1 m 온도 (℃)")
    print("  t(s)      A       B       C       D")
    rows = {}
    for t, vals in Ts:
        for (i, x, y, z) in cols:
            n = NAMES.get((round(x, 3), round(y, 3)))
            if n and abs(z - 1.1) < 1e-6:
                rows.setdefault(round(t), {})[n] = vals[i] - KELVIN
    for t in [0, 60, 130, 190, 260, 390, 510, 640, 770, 900]:
        near = min(rows, key=lambda k: abs(k - t))
        r = rows[near]
        print("%6d  %6.2f  %6.2f  %6.2f  %6.2f"
              % (near, r.get("A", 0), r.get("B", 0), r.get("C", 0), r.get("D", 0)))
    print("-> %s  (%d행)" % (out, sum(1 for _ in open(out, encoding="utf-8")) - 1))


if __name__ == "__main__":
    main()
