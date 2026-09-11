"""4Way 카세트 측면 취출(베인 25°) **임시 목데이터** — acRoom-vane25 완료 전 UE 구조용.

실물 패턴(사용자 확인): 냉기가 4방향으로 천장을 타고 퍼진다 → **천장 바로 아래부터
시원해지고**, 벽에 닿으면 타고 내려와 바닥이 식고, 방 가운데 아래쪽이 마지막.

⚠ 물리 해석이 아니다. 진짜 vane25 결과가 나오면 이 데이터는 통째로 교체된다.
   source 컬럼을 "mock-vane25" 로 박아 실데이터와 절대 안 섞이게 한다.

스키마·시각표는 진짜 CFD(acRoom-transient)와 동일:
    x,y,z,T(K),Ux,Uy,Uz,p,source · manifest {frame, time_s, points, file}
    시각 0,60,130,...,900초 15프레임 · probes.csv (A/B/C/D × 3높이 × 1.15초 간격)

실행  py -m src.vane_mock
"""
from __future__ import annotations

import json
import os

import numpy as np
# pandas 금지 — 이 PC 는 앱 제어 정책이 pandas DLL 을 차단한다 (hanes 참조 예정)

from src.config import load_config
from src.geometry import make_grid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "frames")
KELVIN = 273.15

TIMES = [0.0, 60.0, 130.0, 190.0, 260.0, 320.0, 390.0, 450.0, 510.0,
         580.0, 640.0, 710.0, 770.0, 840.0, 900.0]     # 진짜 manifest 그대로

AC = (4.0, 2.0, 2.7)      # UE m
VANE_DEG = 25.0           # 천장면 기준
U_SUPPLY = 4.108          # 취출 |U| (vane25 경계조건과 동일)
LAYER = 0.32              # 천장 제트층 두께 (m)
T_START = 28.85           # ℃ 균일 초기
T_SUPPLY = 16.35          # 급기
T_FLOOR_END = 22.9        # 900초 바닥 근처
T_CEIL_END = 23.8         # 900초 천장(제트 밖)
T_JET_END = 20.5          # 900초 제트층(에어컨 근처)


def _wall_dist(x, y, cfg):
    """D자 경계까지의 대략적 수평 거리(m). 타원 반경 방향 근사."""
    a, b, cx = cfg.room.Lx / 2.0, cfg.room.Ly, cfg.room.Lx / 2.0
    # 타원 스케일 좌표에서의 '반경'
    s = np.sqrt(((x - cx) / a) ** 2 + (np.maximum(y, 0.0) / b) ** 2)
    r_eff = np.minimum(a, b)                     # 보수적 스케일
    d_ell = (1.0 - np.clip(s, 0.0, 1.0)) * r_eff
    return np.minimum(d_ell, np.maximum(y, 0.0))  # 평벽(y=0)까지 거리와의 최소


def velocity(pts, t, cfg, ac=None):
    """천장 방사 제트 + 벽 하강 + 바닥 귀환 + 중앙 상승(리턴). m/s.

    ac=(x, y): 에어컨 수평 위치(m). 생략 시 기본 위치 — "옮기면 값이 바뀌는"
    라이브 트윈은 이 인자로 임의 위치의 예상 유동장을 얻는다.
    """
    ax, ay = ac if ac is not None else (AC[0], AC[1])
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    dx, dy = x - ax, y - ay
    r = np.sqrt(dx * dx + dy * dy)
    er_x, er_y = dx / np.maximum(r, 1e-6), dy / np.maximum(r, 1e-6)
    zc = cfg.room.Lz

    # ① 천장 제트층: 반경 방향으로 뿜고 천장에 붙어 간다(코안다). 거리 감쇠 1/(1+r/r0)
    jet_prof = np.exp(-(((zc - z) / LAYER) ** 2))
    u_r = U_SUPPLY * np.cos(np.radians(VANE_DEG)) / (1.0 + r / 0.8) * jet_prof
    # 취출 직후에만 25° 아래 성분, 멀어지면 천장에 붙는다
    w_jet = -u_r * np.tan(np.radians(VANE_DEG)) * np.exp(-r / 1.2)

    # ② 벽 하강: 제트가 벽에 닿아 타고 내려온다
    dw = _wall_dist(x, y, cfg)
    wall = np.exp(-((dw / 0.35) ** 2))
    w_wall = -0.55 * wall * np.clip(z / zc, 0.15, 1.0)

    # ③ 바닥 귀환: 바닥층에서 에어컨 쪽으로 되돌아온다
    floor_prof = np.exp(-((z / 0.45) ** 2))
    u_back = -0.30 * floor_prof * np.clip(r / 2.0, 0.0, 1.0)

    # ④ 중앙 상승: 에어컨 리턴(중앙 흡입)으로 올라간다
    core = np.exp(-((r / 0.7) ** 2))
    w_up = 0.35 * core * np.clip(1.0 - z / zc, 0.0, 1.0) * (1.0 - jet_prof)

    ux = (u_r + u_back) * er_x
    uy = (u_r + u_back) * er_y
    w = w_jet + w_wall + w_up
    ramp = 1.0 - np.exp(-t / cfg.flow.tau_flow_s)
    return np.stack([ux, uy, w], axis=1) * ramp


