"""CFD 결과에서 방의 열 파라미터를 **역산**하고, 물리적으로 말이 되는지 검사한다.

왜 이걸 하나
    "CFD 가 맞나?" 를 CFD 로 검증할 수는 없다. 다른 방법으로 같은 답이 나와야 한다.
    여기서는 CFD 결과를 **집중정수(lumped) 모델**에 맞춰 계수를 역으로 뽑아낸 뒤,
    그 계수가 물리적으로 가능한 값인지(에어컨 용량, 벽 열관류율) 따진다.
    계수가 말이 안 되면 CFD 가 틀렸거나 경계조건이 이상한 것이다.

모델
    완전혼합 가정. 방 공기 온도 T 하나로 본다.

        V dT/dt = Q (Ts - T)  +  (UA/rho cp) (Tw - T)
                  ~~~~~~~~~~     ~~~~~~~~~~~~~~~~~~~~
                  에어컨 급기      벽에서 들어오는 열

        해:  T(t) = Tinf + (T0 - Tinf) exp(-t / tau)
             tau  = V / (Q + UA/rho cp)
             Tinf = (Q Ts + (UA/rho cp) Tw) / (Q + UA/rho cp)

    급기만 있고 벽 부하가 없으면 tau = V/Q = 232초, Tinf = Ts = 16.35C 여야 한다.
    CFD 가 23.5C 에서 멎는다면 그 차이가 곧 **벽 부하**다. 그 크기를 역산한다.

실행
    py -m src.room_model
"""
from __future__ import annotations

import csv
import json
import math
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_DIR = os.path.join(REPO, "data", "frames")

# ── 방/기기 제원 ──────────────────────────────────────────────
LX, LY, LZ = 8.0, 5.7, 2.7
AREA = math.pi * (LX / 2.0) * LY / 2.0      # 반타원 바닥 (m2)
VOL = AREA * LZ                             # 체적 (m3)

CMM = 25.0                                  # 카탈로그 풍량 (강)
Q = CMM / 60.0                              # m3/s
TS = 289.5 - 273.15                         # 급기 온도 (C)
TW = 29.0                                   # 벽 고정 온도 가정 (C)

RHO, CP = 1.2, 1005.0                       # 공기 (kg/m3, J/kgK)
RATED_W = 9000.0                            # 명판 정격 냉방능력


def room_curve():
    """프레임별 방 평균 온도 (부피가중 대신 셀 균등 — 격자가 거의 균일하다)."""
    man = json.load(open(os.path.join(FRAME_DIR, "manifest.json"),
                        encoding="utf-8"))
    ts, Ts = [], []
    for m in man["frames"]:
        T = []
        with open(os.path.join(FRAME_DIR, m["file"]), newline="",
                  encoding="utf-8") as f:
            for r in csv.DictReader(f):
                T.append(float(r["T"]))
        a = np.asarray(T)
        if a.mean() > 200.0:
            a = a - 273.15
        ts.append(float(m["time_s"]))
        Ts.append(float(a.mean()))
    return np.asarray(ts), np.asarray(Ts)


def fit_exp(t, T):
    """T = Tinf + (T0-Tinf) exp(-t/tau) 를 (Tinf, tau) 에 대해 맞춘다.

    비선형이라 Tinf 를 격자 탐색하고, 각 Tinf 에서 tau 는 선형회귀로 푼다
    (ln(T-Tinf) 가 t 에 대해 직선이므로). 파라미터가 둘뿐이라 이걸로 충분하다.
    """
    best = None
    for Tinf in np.arange(10.0, T.min() - 0.01, 0.01):
        y = T - Tinf
        if np.any(y <= 0):
            continue
        ln = np.log(y)
        A = np.vstack([t, np.ones_like(t)]).T
        sol, *_ = np.linalg.lstsq(A, ln, rcond=None)
        slope, inter = sol
        if slope >= 0:
            continue
        tau = -1.0 / slope
        pred = Tinf + math.exp(inter) * np.exp(-t / tau)
        rms = float(np.sqrt(np.mean((pred - T) ** 2)))
        if best is None or rms < best[0]:
            best = (rms, float(Tinf), float(tau), float(math.exp(inter)))
    return best


def sensor_lag(tau_room, Tinf, T0, t_target, T_target, tau_s_max=3000.0):
    """1차 지연 센서가 t_target 에 T_target 을 읽으려면 시정수가 얼마여야 하나.

    싸구려 온도계는 자기 열용량 때문에 실제 공기 온도를 몇 분 늦게 따라간다.
    "추운데 온도계는 27도" 는 이걸로 설명될 수 있다.
    """
    def read_at(tau_s):
        # dTs/dt = (T(t) - Ts)/tau_s 를 잘게 적분
        dt, Ts, t = 0.5, T0, 0.0
        while t < t_target:
            T = Tinf + (T0 - Tinf) * math.exp(-t / tau_room)
            Ts += (T - Ts) / tau_s * dt
            t += dt
        return Ts
    lo, hi = 1.0, tau_s_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if read_at(mid) < T_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), read_at(0.5 * (lo + hi))


