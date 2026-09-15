"""4방향 취출 리본 커튼 — 슬롯마다 궤적 다발을 적분해 '시트'로 만든다.

유선 140개 부챗살("다 이상하다")을 대체하는 정돈된 표현:
    슬롯 4개 × 궤적 9줄 = 리본 시트 4장.
    천장을 타고 나가 벽에서 내려오는 경로가 한 장의 커튼으로 보인다.
    색 = 그 지점 온도 (UE 쪽에서 정점색으로 칠함).

지금은 mock(vane_mock) 유동장을 직접 적분한다. 진짜 vane25 프레임이 오면
같은 스키마로 격자 보간 버전을 붙인다.

출력  data/jets/jet_NN.csv   dir,k,step,x,y,z,T   (m, ℃)
실행  py -m src.pipeline.make_jets
"""
from __future__ import annotations

import json
import os

import numpy as np

from src.config import load_config
from src.pipeline.make_traces import Field, load_frame
from src.models.vane_mock import TIMES, temperature, velocity

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "data", "jets")
FRAME_DIR = os.path.join(REPO, "data", "frames")
KELVIN = 273.15

AC = (4.0, 2.0)
K = 9            # 시트당 궤적 수
N = 170          # 스텝 수 (모든 궤적 동일 — 시트 격자가 되도록)
DT = 0.07        # s

# 슬롯 시드: (방향, 시드 시작점, 시드 끝점)  z=2.60 슬롯 바로 아래
# ⚠ Y 슬롯은 x 3.70~4.30 (에어컨 중심 4.0) — 처음에 1.70~2.30 으로 잘못 찍어서
#   Y 커튼 둘이 허공에서 시작해 "한 방향으로만 나간다"로 보였다.
SHEETS = {
    "Xp": ((4.457, 1.70), (4.457, 2.30)),
    "Xm": ((3.543, 1.70), (3.543, 2.30)),
    "Yp": ((3.70, 2.457), (4.30, 2.457)),
    "Ym": ((3.70, 1.543), (4.30, 1.543)),
}
Z_SEED = 2.60


def in_room(p, cfg):
    x, y, z = p
    if z < 0.03 or z > cfg.room.Lz or y < 0.0:
        return False
    a, b, cx = cfg.room.Lx / 2.0, cfg.room.Ly, cfg.room.Lx / 2.0
    return ((x - cx) / a) ** 2 + (y / b) ** 2 <= 1.0


def integrate_sheet(d, cfg, t):
    (x0, y0), (x1, y1) = SHEETS[d]
    if d in ("Yp", "Ym"):        # 시드가 x 방향으로 늘어선 시트
        seeds = [(x0 + (x1 - x0) * i / (K - 1), y0, Z_SEED) for i in range(K)]
    else:
        seeds = [(x0, y0 + (y1 - y0) * i / (K - 1), Z_SEED) for i in range(K)]
    pts = np.array(seeds)                     # (K,3) 현재 위치
    alive = np.ones(K, dtype=bool)
    rows = []
    for step in range(N):
        T = temperature(pts, t, cfg) - KELVIN
        for k in range(K):
            rows.append((d, k, step, *pts[k], T[k]))
        # RK2
        v1 = velocity(pts, t, cfg)
        mid = pts + v1 * (DT / 2)
        v2 = velocity(mid, t, cfg)
        nxt = pts + v2 * DT
        for k in range(K):
            if alive[k]:
                sp = np.linalg.norm(v2[k])
                if not in_room(nxt[k], cfg) or sp < 0.02:
                    alive[k] = False
                else:
                    pts[k] = nxt[k]
        # 죽은 궤적은 그 자리에 멈춘다 (시트 격자 유지)
    return rows


def _load_T(idx):
    import csv as _csv
    path = os.path.join(FRAME_DIR, "frame_%02d.csv" % idx)
    Ts = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            Ts.append(float(r["T"]))
    return np.asarray(Ts, dtype=np.float64)


def integrate_sheet_grid(d, cfg, fidx):
    """진짜 CFD 프레임의 격자 속도장으로 적분 (mock 해석식 대신)."""
    pts_f, vel = load_frame(fidx)
    fld = Field(pts_f, vel)
    tfld = Field(pts_f, _load_T(fidx)[:, None])
    (x0, y0), (x1, y1) = SHEETS[d]
    if d in ("Yp", "Ym"):
        seeds = [(x0 + (x1 - x0) * i / (K - 1), y0, Z_SEED) for i in range(K)]
    else:
        seeds = [(x0, y0 + (y1 - y0) * i / (K - 1), Z_SEED) for i in range(K)]
    pts = np.array(seeds)
    alive = np.ones(K, dtype=bool)
    P = np.zeros((N, K, 3))
    dt = 0.05
    for step in range(N):
        P[step] = pts
        v1 = fld.sample(pts)
        v2 = fld.sample(pts + v1 * (dt / 2))
        nxt = pts + v2 * dt
        for k in range(K):
            if alive[k]:
                # 문턱은 make_traces 와 동일 0.015 — 벽 근처 경계층이 느려서
                # 0.03 이면 벽에 닿자마자 얼어붙는다 (하강 구간이 잘림)
                if not in_room(nxt[k], cfg) or np.linalg.norm(v2[k]) < 0.015:
                    alive[k] = False
                else:
                    pts[k] = nxt[k]
    # 최근접 셀 샘플링의 지그재그를 진행 방향으로 이동평균(창 7, 2회) —
    # 구겨진 비닐("부자연스럽다")이 매끈한 커튼이 된다. 시작점은 고정.
    for _ in range(2):
        Q = P.copy()
        for s in range(1, N):
            a, b = max(0, s - 3), min(N, s + 4)
            Q[s] = P[a:b].mean(axis=0)
        P = Q
    rows = []
    for step in range(N):
        T = tfld.sample(P[step])[:, 0] - KELVIN
        for k in range(K):
            rows.append((d, k, step, *P[step, k], T[k]))
    return rows


def main():
    cfg = load_config(os.path.join(REPO, "geometry.json"))
    os.makedirs(OUT, exist_ok=True)
    man_p = os.path.join(FRAME_DIR, "manifest.json")
    src = ""
    if os.path.isfile(man_p):
        src = str(json.load(open(man_p, encoding="utf-8")).get("source", ""))
    real = "MOCK" not in src.upper()
    print("모드: %s (frames source=%s)" % ("실데이터 격자" if real else "mock 해석식",
                                          src[:40]))
    for f, t in enumerate(TIMES):
        rows = []
        for d in SHEETS:
            if real:
                rows += integrate_sheet_grid(d, cfg, f)
            else:
                rows += integrate_sheet(d, cfg, max(t, 5.0))
        path = os.path.join(OUT, "jet_%02d.csv" % f)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("dir,k,step,x,y,z,T\n")
            for r in rows:
                fh.write("%s,%d,%d,%.4f,%.4f,%.4f,%.3f\n" % r)
        if f in (0, 5, 14):
            zs = [r[5] for r in rows]
            print("jet_%02d t=%.0fs  행 %d  z범위 %.2f~%.2f" %
                  (f, t, len(rows), min(zs), max(zs)))
    print("done -> data/jets (시트 4장 × 궤적 %d × 스텝 %d)" % (K, N))


if __name__ == "__main__":
    main()
