"""라이브 트윈 예측기(임시) — 에어컨 위치를 받아 예상 온도·기류를 즉석 생성.

    data/_ac.json {"ac": [x_m, y_m]}   ← UE 가 에어컨 액터 위치를 써 준다
        ↓  (수식 모델 vane_mock, 수 초)
    data/slices/slice_NN.csv · vslice_NN.csv   (스키마 = make_slice 와 동일, cm)
    data/jets/jet_NN.csv                        (스키마 = make_jets 와 동일, m)
    data/probes.csv · data/frames/manifest.json

⚠ 이건 **임시 예측기**다. 나중에 케이스 라이브러리/대리모델(R5)이 오면
   이 파일 하나만 교체하면 된다 — 출력 스키마가 계약이고, UE 쪽은 그대로다.
   manifest source 에 MOCK 을 박아 실데이터와 절대 안 섞이게 한다.

실행  py -m src.predict_mock
"""
from __future__ import annotations

import json
import os
import shutil

import numpy as np

from src.config import load_config
from src.geometry import inside_mask
from src.power_model import FAN_W, series as power_series
from src.vane_mock import LIGHT_W, TIMES, temperature, velocity, write_probes

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KELVIN = 273.15
Z_H = 1.1               # 수평 단면 높이 (프로브 기준)
Z_SEED = 2.60
K, N, DT = 9, 170, 0.07


def _backup_real_once():
    """실데이터(vane25) 파생물을 mock 이 덮기 전에 한 번만 대피."""
    man_p = os.path.join(REPO, "data", "frames", "manifest.json")
    if not os.path.isfile(man_p):
        return
    src = str(json.load(open(man_p, encoding="utf-8")).get("source", ""))
    bak = os.path.join(REPO, "data", "_real-vane25")
    if "MOCK" in src.upper() or os.path.isdir(bak):
        return
    os.makedirs(bak)
    for d in ("slices", "jets"):
        p = os.path.join(REPO, "data", d)
        if os.path.isdir(p):
            shutil.copytree(p, os.path.join(bak, d))
    for f in ("probes.csv", os.path.join("frames", "manifest.json")):
        p = os.path.join(REPO, "data", f)
        if os.path.isfile(p):
            os.makedirs(os.path.dirname(os.path.join(bak, f)), exist_ok=True)
            shutil.copy2(p, os.path.join(bak, f))
    print("실데이터(vane25) -> data/_real-vane25/ 대피")


def write_hslice(cfg, ac, f, t, light=0.0):
    xs = np.linspace(0.0, cfg.room.Lx, 101)
    ys = np.linspace(0.0, cfg.room.Ly, 72)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    m = inside_mask(X.ravel(), Y.ravel(), cfg)
    ix, iy = np.meshgrid(range(101), range(72), indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), np.full(X.size, Z_H)], axis=1)[m]
    T = temperature(pts, t, cfg, ac, light) - KELVIN
    path = os.path.join(REPO, "data", "slices", "slice_%02d.csv" % f)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("ix,iy,x,y,T\n")
        for (i, j, p, tv) in zip(ix.ravel()[m], iy.ravel()[m], pts, T):
            fh.write("%d,%d,%.1f,%.1f,%.3f\n" % (i, j, p[0] * 100, p[1] * 100, tv))


def write_vslice(cfg, ac, f, t, light=0.0):
    """에어컨을 지나는 y=ac_y 수직 단면."""
    xs = np.linspace(0.0, cfg.room.Lx, 101)
    zs = np.linspace(0.05, cfg.room.Lz - 0.05, 34)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    m = inside_mask(X.ravel(), np.full(X.size, ac[1]), cfg)
    ix, iz = np.meshgrid(range(101), range(34), indexing="ij")
    pts = np.stack([X.ravel(), np.full(X.size, ac[1]), Z.ravel()], axis=1)[m]
    T = temperature(pts, t, cfg, ac, light) - KELVIN
    path = os.path.join(REPO, "data", "slices", "vslice_%02d.csv" % f)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("ix,iz,x,z,T\n")
        for (i, j, p, tv) in zip(ix.ravel()[m], iz.ravel()[m], pts, T):
            fh.write("%d,%d,%.1f,%.1f,%.3f\n" % (i, j, p[0] * 100, p[2] * 100, tv))


def in_room(p, cfg):
    x, y, z = p
    if z < 0.03 or z > cfg.room.Lz or y < 0.0:
        return False
    return bool(inside_mask(np.array([x]), np.array([y]), cfg)[0])


