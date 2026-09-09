"""속도장을 성긴 격자로 추려 화살표용 데이터를 만든다.

왜 필요한가
    유선(streamline)은 "급기가 어디로 가는가"는 잘 보여주지만, 유선이 도달하지 못한
    구역(정체 구역)에 대해서는 아무 말도 안 한다. 화살표 격자는 방 **전체**를 고르게
    훑으므로 그 빈틈을 메운다. 둘은 상호보완이다.

    엔진 기본 Niagara 시각화의 빨간 화살표를 대체한다. 그쪽은 파티클 구·경계상자가
    한 시스템에 묶여 있어 개별로 못 끄고, 색도 고정 빨강이라 정보가 없다.

출력
    data/arrows/arrow_<frame>.csv
        x, y, z, ux, uy, uz, speed, T      (좌표 cm / 속도 m/s / T 섭씨)
        ux,uy,uz 는 **단위벡터**. 길이는 UE 쪽에서 speed 로 정한다.

실행
    py -m src.make_arrows            # 전 프레임
    py -m src.make_arrows 14         # 한 프레임만
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_DIR = os.path.join(REPO, "data", "frames")
OUT_DIR = os.path.join(REPO, "data", "arrows")

LX, LY, LZ = 8.0, 5.7, 2.7
CX = LX / 2.0
KELVIN = 273.15
S = 100.0

# 격자 간격 (m). 촘촘하면 화면이 뭉개지고, 성기면 구조를 놓친다.
DX, DY = 0.60, 0.60
# ★ 높이를 셋에서 **하나**로 줄였다.
#   세 층을 동시에 그리면 화면 깊이 방향으로 화살표가 겹쳐서 벽처럼 보인다.
#   3D 구조는 유선(튜브)이 이미 말하고 있으므로, 화살표는 한 평면만 맡는다.
#   1.1 m = 서 있을 때 몸통 높이. ParaView 의 horz_T 단면과 같은 높이다.
ZS = [1.10]
R_PICK = 0.30               # 격자점 주변 이 반경(m) 안의 셀을 평균
CULL_PCT = 25               # 느린 쪽 이 백분율은 버린다 (배경 잡음처럼 깔림)


def in_room(x, y):
    return ((x - CX) / CX) ** 2 + (y / LY) ** 2 <= 0.96   # 벽에서 살짝 안쪽


def load_frame(idx):
    P, U, T = [], [], []
    with open(os.path.join(FRAME_DIR, "frame_%02d.csv" % idx),
              newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            P.append((float(r["x"]), float(r["y"]), float(r["z"])))
            U.append((float(r["Ux"]), float(r["Uy"]), float(r["Uz"])))
            T.append(float(r["T"]))
    P = np.asarray(P)
    U = np.asarray(U)
    T = np.asarray(T)
    if T.mean() > 200.0:
        T = T - KELVIN
    return P, U, T


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = [int(sys.argv[1])] if len(sys.argv) > 1 else list(range(15))
    for i in frames:
        P, U, T = load_frame(i)

        # 격자점마다 반경 R_PICK 안의 셀 평균. 셀이 산재해 있어 최근접 하나만 쓰면
        # 값이 튄다 (한 셀이 그 구역을 대표하지 못함).
        cell = R_PICK
        key = np.floor(P / cell).astype(np.int64)
        off = key.min(axis=0)
        span = key.max(axis=0) - off + 1
        flat = ((key[:, 0] - off[0]) * span[1] + (key[:, 1] - off[1])) * span[2] \
            + (key[:, 2] - off[2])
        n = int(span[0] * span[1] * span[2])
        accU = np.zeros((n, 3))
        accT = np.zeros(n)
        cnt = np.zeros(n)
        np.add.at(accU, flat, U)
        np.add.at(accT, flat, T)
        np.add.at(cnt, flat, 1.0)
        nz = cnt > 0
        accU[nz] /= cnt[nz][:, None]
        accT[nz] /= cnt[nz]

        rows = []
        nx = int(LX / DX) + 1
        ny = int(LY / DY) + 1
        for a in range(nx):
            for b in range(ny):
                x = a * DX
                y = b * DY
                if not in_room(x, y):
                    continue
                for z in ZS:
                    k = np.floor(np.array([x, y, z]) / cell).astype(np.int64) - off
                    if np.any(k < 0) or np.any(k >= span):
                        continue
                    idx = int((k[0] * span[1] + k[1]) * span[2] + k[2])
                    if cnt[idx] <= 0:
                        continue
                    v = accU[idx]
                    sp = float(np.linalg.norm(v))
                    if sp < 1e-4:
                        continue
                    u = v / sp
                    rows.append((x * S, y * S, z * S,
                                 u[0], u[1], u[2], sp, accT[idx]))

        # 느린 화살표를 다 그리면 정체 구역이 "짧은 화살표 밭"이 되어 오히려 안 보인다.
        # 잘라내면 화살표가 **없는 것** 자체가 정체를 말해준다.
        if rows and CULL_PCT > 0:
            sp_all = sorted(r[6] for r in rows)
            thr = sp_all[int(len(sp_all) * CULL_PCT / 100.0)]
            kept = [r for r in rows if r[6] >= thr]
            print("  frame %02d: %d개 중 느린 %d%% 제거 -> %d개 (기준 %.3f m/s)"
                  % (i, len(rows), CULL_PCT, len(kept), thr))
            rows = kept

        out = os.path.join(OUT_DIR, "arrow_%02d.csv" % i)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["x", "y", "z", "ux", "uy", "uz", "speed", "T"])
            for r in rows:
                w.writerow(["%.1f" % r[0], "%.1f" % r[1], "%.1f" % r[2],
                            "%.4f" % r[3], "%.4f" % r[4], "%.4f" % r[5],
                            "%.4f" % r[6], "%.2f" % r[7]])
        sp = [r[6] for r in rows]
        if not sp:
            # frame_00 은 냉방 전이라 속도가 사실상 0 — 화살표가 하나도 안 남는다.
            # 오류가 아니라 물리적으로 맞는 결과이므로 빈 파일을 그대로 둔다.
            print("arrow_%02d.csv  화살표 0개 (정지 상태)" % i)
            continue
        print("arrow_%02d.csv  화살표 %d개  |V| %.3f~%.3f m/s"
              % (i, len(rows), min(sp), max(sp)))


if __name__ == "__main__":
    main()