def temperature(pts, t, cfg, ac=None):
    """냉각 도달 지연 d(점) + 국소 시정수. 천장층 → 벽 → 바닥 중앙 순서로 식는다."""
    ax, ay = ac if ac is not None else (AC[0], AC[1])
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    dx, dy = x - ax, y - ay
    r = np.sqrt(dx * dx + dy * dy)
    zc = cfg.room.Lz

    # 냉기 도달 지연: 천장을 타고(r) → 벽에서 내려와(zc-z) → 바닥을 돌아온다
    dw = _wall_dist(x, y, cfg)
    near_ceil = np.exp(-(((zc - z) / LAYER) ** 2))
    d_ceil = r / 0.045                          # 천장층: 900초 안에 다 덮는 속도
    d_wall = dw / 0.9 * 60 + (zc - z) / 0.011   # 벽에서 내려오는 경로
    delay = np.where(near_ceil > 0.4, d_ceil, np.minimum(d_wall, d_ceil + (zc - z) / 0.008))

    # 최종(900초+) 온도장: 성층 + 제트층 한랭
    T_end = T_FLOOR_END + (T_CEIL_END - T_FLOOR_END) * (z / zc)
    jet_cold = (T_JET_END - T_CEIL_END) * near_ceil * np.exp(-r / 2.2)
    T_end = T_end + jet_cold
    # 취출구 바로 옆은 급기 온도에 접근
    T_end = np.minimum(T_end + 0, np.where(
        (near_ceil > 0.5) & (r < 0.9), T_SUPPLY + 3.0 + r * 2.0, T_end))

    tau = 90.0 + 140.0 * np.clip(1.0 - z / zc, 0.0, 1.0)   # 아래쪽일수록 느리게
    te = np.maximum(t - delay, 0.0)
    prog = 1.0 - np.exp(-te / tau)
    T_C = T_START + (T_end - T_START) * prog
    return T_C + KELVIN


def write_probes(cfg, ac=None):
    """A/B/C/D × 3높이 × 1.15초 간격 — 진짜 probes.csv 와 같은 스키마.

    측정점은 방에 고정이고(센서 위치), 에어컨(ac)이 옮겨지면 값만 달라진다.
    """
    pos = {"A": (4.0, 2.0), "B": (7.5, 0.8), "C": (4.0, 4.5), "D": (0.5, 0.8)}
    heights = [0.1, 1.1, 1.7]
    ts = np.arange(0.0, 900.0 + 1e-6, 1.15)
    rows = []
    pts = np.array([[px, py, h] for px, py in pos.values() for h in heights])
    names = [n for n in pos for _ in heights]
    hs = heights * len(pos)
    for t in ts:
        T = temperature(pts, t, cfg, ac) - KELVIN
        U = np.linalg.norm(velocity(pts, t, cfg, ac), axis=1)
        for i, n in enumerate(names):
            rows.append((round(t, 2), n, pts[i, 0], pts[i, 1], hs[i],
                         round(float(T[i]), 3), round(float(U[i]), 4)))
    path = os.path.join(REPO, "data", "probes.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("t_s,point,ue_x,ue_y,z,T_C,U_mag\n")
        for r_ in rows:
            f.write("%s,%s,%.2f,%.2f,%.2f,%.3f,%.4f\n" % r_)
    print("probes.csv: %d행" % len(rows))


def main():
    cfg = load_config(os.path.join(REPO, "geometry.json"))
    os.makedirs(OUT, exist_ok=True)
    pts = make_grid(cfg)
    man = {"source": "MOCK-vane25 (임시값 — 진짜 계산 완료 시 교체)",
           "solver": "field model (src/vane_mock.py)",
           "room_m": {"Lx": cfg.room.Lx, "Ly": cfg.room.Ly, "Lz": cfg.room.Lz,
                      "shape": "D (semi-ellipse)"},
           "ac": {"type": "4Way ceiling cassette (vane 25deg side discharge)",
                  "centre_ue_m": list(AC)},
           "frames": []}
    for f, t in enumerate(TIMES):
        T = temperature(pts, t, cfg)
        U = velocity(pts, t, cfg)
        name = "frame_%02d.csv" % f
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as fh:
            fh.write("x,y,z,T,Ux,Uy,Uz,p,source\n")
            for i in range(len(pts)):
                fh.write("%.4f,%.4f,%.4f,%.3f,%.4f,%.4f,%.4f,%.2f,mock-vane25\n"
                         % (pts[i, 0], pts[i, 1], pts[i, 2], T[i],
                            U[i, 0], U[i, 1], U[i, 2], 100000.0))
        tc = T - KELVIN
        print("frame %02d t=%4.0fs  T %.1f~%.1f  |U|max %.2f" %
              (f, t, tc.min(), tc.max(), np.linalg.norm(U, axis=1).max()))
        man["frames"].append({"frame": f, "time_s": t, "points": len(pts),
                              "file": name})
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2)
    write_probes(cfg)
    print("done -> data/frames (MOCK-vane25)")


if __name__ == "__main__":
    main()
