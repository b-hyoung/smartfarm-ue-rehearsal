# -*- coding: utf-8 -*-
"""프레임 CSV -> OpenVDB 시퀀스 (UE Sparse Volume Texture 용).

    out/frames/<케이스>/frame_NN.csv (x,y,z m / T K / U m/s)
      -> 0.1 m 복셀 정규 격자로 평균 리샘플 (80 x 57 x 27)
      -> out/vdb/<케이스>/sf_<케이스>.NNNN.vdb
             FloatGrid "temperature"  0~1 정규화
             FloatGrid "speed"        m/s 그대로

master 브랜치 `src/pipeline/make_vdb.py` 를 팬 스터디용으로 옮긴 것이다.
바뀐 곳은 두 군데다.

1. 입력이 케이스별 폴더다. 팬 스터디는 케이스가 여럿이라 한 폴더에 섞으면 안 된다.
2. **좌표를 UE 로 되돌린다.** 팬 스터디는 CFD x = UE x − 4.0 규약을 쓴다.
   VDB 는 방 왼쪽 앞 아래 모서리를 원점으로 하는 UE 좌표라야 임포트 뒤 자리가 맞는다.

정규화: t = (T℃ − TMIN) / (TMAX − TMIN). 방 밖(반타원 바깥)은 배경 0.
복셀 트랜스폼: 1 복셀 = 10 cm(UE 단위)라 임포트 후 방 800x570x270 과 맞는다.

실행 (윈도우 파이썬엔 openvdb 가 없어 도커로 돈다)
    bash src/make_vdb.sh 05_F3
직접 돌릴 때
    python3 -m src.make_vdb --case 05_F3
"""
from __future__ import annotations

import argparse
import csv
import json
import os

import numpy as np

try:                            # pip 휠은 openvdb, 데비안 패키지는 pyopenvdb
    import openvdb
except ModuleNotFoundError:
    import pyopenvdb as openvdb

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KELVIN = 273.15
X_SHIFT = 4.0                   # CFD x + 4.0 = UE x
NX, NY, NZ = 80, 57, 27
VOXEL_CM = 10.0

_viz = json.load(open(os.path.join(REPO, "geometry.json"), encoding="utf-8")).get("viz", {})
TMIN = float(_viz.get("vdb_t_min", 18.5))
TMAX = float(_viz.get("vdb_t_max", 29.0))
DX = float(_viz.get("vdb_voxel_m", 0.1))


def load_frame(fdir, name):
    pts, T, U = [], [], []
    with open(os.path.join(fdir, name), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pts.append((float(r["x"]) + X_SHIFT, float(r["y"]), float(r["z"])))
            T.append(float(r["T"]) - KELVIN)
            U.append((float(r["Ux"]), float(r["Uy"]), float(r["Uz"])))
    return np.asarray(pts), np.asarray(T), np.asarray(U)


def bin_to_grid(pts, vals):
    """점 값들을 0.1 m 복셀에 평균으로 담는다. 빈 복셀은 NaN."""
    idx = np.floor(pts / DX).astype(int)
    ok = ((idx[:, 0] >= 0) & (idx[:, 0] < NX) &
          (idx[:, 1] >= 0) & (idx[:, 1] < NY) &
          (idx[:, 2] >= 0) & (idx[:, 2] < NZ))
    idx, vals = idx[ok], vals[ok]
    flat = (idx[:, 0] * NY + idx[:, 1]) * NZ + idx[:, 2]
    s = np.bincount(flat, weights=vals, minlength=NX * NY * NZ)
    n = np.bincount(flat, minlength=NX * NY * NZ)
    g = np.full(NX * NY * NZ, np.nan)
    nz = n > 0
    g[nz] = s[nz] / n[nz]
    return g.reshape(NX, NY, NZ)


def grid_of(arr, name):
    g = openvdb.FloatGrid()
    g.copyFromArray(arr)
    g.name = name
    g.transform = openvdb.createLinearTransform(voxelSize=VOXEL_CM)
    g.gridClass = openvdb.GridClass.FOG_VOLUME
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--frames", default=os.path.join(REPO, "out", "frames"))
    ap.add_argument("--out", default=os.path.join(REPO, "out", "vdb"))
    # 색척도는 시퀀스 내내 고정이라야 프레임끼리 비교가 된다. 자동 맞춤을 쓰지 않는다.
    # 팬 스터디는 조명 발열을 빼고 풀어서 방이 차다 — 기본 18.5~29 ℃ 로는 아래가 잘린다.
    ap.add_argument("--tmin", type=float, default=TMIN, help="색척도 하한 ℃ (기본 %.1f)" % TMIN)
    ap.add_argument("--tmax", type=float, default=TMAX, help="색척도 상한 ℃ (기본 %.1f)" % TMAX)
    a = ap.parse_args()
    tmin, tmax = a.tmin, a.tmax

    fdir = os.path.join(a.frames, a.case)
    man = json.load(open(os.path.join(fdir, "manifest.json"), encoding="utf-8"))
    outdir = os.path.join(a.out, a.case)
    os.makedirs(outdir, exist_ok=True)
    print("source:", man.get("source", "?"))
    print("색척도 %.1f ~ %.1f ℃ (시퀀스 내내 고정)" % (tmin, tmax))

    for i, fr in enumerate(man["frames"]):
        pts, T, U = load_frame(fdir, fr["file"])
        tg = bin_to_grid(pts, T)
        sg = bin_to_grid(pts, np.linalg.norm(U, axis=1))
        tn = (np.clip(tg, tmin, tmax) - tmin) / (tmax - tmin)
        tn = np.nan_to_num(tn, nan=0.0).astype(np.float32)
        sn = np.nan_to_num(sg, nan=0.0).astype(np.float32)

        path = os.path.join(outdir, "sf_%s.%04d.vdb" % (a.case, i))
        openvdb.write(path, grids=[grid_of(tn, "temperature"), grid_of(sn, "speed")])
        print("sf_%s.%04d.vdb  t=%5.0fs  채운 복셀 %d/%d  T %4.1f~%4.1f℃  |U| ~%4.2f"
              % (a.case, i, fr["time_s"], int((tn > 0).sum()), NX * NY * NZ,
                 np.nanmin(tg), np.nanmax(tg), np.nanmax(sg)))
    with open(os.path.join(outdir, "scale.json"), "w", encoding="utf-8") as f:
        json.dump({"t_min_c": tmin, "t_max_c": tmax, "voxel_cm": VOXEL_CM,
                   "dims": [NX, NY, NZ], "case": a.case,
                   "note": "temperature 는 0~1 정규화. ℃ = t_min + v * (t_max - t_min)"},
                  f, ensure_ascii=False, indent=2)
    print("VDB-DONE ->", outdir)


if __name__ == "__main__":
    main()
