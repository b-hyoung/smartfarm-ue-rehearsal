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


def velocity(pts, t, cfg):
    """(N,3) 기류(m/s). 에어컨 하강제트→바닥 방사확산→벽쪽 상승. t로 램프업."""
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    dx = x - cfg.ac.x
    dy = y - cfg.ac.y
    r = np.sqrt(dx * dx + dy * dy)
    core = np.exp(-((r / cfg.ac.jet_radius) ** 2))     # 에어컨 축 근처일수록 1
    zf = z / cfg.room.Lz                                # 0=바닥, 1=천장
    umax = cfg.flow.u_max

    w = -umax * core * zf                               # 축 아래 하강(음의 z), 위에서 강
    radial = umax * core * (1.0 - zf) * 0.7             # 바닥 근처 방사 확산
    ux = radial * dx / np.maximum(r, _EPS)
    uy = radial * dy / np.maximum(r, _EPS)

    r_ref = cfg.room.Lx / 2.0
    wall = np.clip(r / r_ref, 0.0, 1.0)
    w = w + umax * 0.3 * wall * (1.0 - zf)              # 벽 쪽 완만한 상승(재순환)

    U = np.stack([ux, uy, w], axis=1)
    ramp = 1.0 - np.exp(-t / cfg.flow.tau_flow_s)       # 에어컨 켜지며 발달
    return U * ramp
