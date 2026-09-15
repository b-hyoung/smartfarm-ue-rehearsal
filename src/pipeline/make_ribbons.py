"""유선(streamline) + 각 지점의 온도를 하나로 묶어 UE 반입용 파일을 만든다.

왜 필요한가
    `make_traces.py` 의 궤적에는 속도만 있고 온도가 없습니다. 그런데 보고 싶은 건
    "바람이 어디로 가서 **그 자리 온도가 어떻게 되는지**" 입니다. 둘을 한 화면에
    담으려면 궤적의 각 점에 그 자리의 T 를 실어 줘야 합니다.

    무거운 계산(89,600 점 최근접 조회)은 여기서 끝내고, UE 는 읽어서 메시만 만듭니다.
    UE 내장 파이썬에는 numpy 가 없습니다.

출력
    data/ribbons/ribbon_<frame>.csv
        pid, x, y, z, T, speed        (좌표 cm — UE 단위 그대로, T 섭씨)

실행
    py -m src.pipeline.make_ribbons            # 전 프레임
    py -m src.pipeline.make_ribbons 14         # 한 프레임만
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRAME_DIR = os.path.join(REPO, "data", "frames")
TRACE_DIR = os.path.join(REPO, "data", "traces")
OUT_DIR = os.path.join(REPO, "data", "ribbons")

N_LINES = 140          # 900개 다 그리면 화면이 뭉개진다. 읽을 수 있을 만큼만.
CELL = 0.12            # 온도 조회용 격자 (m)
KELVIN = 273.15
S = 100.0              # m -> cm


def load_frame(idx):
    """프레임의 (좌표, 온도) — 격자 해시로 최근접 조회할 수 있게."""
    pts, temps = [], []
    path = os.path.join(FRAME_DIR, "frame_%02d.csv" % idx)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pts.append((float(r["x"]), float(r["y"]), float(r["z"])))
            temps.append(float(r["T"]))
    p = np.asarray(pts)
    t = np.asarray(temps)
    if t.mean() > 200.0:          # 켈빈으로 들어온 경우
        t = t - KELVIN
    return p, t


def build_lookup(pts, temps):
    """격자 셀별 평균 온도. dict[(i,j,k)] = T"""
    key = np.floor(pts / CELL).astype(np.int64)
    # 셀 인덱스를 하나의 정수로 접어서 그룹핑
    off = key.min(axis=0)
    span = (key.max(axis=0) - off + 1)
    flat = ((key[:, 0] - off[0]) * span[1] + (key[:, 1] - off[1])) * span[2] \
        + (key[:, 2] - off[2])
    n = int(span[0] * span[1] * span[2])
    acc = np.zeros(n)
    cnt = np.zeros(n)
    np.add.at(acc, flat, temps)
    np.add.at(cnt, flat, 1.0)
    nz = cnt > 0
    acc[nz] /= cnt[nz]
    return acc, cnt, off, span


def sample_T(q, acc, cnt, off, span, fallback):
    """조회점 q(N,3) 의 온도. 빈 셀은 이웃(3x3x3)까지 넓혀 찾고, 그래도 없으면 fallback."""
    out = np.full(len(q), np.nan)
    base = np.floor(q / CELL).astype(np.int64) - off

    def gather(shift):
        k = base + shift
        ok = np.all((k >= 0) & (k < span), axis=1)
        idx = np.full(len(q), -1, dtype=np.int64)
        if ok.any():
            kk = k[ok]
            idx[ok] = (kk[:, 0] * span[1] + kk[:, 1]) * span[2] + kk[:, 2]
        return idx

    todo = np.ones(len(q), dtype=bool)
    for shift in [(0, 0, 0)] + [(a, b, c)
                                for a in (-1, 0, 1)
                                for b in (-1, 0, 1)
                                for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]:
        if not todo.any():
            break
        idx = gather(np.asarray(shift))
        hit = todo & (idx >= 0)
        if hit.any():
            v = np.where(idx[hit] >= 0, cnt[idx[hit]], 0.0) > 0
            sel = np.nonzero(hit)[0][v]
            out[sel] = acc[idx[sel]]
            todo[sel] = False
    out[np.isnan(out)] = fallback
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = [int(sys.argv[1])] if len(sys.argv) > 1 else list(range(15))
    for i in frames:
        tp = os.path.join(TRACE_DIR, "trace_%02d.csv" % i)
        if not os.path.isfile(tp) or os.path.getsize(tp) < 1000:
            print("trace_%02d.csv 없음/비어있음 — 건너뜀" % i)
            continue

        rows = []
        with open(tp, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append((int(r["pid"]), int(r["step"]),
                             float(r["x"]), float(r["y"]), float(r["z"]),
                             float(r["speed"])))
        pids = sorted({r[0] for r in rows})
        keep = set(pids[::max(1, len(pids) // N_LINES)][:N_LINES])
        rows = [r for r in rows if r[0] in keep]
        rows.sort(key=lambda r: (r[0], r[1]))

        pts, tmp, off, span = None, None, None, None
        fpts, ftemp = load_frame(i)
        acc, cnt, off, span = build_lookup(fpts, ftemp)

        q = np.asarray([[r[2], r[3], r[4]] for r in rows])
        T = sample_T(q, acc, cnt, off, span, float(np.median(ftemp)))

        out = os.path.join(OUT_DIR, "ribbon_%02d.csv" % i)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["pid", "x", "y", "z", "T", "speed"])
            for (pid, _s, x, y, z, sp), t in zip(rows, T):
                w.writerow([pid, "%.1f" % (x * S), "%.1f" % (y * S),
                            "%.1f" % (z * S), "%.2f" % t, "%.3f" % sp])
        print("ribbon_%02d.csv  유선 %d개 · 점 %d개 · T %.1f~%.1f C  %.1f MB"
              % (i, len(keep), len(rows), T.min(), T.max(),
                 os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
