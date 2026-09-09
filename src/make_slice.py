"""1.1 m 높이 온도 단면을 격자로 뽑는다.

왜 필요한가
    관(유선)과 화살표만으로는 **색칠된 면적이 너무 작다.** 색이 변해도 눈에 안 띈다.
    ParaView 의 horz_T 처럼 넓은 면 하나가 통째로 색이 변해야 "식고 있다"가 보인다.
    1.1 m = 서 있을 때 몸통 높이, probes 의 기준 높이와 같다.

출력
    data/slices/slice_<frame>.csv     수평 1.1 m   ix, iy, x, y, T
    data/slices/vslice_<frame>.csv    수직 y=2.0m  ix, iz, x, z, T
    (좌표 cm / T 섭씨. 방 밖은 아예 안 쓴다)

    수평 한 장만으로는 "한 높이"만 보인다. 에어컨을 지나는 수직 단면을 같이 놓아야
    찬 공기가 내려오고 더운 공기가 천장에 남는 **성층**이 보인다.

실행
    py -m src.make_slice            # 전 프레임
    py -m src.make_slice 14
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_DIR = os.path.join(REPO, "data", "frames")
OUT_DIR = os.path.join(REPO, "data", "slices")

LX, LY, LZ = 8.0, 5.7, 2.7
CX = LX / 2.0
Z_SLICE = 1.10
Y_VSLICE = 2.00            # 수직 단면 위치 — 에어컨 카세트 중심을 지난다
VBAND = 0.22               # 이 y 범위의 셀을 쓴다 (m)
VDXZ = 0.08                # 수직 단면 격자 (m)
DXY = 0.08                 # 격자 간격 (m)
#   0.16 이었을 때 D자 경계가 16cm 계단으로 깨져 보였다.
#   절반으로 줄이면 8cm — 이 카메라 거리에서는 거의 안 보인다.
BAND = 0.20                # 이 높이 범위의 셀을 쓴다 (m)
R_PICK = 0.28              # 격자점 주변 이 반경 안의 셀 평균 (m)
KELVIN = 273.15
S = 100.0


def in_room(x, y):
    return ((x - CX) / CX) ** 2 + (y / LY) ** 2 <= 1.0


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = [int(sys.argv[1])] if len(sys.argv) > 1 else list(range(15))

    gx = np.arange(0.0, LX + 1e-9, DXY)
    gy = np.arange(0.0, LY + 1e-9, DXY)

    for i in frames:
        P, T = [], []
        with open(os.path.join(FRAME_DIR, "frame_%02d.csv" % i),
                  newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                z = float(r["z"])
                if abs(z - Z_SLICE) > BAND:
                    continue
                P.append((float(r["x"]), float(r["y"])))
                T.append(float(r["T"]))
        P = np.asarray(P)
        T = np.asarray(T)
        if T.mean() > 200.0:
            T = T - KELVIN

        # 격자 해시로 근방 평균 — 셀이 산재해서 최근접 하나만 쓰면 값이 튄다
        key = np.floor(P / R_PICK).astype(np.int64)
        off = key.min(axis=0)
        span = key.max(axis=0) - off + 1
        flat = (key[:, 0] - off[0]) * span[1] + (key[:, 1] - off[1])
        n = int(span[0] * span[1])
        acc = np.zeros(n)
        cnt = np.zeros(n)
        np.add.at(acc, flat, T)
        np.add.at(cnt, flat, 1.0)
        nz = cnt > 0
        acc[nz] /= cnt[nz]
        fallback = float(np.median(T))

        rows = []
        for iy, y in enumerate(gy):
            for ix, x in enumerate(gx):
                if not in_room(x, y):
                    continue
                k = np.floor(np.array([x, y]) / R_PICK).astype(np.int64) - off
                val = None
                if np.all(k >= 0) and np.all(k < span):
                    idx = int(k[0] * span[1] + k[1])
                    if cnt[idx] > 0:
                        val = acc[idx]
                if val is None:      # 경계 셀은 이웃까지 넓혀서 찾는다
                    best = None
                    for da in (-1, 0, 1):
                        for db in (-1, 0, 1):
                            kk = k + np.array([da, db])
                            if np.all(kk >= 0) and np.all(kk < span):
                                j = int(kk[0] * span[1] + kk[1])
                                if cnt[j] > 0:
                                    best = acc[j] if best is None else best
                    val = best if best is not None else fallback
                rows.append((ix, iy, x * S, y * S, val))

        out = os.path.join(OUT_DIR, "slice_%02d.csv" % i)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ix", "iy", "x", "y", "T"])
            for r in rows:
                w.writerow([r[0], r[1], "%.1f" % r[2], "%.1f" % r[3],
                            "%.3f" % r[4]])
        vals = [r[4] for r in rows]
        print("slice_%02d.csv   점 %d개 (격자 %dx%d)  T %.2f~%.2f C"
              % (i, len(rows), len(gx), len(gy), min(vals), max(vals)))

        # ── 수직 단면 (y = Y_VSLICE, 에어컨을 지나는 면) ──────────
        P2, T2 = [], []
        with open(os.path.join(FRAME_DIR, "frame_%02d.csv" % i),
                  newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if abs(float(r["y"]) - Y_VSLICE) > VBAND:
                    continue
                P2.append((float(r["x"]), float(r["z"])))
                T2.append(float(r["T"]))
        P2 = np.asarray(P2)
        T2 = np.asarray(T2)
        if T2.mean() > 200.0:
            T2 = T2 - KELVIN

        k2 = np.floor(P2 / R_PICK).astype(np.int64)
        o2 = k2.min(axis=0)
        s2 = k2.max(axis=0) - o2 + 1
        f2 = (k2[:, 0] - o2[0]) * s2[1] + (k2[:, 1] - o2[1])
        n2 = int(s2[0] * s2[1])
        a2 = np.zeros(n2)
        c2 = np.zeros(n2)
        np.add.at(a2, f2, T2)
        np.add.at(c2, f2, 1.0)
        nz2 = c2 > 0
        a2[nz2] /= c2[nz2]
        fb2 = float(np.median(T2))

        vx = np.arange(0.0, LX + 1e-9, VDXZ)
        vz = np.arange(0.0, LZ + 1e-9, VDXZ)
        vrows = []
        for iz, z in enumerate(vz):
            for ix, x in enumerate(vx):
                if not in_room(x, Y_VSLICE):
                    continue
                k = np.floor(np.array([x, z]) / R_PICK).astype(np.int64) - o2
                val = fb2
                if np.all(k >= 0) and np.all(k < s2):
                    j = int(k[0] * s2[1] + k[1])
                    if c2[j] > 0:
                        val = a2[j]
                vrows.append((ix, iz, x * S, z * S, val))

        vout = os.path.join(OUT_DIR, "vslice_%02d.csv" % i)
        with open(vout, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ix", "iz", "x", "z", "T"])
            for r in vrows:
                w.writerow([r[0], r[1], "%.1f" % r[2], "%.1f" % r[3],
                            "%.3f" % r[4]])
        vv = [r[4] for r in vrows]
        print("vslice_%02d.csv  점 %d개 (격자 %dx%d)  T %.2f~%.2f C"
              % (i, len(vrows), len(vx), len(vz), min(vv), max(vv)))


if __name__ == "__main__":
    main()