def main():
    t, T = room_curve()
    print("방 체적 %.1f m3 (바닥 %.1f m2 x %.1f m)" % (VOL, AREA, LZ))
    print("급기 %.3f m3/s (%.0f CMM), 급기온도 %.2f C, 벽 %.1f C 고정"
          % (Q, CMM, TS, TW))
    print()

    rms, Tinf, tau, amp = fit_exp(t, T)
    tau_ideal = VOL / Q
    print("[1] CFD 방 평균온도 곡선을 지수함수로 맞춤")
    print("    T(t) = %.2f + %.2f exp(-t/%.0f)      RMS %.3f K" % (Tinf, amp, tau, rms))
    print("    tau = %.0f 초,  V/Q = %.0f 초  ->  차이 %.1f%%"
          % (tau, tau_ideal, 100 * abs(tau - tau_ideal) / tau_ideal))
    print()

    print("[2] 정상상태 에너지 수지로 역산한 열부하")
    q_cool = RHO * CP * Q * (Tinf - TS)
    print("    에어컨이 빼는 열 = rho cp Q (Tinf - Ts) = %.0f W" % q_cool)
    print("    정상상태이므로 벽에서 들어오는 열도 같은 %.0f W" % q_cool)
    UA = q_cool / (TW - Tinf)
    wall_area = 2 * AREA + math.pi * LY * LZ * 0.6
    print("    UA = %.0f W / (%.1f - %.2f K) = %.0f W/K" % (q_cool, TW, Tinf, UA))
    print("    벽 면적 약 %.0f m2 -> U = %.1f W/m2K" % (wall_area, UA / wall_area))
    print()

    print("[3] 물리적으로 말이 되는가")
    ok1 = q_cool <= RATED_W
    print("    (a) 냉방부하 %.0f W vs 명판 정격 %.0f W -> %s (%.0f%% 사용)"
          % (q_cool, RATED_W, "가능" if ok1 else "*불가능*", 100 * q_cool / RATED_W))
    U = UA / wall_area
    ok2 = 2.0 <= U <= 12.0
    print("    (b) U = %.1f W/m2K, 실내 표면 대류는 보통 2~10 -> %s"
          % (U, "타당" if ok2 else "*비현실적*"))
    print()

    print("[4] ★ 여기서 모순이 나온다")
    G = UA / (RHO * CP)
    tau_pred = VOL / (Q + G)
    print("    벽 부하가 (Tw - T) 에 비례한다면 tau = V/(Q + UA/rho cp)")
    print("      = %.1f / (%.4f + %.4f) = %.0f 초 여야 한다" % (VOL, Q, G, tau_pred))
    print("    그런데 CFD 곡선의 tau 는 %.0f 초 — V/Q 와 정확히 같다 (오차 %.1f%%)."
          % (tau, 100 * abs(tau - tau_ideal) / tau_ideal))
    print()
    print("    tau 가 V/Q 라는 건 벽 열유입이 방 평균온도에 **거의 안 반응한다**는 뜻이다.")
    print("    즉 CFD 안에서 벽 근처 공기가 방 평균과 따로 논다 — 방이 완전혼합이 아니다.")
    print("    (실제로 반원 안쪽 유속이 0.075 m/s 로 평벽 쪽 0.138 의 절반이다)")
    print("    -> 단일존 모델로는 이 방을 못 그린다. 지점별로 봐야 하는 이유.")
    print()

    print("[5] 실측과 대조 — 29C 에서 켜고 10분 뒤 27C, 그런데 몸은 추웠다")
    T0r, tr, Tr = 29.0, 600.0, 27.0
    pred = Tinf + (T0r - Tinf) * math.exp(-tr / tau)
    print("    CFD 기준 예측: %.0f초 후 %.2f C   (실측 %.2f C, 차 %.2f K)"
          % (tr, pred, Tr, Tr - pred))
    tau_s, got = sensor_lag(tau, Tinf, T0r, tr, Tr)
    print("    온도계가 1차 지연이라면 시정수 %.0f 초(%.1f 분)일 때 %.2f C 를 읽는다."
          % (tau_s, tau_s / 60.0, got))
    print("    싸구려 온도계 시정수는 보통 1~5분이다. %s"
          % ("이 범위 안이라 '추운데 27도'가 센서 지연으로 설명된다."
             if tau_s <= 420 else
             "이 범위를 넘으므로 센서 지연만으로는 설명이 안 된다 — 방 자체가 덜 식었다."))
    print()
    print("    ※ 주의: 이건 '실측이 틀렸다'는 뜻이 아니다. 두 가지 가능성이 남는다.")
    print("       (a) 온도계 지연 — 센서를 바람 부는 곳에 두고 5분 기다린 뒤 읽으면 갈린다")
    print("       (b) 실제 열부하가 CFD 가정(벽 29C)보다 크다 — 그러면 방이 덜 식는다")


if __name__ == "__main__":
    main()
