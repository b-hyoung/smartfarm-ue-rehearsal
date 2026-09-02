"""반원 공간의 시간별 온도(K)·기류(m/s)를 계산식으로 채운다(솔버 없음).

물리 정확이 아니라 '그럴듯함'이 목적 — UE 파이프 리허설용. 모든 상수는 cfg에서.
"""
import numpy as np

_EPS = 1e-6


def _horizontal_r(pts, cfg):
    dx = pts[:, 0] - cfg.ac.x
    dy = pts[:, 1] - cfg.ac.y
    return np.sqrt(dx * dx + dy * dy)


def temperature(pts, t, cfg):
    """(N,3) 점의 시각 t(s) 온도를 켈빈으로. t=0이면 start 균일, t→∞면 앵커 패턴."""
    tc = cfg.temperature_C
    r = _horizontal_r(pts, cfg)
    r_ref = cfg.room.Lx / 2.0
    s = np.clip(r / r_ref, 0.0, 1.0)               # 0=에어컨축, 1=먼 곳
    T_inf = tc.ac + (tc.side - tc.ac) * s           # 20C(축) → 22C(벽)
    tau = tc.tau_near_s + (tc.tau_far_s - tc.tau_near_s) * s
    T_C = T_inf + (tc.start - T_inf) * np.exp(-t / tau)
    return T_C + 273.15
