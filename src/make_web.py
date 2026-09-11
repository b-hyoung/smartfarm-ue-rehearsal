"""웹 미리보기 데이터 패킹 — web/template.html + 데이터 JSON -> out/web/index.html

왜 웹인가
    UE 3D 씬은 단면·유선·화살표가 한 원근에 겹쳐서 서로를 가린다(사용자 지적).
    웹 2D는 레이어를 분리한다: 온도만 항상 켜고, 바람은 토글로 뺀다.

입력
    data/slices/slice_NN.csv    수평 1.1 m 온도 격자 (ix,iy,x,y,T / m,섭씨)
    data/slices/vslice_NN.csv   수직 y=2.0 m 온도 격자 (ix,iz,x,z,T)
    data/arrows/arrow_NN.csv    바람 글리프 (x,y,z,ux,uy,uz,speed,T / cm)
    data/probes.csv             A/B/C/D 시계열 (0.64 s 간격)
    data/frames/manifest.json   프레임 -> 실제 시각(초)

출력
    out/web/index.html          자급자족 단일 파일 (데이터 인라인)

실행
    py -m src.make_web
"""
from __future__ import annotations

import csv
import json
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "out", "web")
N_FRAMES = 15

# 웹에 15프레임 x 5,639셀을 다 실으면 좌표가 중복이라 낭비다.
# 격자(ix,iy -> x,y)는 한 번만 싣고, 프레임은 T 배열만 싣는다.
# T 는 0.01K 정수(센티켈빈)로 실어 JSON 크기를 절반으로 줄인다.


def load_grid(path_fmt, ij_keys, xy_keys):
    """프레임 공통 격자 + 프레임별 T 배열.

    반환: {"nx","ny","cells":[[i,j,x,y],...], "T": [[...frame0], ...]}
    cells 순서가 곧 T 배열 순서다.
    """
    ik, jk = ij_keys
    xk, yk = xy_keys
    order = None      # [(i,j), ...] 프레임 0 기준
    cells = []
    frames_T = []
    for f in range(N_FRAMES):
        path = path_fmt % f
        with open(path, newline="", encoding="utf-8") as fp:
            rows = list(csv.DictReader(fp))
        if order is None:
            order = [(int(r[ik]), int(r[jk])) for r in rows]
            # ⚠ slice CSV 좌표는 cm 다 (UE 단위 그대로). 웹은 m 로 통일.
            cells = [[int(r[ik]), int(r[jk]),
                      round(float(r[xk]) / 100, 3), round(float(r[yk]) / 100, 3)]
                     for r in rows]
        else:
            got = [(int(r[ik]), int(r[jk])) for r in rows]
            if got != order:
                raise SystemExit("%s: 격자가 프레임 0 과 다르다" % path)
        frames_T.append([int(round(float(r["T"]) * 100)) for r in rows])
    nx = max(c[0] for c in cells) + 1
    ny = max(c[1] for c in cells) + 1
    return {"nx": nx, "ny": ny, "cells": cells, "T": frames_T}


def load_probes():
    """z=1.1 m 만. {"pos": {pt:[x,y]}, "t": [...], "T": {pt: [...]}}

    0.64 s 간격 781 스텝은 곡선용으로 과하다 -> 4스텝(2.56 s)마다 하나.
    """
    path = os.path.join(REPO, "data", "probes.csv")
    pos = {}
    series = {}
    with open(path, newline="", encoding="utf-8") as fp:
        for r in csv.DictReader(fp):
            if abs(float(r["z"]) - 1.1) > 1e-6:
                continue
            pt = r["point"]
            pos.setdefault(pt, [float(r["ue_x"]), float(r["ue_y"])])
            series.setdefault(pt, []).append(
                (float(r["t_s"]), float(r["T_C"])))
    pts = sorted(series)
    t0 = [t for t, _ in series[pts[0]]][::4]
    T = {p: [round(v, 2) for _, v in series[p]][::4] for p in pts}
    return {"pos": pos, "t": [round(t, 1) for t in t0], "T": T}


def load_arrows():
    """프레임별 [x, y, ux, uy, speed]. z 는 1.1 m 층만 (위에서 본 그림이니까)."""
    frames = []
    for f in range(N_FRAMES):
        path = os.path.join(REPO, "data", "arrows", "arrow_%02d.csv" % f)
        rows = []
        if os.path.isfile(path):
            with open(path, newline="", encoding="utf-8") as fp:
                for r in csv.DictReader(fp):
                    if abs(float(r["z"]) - 110.0) > 1.0:
                        continue
                    rows.append([round(float(r["x"]) / 100, 2),
                                 round(float(r["y"]) / 100, 2),
                                 round(float(r["ux"]), 3),
                                 round(float(r["uy"]), 3),
                                 round(float(r["speed"]), 3)])
        frames.append(rows)
    return frames


def main():
    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    times = [float(m["time_s"]) for m in man["frames"]][:N_FRAMES]

    hs = load_grid(os.path.join(REPO, "data", "slices", "slice_%02d.csv"),
                   ("ix", "iy"), ("x", "y"))
    vs = load_grid(os.path.join(REPO, "data", "slices", "vslice_%02d.csv"),
                   ("ix", "iz"), ("x", "z"))
    probes = load_probes()
    arrows = load_arrows()

    allT = [t for fr in hs["T"] for t in fr] + [t for fr in vs["T"] for t in fr]
    tmin, tmax = min(allT) / 100.0, max(allT) / 100.0
    # 색 척도는 0.5K 격자에 스냅한 고정 범위 (프레임마다 바꾸면 애니가 거짓말)
    dmin = math.floor(tmin * 2) / 2
    dmax = math.ceil(tmax * 2) / 2

    data = {
        "meta": {
            "solver": man.get("solver", ""),
            "source": man.get("source", ""),
            "room": man["room_m"],
            "ac": man["ac"]["centre_ue_m"][:2],
            "times": times,
            "domain": [dmin, dmax],
            "data_minmax": [round(tmin, 2), round(tmax, 2)],
        },
        "hslice": hs,
        "vslice": vs,
        "probes": probes,
        "arrows": arrows,
    }
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    tpl_path = os.path.join(REPO, "web", "template.html")
    with open(tpl_path, encoding="utf-8") as fp:
        tpl = fp.read()
    if "__SF_DATA__" not in tpl:
        raise SystemExit("template.html 에 __SF_DATA__ 자리표시자가 없다")
    html = tpl.replace("__SF_DATA__", blob)

    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, "index.html")
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(html)
    print("SF_WEB: %s  (%.1f MB, T범위 %.2f~%.2f, 척도 %.1f~%.1f)" %
          (out_path, len(html) / 1e6, tmin, tmax, dmin, dmax))


if __name__ == "__main__":
    main()
