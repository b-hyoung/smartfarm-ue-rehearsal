"""냉방 전력 근사 모델 — CFD 리턴온도에서 열제거율·소비전력을 계산.

원리 (에너지 수지):
    열제거율 Q̇(t) = ṁ·cp·(T_return(t) − T_supply)
        ṁ  = 취출 유량 25 CMM × 공기밀도  (CFD 경계조건과 동일)
        T_supply = 16.35 ℃ (급기, CFD 경계조건)
        T_return(t) ≈ 에어컨 바로 아래 1.7 m 프로브(A) — 리턴이 빨아들이는 공기
    소비전력 P(t) = Q̇(t) / COP

⚠ COP 는 가정값이다 (기본 3.2 — 천장 카세트 통상 범위 3.0~3.8).
   명판의 정격 소비전력을 주면 그걸로 교정한다. 그 전까지 이 값은
   "경향은 맞는 근사"로만 쓸 것. R4(EnergyPlus)·전력 실측이 오면 교체.

실행  py -m src.power_model            (data/probes.csv 기준)
      py -m src.power_model 경로.csv   (다른 probes 파일)
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FLOW_CMM = 25.0          # 취출 유량 (CFD 경계조건)
T_SUPPLY = 16.35         # 급기 온도 ℃
RHO = 1.17               # 공기 밀도 kg/m3 (~25℃)
CP = 1006.0              # 공기 비열 J/kgK
COP = 3.2                # ★ 가정 — 명판 소비전력으로 교정할 것
FAN_W = 90.0             # 실내기 팬 소비(대략, 카세트 강풍)

MDOT_CP = FLOW_CMM / 60.0 * RHO * CP     # W/K


def load_return_T(path):
    """probes.csv → [(t, T_return)] — A 지점 1.7 m 를 리턴 온도 근사로."""
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["point"] == "A" and abs(float(r["z"]) - 1.7) < 1e-6:
                out.append((float(r["t_s"]), float(r["T_C"])))
    return out


def series(path):
    rows = []
    for t, tr in load_return_T(path):
        q = max(MDOT_CP * (tr - T_SUPPLY), 0.0)      # 열제거율 W
        p = q / COP + FAN_W                          # 소비전력 W
        rows.append((t, tr, q, p))
    return rows


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        REPO, "data", "probes.csv")
    rows = series(path)
    if not rows:
        raise SystemExit("A/1.7m 프로브가 없음: %s" % path)
    # 적산 전력량 (사다리꼴)
    wh = 0.0
    for (t0, _, _, p0), (t1, _, _, p1) in zip(rows, rows[1:]):
        wh += (p0 + p1) / 2 * (t1 - t0) / 3600.0
    print("냉방 전력 근사 (유량 %.0f CMM · 급기 %.2f℃ · COP %.1f 가정)"
          % (FLOW_CMM, T_SUPPLY, COP))
    print("%8s %10s %12s %12s" % ("t(s)", "리턴 ℃", "열제거 W", "소비전력 W"))
    for t, tr, q, p in rows:
        if t in (0.0,) or abs(t % 115.0) < 0.6 or t == rows[-1][0]:
            print("%8.0f %10.2f %12.0f %12.0f" % (t, tr, q, p))
    print("15분 적산: %.0f Wh (%.2f kWh)" % (wh, wh / 1000))
    print("참고: 정격 9 kW 대비 평균 부하율 %.0f%%"
          % (sum(r[2] for r in rows) / len(rows) / 9000 * 100))


if __name__ == "__main__":
    main()