def write_jets(cfg, ac, f, t, light=0.0):
    """슬롯 4방향 커튼 — 시드는 에어컨 위치를 따라간다."""
    sheets = {
        "Xp": [(ac[0] + 0.457, ac[1] - 0.30 + 0.60 * i / (K - 1), Z_SEED)
               for i in range(K)],
        "Xm": [(ac[0] - 0.457, ac[1] - 0.30 + 0.60 * i / (K - 1), Z_SEED)
               for i in range(K)],
        "Yp": [(ac[0] - 0.30 + 0.60 * i / (K - 1), ac[1] + 0.457, Z_SEED)
               for i in range(K)],
        "Ym": [(ac[0] - 0.30 + 0.60 * i / (K - 1), ac[1] - 0.457, Z_SEED)
               for i in range(K)],
    }
    rows = []
    te = max(t, 5.0)                     # t=0 도 형태는 보이게
    for d, seeds in sheets.items():
        pts = np.array(seeds)
        alive = np.ones(K, dtype=bool)
        P = np.zeros((N, K, 3))
        for step in range(N):
            P[step] = pts
            v1 = velocity(pts, te, cfg, ac, light)
            v2 = velocity(pts + v1 * (DT / 2), te, cfg, ac, light)
            nxt = pts + v2 * DT
            for k in range(K):
                if alive[k]:
                    if not in_room(nxt[k], cfg) or np.linalg.norm(v2[k]) < 0.015:
                        alive[k] = False
                    else:
                        pts[k] = nxt[k]
        for _ in range(2):               # 스무딩 (make_jets 와 동일)
            Q = P.copy()
            for s in range(1, N):
                a, b = max(0, s - 3), min(N, s + 4)
                Q[s] = P[a:b].mean(axis=0)
            P = Q
        for step in range(N):
            T = temperature(P[step], te, cfg, ac, light) - KELVIN
            for k in range(K):
                rows.append((d, k, step, *P[step, k], T[k]))
    path = os.path.join(REPO, "data", "jets", "jet_%02d.csv" % f)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("dir,k,step,x,y,z,T\n")
        for r in rows:
            fh.write("%s,%d,%d,%.4f,%.4f,%.4f,%.3f\n" % r)


def main():
    cfg = load_config(os.path.join(REPO, "geometry.json"))
    ac = (4.0, 2.0)
    p = os.path.join(REPO, "data", "_ac.json")
    if os.path.isfile(p):
        ac = tuple(json.load(open(p, encoding="utf-8"))["ac"])[:2]
    # 방 밖·경계 위 배치 방어: 취출구가 방 안에 들도록 살짝 안쪽으로 클램프
    ac = (float(np.clip(ac[0], 0.7, cfg.room.Lx - 0.7)),
          float(np.clip(ac[1], 0.7, cfg.room.Ly - 0.7)))

    light = 0.0
    lp = os.path.join(REPO, "data", "_light.json")
    if os.path.isfile(lp):
        light = float(json.load(open(lp, encoding="utf-8")).get("pct", 0)) / 100.0

    _backup_real_once()
    for d in ("slices", "jets", "frames"):
        os.makedirs(os.path.join(REPO, "data", d), exist_ok=True)

    for f, t in enumerate(TIMES):
        write_hslice(cfg, ac, f, t, light)
        write_vslice(cfg, ac, f, t, light)
        write_jets(cfg, ac, f, t, light)
    write_probes(cfg, ac, light)

    # 전력(임시값 기반): 냉방 = 에너지수지(power_model), 조명 = pct x LIGHT_W
    rows = power_series(os.path.join(REPO, "data", "probes.csv"))
    pw = {"t": [], "cool_W": [], "light_W": round(light * LIGHT_W, 1),
          "fan_W": FAN_W,
          "note": "임시값: COP 3.5(1등급 추정)·조명 480W 가정 — 실측으로 교체"}
    for t in TIMES:
        r = min(rows, key=lambda x: abs(x[0] - t))
        pw["t"].append(t)
        pw["cool_W"].append(round(r[3], 1))
    kwh = 0.0
    for (t0, _, _, p0), (t1, _, _, p1) in zip(rows, rows[1:]):
        kwh += (p0 + p1) / 2 * (t1 - t0) / 3600.0
    pw["kwh_15min"] = round((kwh + light * LIGHT_W * 900 / 3600.0) / 1000.0, 3)
    with open(os.path.join(REPO, "data", "power.json"), "w",
              encoding="utf-8") as fh:
        json.dump(pw, fh, ensure_ascii=False)

    man = {"source": "MOCK-live (수식 예측, AC=%.2f,%.2f, 조명 %.0f%% — 대리모델로 교체 예정)"
                     % (ac[0], ac[1], light * 100),
           "solver": "field model (src/predict_mock.py)",
           "room_m": {"Lx": cfg.room.Lx, "Ly": cfg.room.Ly, "Lz": cfg.room.Lz},
           "ac": {"centre_ue_m": [ac[0], ac[1], cfg.room.Lz]},
           "frames": [{"frame": f, "time_s": float(t), "points": 0, "file": ""}
                      for f, t in enumerate(TIMES)]}
    with open(os.path.join(REPO, "data", "frames", "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2)
    print("PREDICT-MOCK done: AC=(%.2f, %.2f) 조명 %.0f%%  15프레임 갱신" % (ac[0], ac[1], light * 100))


if __name__ == "__main__":
    main()
