"""frames CSV -> OpenVDB 볼륨 시퀀스 (UE Sparse Volume Texture 용).

    data/frames/frame_NN.csv (x,y,z m / T K)
      -> 0.1 m 복셀 정규 격자로 평균 리샘플 (80 x 57 x 27)
      -> out/vdb/sf_temp.NNNN.vdb   FloatGrid "temperature" (0~1 정규화)
                                    FloatGrid "speed"       (m/s)

정규화: t = (T℃ − TMIN) / (TMAX − TMIN), 방 밖(D자 바깥)은 배경 0.
  TMIN/TMAX 는 웹·UE 색척도와 같은 18.5~29.0 — 머티리얼에서 그대로 온도로 역산 가능.
복셀 트랜스폼: 1 복셀 = 10 cm (UE 단위). 인덱스 (0,0,0) 복셀 중심 = (5,5,5) cm.
  UE 임포트 후 볼륨 스케일 조정 없이 방(800x570x270)과 맞는다.

실행 (Windows python 엔 openvdb 가 없어서 도커):
    wsl docker run --rm -v /mnt/c/.../smartfarm-ue-rehearsal:/work -w /work \
        debian:bookworm-slim bash -c \
        "apt-get -qq update && apt-get -qq install -y python3-openvdb python3-numpy \
         && python3 src/pipeline/make_vdb.py"
"""
from __future__ import annotations

import csv
import json
import os

import numpy as np

try:                            # pip 휠은 openvdb, 데비안 패키지는 pyopenvdb
    import openvdb
except ModuleNotFoundError:
    import pyopenvdb as openvdb

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "out", "vdb")
KELVIN = 273.15
# 정규화·복셀 단일 출처: geometry.json viz
_viz = json.load(open(os.path.join(REPO, "geometry.json"), encoding="utf-8")).get("viz", {})
TMIN = float(_viz.get("vdb_t_min", 18.5))
TMAX = float(_viz.get("vdb_t_max", 29.0))
DX = float(_viz.get("vdb_voxel_m", 0.1))
NX, NY, NZ = 80, 57, 27
# 복셀 10 = UE 단위(cm). SVT FrameTransform 으로 들어가 [0..800,0..570,0..270]에
# 정착한다. ⚠ 컴포넌트의 FrameTransform 동기화는 **재생 틱에서만** 일어난다
# (엔진 소스 HeterogeneousVolumeComponent.cpp 696행) — 에디터에서 갓 임포트하면
# 1/10 크기로 보이다가, 시퀀서 재생/PIE 한 번이면 방 크기로 맞는다. 액터는 identity.
VOXEL_CM = 10.0


def load_frame(idx):
    path = os.path.join(REPO, "data", "frames", "frame_%02d.csv" % idx)
    pts, T, U = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pts.append((float(r["x"]), float(r["y"]), float(r["z"])))
            T.append(float(r["T"]) - KELVIN)
            U.append((float(r["Ux"]), float(r["Uy"]), float(r["Uz"])))
    return np.asarray(pts), np.asarray(T), np.asarray(U)


def bin_to_grid(pts, vals):
    """셀 값들을 0.1 m 복셀에 평균으로 담는다. 빈 복셀은 NaN."""
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


def main():
    os.makedirs(OUT, exist_ok=True)
    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    print("source:", man.get("source", "?"))
    for f in range(len(man["frames"])):
        pts, T, U = load_frame(f)
        tg = bin_to_grid(pts, T)
        sg = bin_to_grid(pts, np.linalg.norm(U, axis=1))
        # 정규화, 방 밖(NaN)은 배경 0
        tn = (np.clip(tg, TMIN, TMAX) - TMIN) / (TMAX - TMIN)
        tn = np.nan_to_num(tn, nan=0.0).astype(np.float32)
        sn = np.nan_to_num(sg, nan=0.0).astype(np.float32)

        grid_t = openvdb.FloatGrid()
        grid_t.copyFromArray(tn)
        grid_t.name = "temperature"
        grid_t.transform = openvdb.createLinearTransform(voxelSize=VOXEL_CM)
        grid_t.gridClass = openvdb.GridClass.FOG_VOLUME

        grid_s = openvdb.FloatGrid()
        grid_s.copyFromArray(sn)
        grid_s.name = "speed"
        grid_s.transform = openvdb.createLinearTransform(voxelSize=VOXEL_CM)
        grid_s.gridClass = openvdb.GridClass.FOG_VOLUME

        path = os.path.join(OUT, "sf_temp.%04d.vdb" % f)
        openvdb.write(path, grids=[grid_t, grid_s])
        filled = int((tn > 0).sum())
        print("sf_temp.%04d.vdb  t=%4.0fs  채운 복셀 %d/%d  T %4.1f~%4.1f℃"
              % (f, man["frames"][f]["time_s"], filled, NX * NY * NZ,
                 np.nanmin(tg), np.nanmax(tg)))
    print("VDB-DONE ->", OUT)


if __name__ == "__main__":
    main()
