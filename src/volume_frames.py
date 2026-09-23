# -*- coding: utf-8 -*-
"""volumeGrid 수평면 raw -> VDB 입력용 프레임 CSV.

    <케이스>/postProcessing/volumeGrid/<시각>/{U,T}_zNNN.raw
      -> out/frames/<케이스>/frame_NN.csv   (x,y,z,T,Ux,Uy,Uz)
         out/frames/<케이스>/manifest.json

src/make_vdb.py 가 이 폴더를 그대로 읽는다. 열 이름은 master 브랜치의
data/frames 규약과 같게 맞췄다 — 온도는 켈빈이다.

실행  py -m src.volume_frames --case 05_F3
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ROOT = os.path.join(os.path.expanduser("~"), "smartfarm-cfd", "cases", "fan-study")


def read_raw(path, ncol):
    """raw 한 장 -> {(x,y,z): 값들}. 주석 줄과 빈 줄은 버린다."""
    out = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip() or line[0] == "#":
                continue
            p = line.split()
            if len(p) < 3 + ncol:
                continue
            key = (round(float(p[0]), 4), round(float(p[1]), 4), round(float(p[2]), 4))
            out[key] = tuple(float(v) for v in p[3:3 + ncol])
    return out


def times_of(vdir):
    ts = []
    for d in os.listdir(vdir):
        try:
            ts.append((float(d), d))
        except ValueError:
            pass
    return [d for _, d in sorted(ts)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--out", default=os.path.join(REPO, "out", "frames"))
    ap.add_argument("--from-time", type=float, default=300.0,
                    help="이 시각 이상만 프레임으로 쓴다 (기본 300 s — 채점 창 시작)")
    a = ap.parse_args()

    case = a.case if os.path.isdir(a.case) else os.path.join(a.root, a.case)
    rid = os.path.basename(case.rstrip("/\\"))
    vdir = os.path.join(case, "postProcessing", "volumeGrid")
    if not os.path.isdir(vdir):
        raise SystemExit("volumeGrid 가 없다. 먼저: bash src/export_volume.sh " + rid)

    outdir = os.path.join(a.out, rid)
    os.makedirs(outdir, exist_ok=True)

    frames, n = [], 0
    for tdir in times_of(vdir):
        if float(tdir) < a.from_time:
            continue
        src = os.path.join(vdir, tdir)
        planes = sorted(set(re.sub(r"^[UT]_", "", f)
                            for f in os.listdir(src) if f.endswith(".raw")))
        rows = 0
        path = os.path.join(outdir, "frame_%02d.csv" % n)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["x", "y", "z", "T", "Ux", "Uy", "Uz"])
            for pl in planes:
                fu = os.path.join(src, "U_" + pl)
                ft = os.path.join(src, "T_" + pl)
                if not (os.path.exists(fu) and os.path.exists(ft)):
                    continue
                U, T = read_raw(fu, 3), read_raw(ft, 1)
                for key, u in U.items():
                    t = T.get(key)
                    if t is None:
                        continue
                    w.writerow(["%.4f" % key[0], "%.4f" % key[1], "%.4f" % key[2],
                                "%.3f" % t[0], "%.4f" % u[0], "%.4f" % u[1], "%.4f" % u[2]])
                    rows += 1
        frames.append({"time_s": float(tdir), "points": rows,
                       "file": "frame_%02d.csv" % n})
        print("frame_%02d.csv  t=%6.1f s  점 %d" % (n, float(tdir), rows))
        n += 1

    if not frames:
        raise SystemExit("쓸 시각이 없다 (--from-time %.0f 이상)" % a.from_time)

    man = {"source": "%s · OpenFOAM volumeGrid 수평면 27 장" % rid,
           "case": rid, "frames": frames,
           "note": "T 는 켈빈, U 는 m/s. 좌표는 CFD 좌표(UE x − 4.0)."}
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
    print("\n-> %s  프레임 %d" % (outdir, len(frames)))
    print("다음: bash src/make_vdb.sh %s" % rid)


if __name__ == "__main__":
    main()
