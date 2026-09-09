"""CFD 속도장 → .fga (Fluid Grid ASCII) 로 내보낸다. — Niagara 경로

왜 .fga 인가
    Niagara 시스템 자체를 파이썬으로 저작할 수는 없지만,
    **VectorField 에셋은 .fga 파일로 임포트할 수 있고**(VectorFieldStaticFactory),
    엔진에 그것을 시각화하는 Niagara 시스템이 이미 들어 있습니다
    (/Niagara/VectorFields/VectorFieldVisualizationSystem).
    → 파이썬만으로 '진짜 Niagara' 파티클을 CFD 속도장으로 흐르게 할 수 있습니다.

FGA 포맷 (Epic 정의)
    줄1: sizeX, sizeY, sizeZ,
    줄2: minX, minY, minZ,
    줄3: maxX, maxY, maxZ,
    줄4: vx,vy,vz, vx,vy,vz, ...   (x 가 가장 빠르게, 그다음 y, 그다음 z)
    좌표/속도는 UE 단위(cm) 기준으로 씁니다.

실행
    py -m src.make_fga            # 전 프레임
    py -m src.make_fga 14         # 한 프레임
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_DIR = os.path.join(REPO, "data", "frames")
OUT_DIR = os.path.join(REPO, "data", "fga")

LX, LY, LZ = 8.0, 5.7, 2.7      # m (UE 좌표계, x 0~8)
CX = LX / 2.0
S = 100.0                        # m -> cm

# 격자 해상도 — 방 종횡비(3:2:1)에 맞춤. 너무 키우면 파일이 커진다.
NX, NY, NZ = 48, 34, 16


def in_room(x, y):
    return ((x - CX) / CX) ** 2 + (y / LY) ** 2 <= 1.0


def load(idx):
    xs, vs = [], []
    with open(os.path.join(FRAME_DIR, "frame_%02d.csv" % idx),
              newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            xs.append((float(r["x"]), float(r["y"]), float(r["z"])))
            vs.append((float(r["Ux"]), float(r["Uy"]), float(r["Uz"])))
    return np.asarray(xs), np.asarray(vs)


def resample(pts, vel):
    """산재한 CFD 점 → 균일 격자. 셀 평균, 빈 셀은 0."""
    gx = np.linspace(0.0, LX, NX)
    gy = np.linspace(0.0, LY, NY)
    gz = np.linspace(0.0, LZ, NZ)
    dx, dy, dz = LX / (NX - 1), LY / (NY - 1), LZ / (NZ - 1)

    ix = np.clip(np.round(pts[:, 0] / dx).astype(int), 0, NX - 1)
    iy = np.clip(np.round(pts[:, 1] / dy).astype(int), 0, NY - 1)
    iz = np.clip(np.round(pts[:, 2] / dz).astype(int), 0, NZ - 1)
    flat = (iz * NY + iy) * NX + ix

    acc = np.zeros((NX * NY * NZ, 3))
    cnt = np.zeros(NX * NY * NZ)
    np.add.at(acc, flat, vel)
    np.add.at(cnt, flat, 1.0)
    nz = cnt > 0
    acc[nz] /= cnt[nz][:, None]

    # 방 밖(타원 바깥) 셀은 0 으로 — 파티클이 벽 밖으로 새지 않게
    XX, YY = np.meshgrid(gx, gy, indexing="xy")
    mask2d = np.array([[in_room(x, y) for x in gx] for y in gy])
    mask = np.repeat(mask2d.reshape(1, NY, NX), NZ, axis=0).reshape(-1)
    acc[~mask] = 0.0
    return acc, cnt, mask


def write_fga(path, vec):
    """UE 단위(cm)로 기록. 속도도 cm/s 로 환산."""
    with open(path, "w", encoding="ascii") as f:
        f.write("%d,%d,%d,\n" % (NX, NY, NZ))
        f.write("%.4f,%.4f,%.4f,\n" % (0.0, 0.0, 0.0))
        f.write("%.4f,%.4f,%.4f,\n" % (LX * S, LY * S, LZ * S))
        parts = []
        for v in vec:
            parts.append("%.4f,%.4f,%.4f" % (v[0] * S, v[1] * S, v[2] * S))
        f.write(",".join(parts))
        f.write(",\n")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = [int(sys.argv[1])] if len(sys.argv) > 1 else list(range(15))
    for i in frames:
        pts, vel = load(i)
        vec, cnt, mask = resample(pts, vel)
        out = os.path.join(OUT_DIR, "flow_%02d.fga" % i)
        write_fga(out, vec)
        spd = np.linalg.norm(vec, axis=1)
        print("flow_%02d.fga  %dx%dx%d  채워진 셀 %d/%d  |v|max %.3f m/s  %.1f MB"
              % (i, NX, NY, NZ, int((cnt > 0).sum()), NX * NY * NZ,
                 spd.max(), os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
