"""실측 ↔ 예측 검사 + 미지 입력 역산 — **PINN 자리(임시)**.

루프(STRUCTURE.md)에서 PINN 의 역할: 실측이 예측과 어긋날 때 어떤 입력값이
틀렸는지 역산. 지금은 실측이 없어 CFD 백업 2케이스를 가짜 실측으로 쓰고,
역산기도 물리손실 없는 격자 최소제곱(임시)이다. 진짜가 오면:
    · 실측 CSV  → 이 스크립트 입력 경로만 교체 (스키마 동일: t_s,point,...,T_C)
    · 역산기    → 진짜 PINN(물리손실 포함)으로 이 파일만 교체

역산하는 미지 입력 3개 (vane_mock.temperature 의 fit 인자):
    dT_end   평형온도 오프셋 ℃  → 열부하/UA_EFF 임시값 오차
    s_tau    시정수 배율        → 풍량·믹싱 오차
    s_delay  도달지연 배율      → 취출 유로(베인 방향 등) 오차

판정: 보정 후 RMS ≤0.5℃ 적합(파라미터만 보정) · ≤1.0 주의 · 초과 불일치
(모델 가정 자체가 틀림 — 예: 수직취출인데 측면취출 모델).

실행  py -m src.pinn_check data/archive/vane25/probes.csv
      py -m src.pinn_check data/archive/vert/probes.csv --label vert
결과  콘솔 + data/pinn_check.json (라벨별 누적)
"""
from __future__ import annotations

import argparse
import csv
import json
import os

import numpy as np

from src import vane_mock as VM
from src.config import load_config

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(REPO, "data", "pinn_check.json")


def load_measured(path):
    """probes.csv → (ts (n_t,), pts (n_p,3), names [n_p], T (n_t,n_p) ℃)."""
    by_t = {}
    keys = None
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = (r["point"], float(r["z"]))
            by_t.setdefault(float(r["t_s"]), {})[k] = (
                float(r["ue_x"]), float(r["ue_y"]), float(r["T_C"]))
            if keys is None or len(by_t[float(r["t_s"])]) > len(keys):
                keys = sorted(by_t[float(r["t_s"])])
    ts = sorted(t for t, d in by_t.items() if len(d) == len(keys))
    pts = np.array([[by_t[ts[0]][k][0], by_t[ts[0]][k][1], k[1]] for k in keys])
    T = np.array([[by_t[t][k][2] for k in keys] for t in ts])
    names = ["%s@%.1fm" % (k[0], k[1]) for k in keys]
    return np.array(ts), pts, names, T


def predict(ts, pts, cfg, ac, light, rack, fit=None):
    """(n_t, n_p) ℃ — temperature() 의 t 브로드캐스트 사용, 호출 1번."""
    return VM.temperature(pts, ts[:, None], cfg, ac, light, rack,
                          fit=fit) - VM.KELVIN


def rms(a):
    return float(np.sqrt(np.mean(a * a)))


def inverse_fit(ts, pts, T_meas, cfg, ac, light, rack):
    """격자 탐색 최소제곱(임시) — 진짜 PINN 으로 교체될 자리.

    2단계 coarse→fine. 모델 평가가 싸서(호출당 수 ms) 전수 탐색으로 충분.
    """
    best = {"dT_end": 0.0, "s_tau": 1.0, "s_delay": 1.0}
    ranges = {"dT_end": (-2.5, 2.5), "s_tau": (0.4, 2.5), "s_delay": (0.05, 3.0)}
    lo = {"dT_end": -5.0, "s_tau": 0.05, "s_delay": 0.05}   # 물리 하한
    for stage in range(2):
        n = 9 if stage == 0 else 7
        grids = {k: np.linspace(*ranges[k], n) for k in ranges}
        best_e = None
        for dT in grids["dT_end"]:
            for st in grids["s_tau"]:
                for sd in grids["s_delay"]:
                    fit = {"dT_end": dT, "s_tau": st, "s_delay": sd}
                    e = rms(predict(ts, pts, cfg, ac, light, rack, fit) - T_meas)
                    if best_e is None or e < best_e:
                        best_e, best = e, fit
        # 다음 단계: 최적점 주변으로 좁힌다 (하한 밑으로는 안 내려간다)
        for k in ranges:
            step = (ranges[k][1] - ranges[k][0]) / (n - 1)
            ranges[k] = (max(best[k] - step, lo[k]), best[k] + step)
    return best, best_e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("measured", help="실측 probes.csv 경로")
    ap.add_argument("--label", default=None, help="결과 저장 라벨 (기본: 폴더명)")
    ap.add_argument("--ac", default="4.0,2.0", help="실측 당시 에어컨 위치 m")
    ap.add_argument("--light", type=float, default=0.0, help="점등률 0~1")
    args = ap.parse_args()
    label = args.label or os.path.basename(os.path.dirname(args.measured))
    ac = tuple(float(v) for v in args.ac.split(","))
    cfg = load_config(os.path.join(REPO, "geometry.json"))

    ts, pts, names, T_meas = load_measured(args.measured)
    # 부분 샘플링(속도) — 5초 간격이면 충분
    idx = np.arange(0, len(ts), max(1, int(round(5.0 / max(ts[1] - ts[0], 0.1)))))
    ts, T_meas = ts[idx], T_meas[idx]

    T0 = predict(ts, pts, cfg, ac, args.light, None)
    r0 = T0 - T_meas
    fit, e1 = inverse_fit(ts, pts, T_meas, cfg, ac, args.light, None)
    r1 = predict(ts, pts, cfg, ac, args.light, None, fit) - T_meas

    verdict = ("적합 — 파라미터 보정으로 충분" if e1 <= 0.5 else
               "주의 — 보정해도 잔차 있음" if e1 <= 1.0 else
               "불일치 — 모델 가정 자체가 틀림 (취출 방식 등)")
    per = {names[i]: round(float(np.sqrt(np.mean(r1[:, i] ** 2))), 3)
           for i in range(len(names))}
    worst = max(per, key=per.get)

    print("PINN_CHECK [%s]  %d시각 × %d점" % (label, len(ts), len(names)))
    print("  보정 전 RMS %.3f℃ (bias %+.3f)" % (rms(r0), float(r0.mean())))
    print("  역산: dT_end %+.2f℃ · s_tau ×%.2f · s_delay ×%.2f" %
          (fit["dT_end"], fit["s_tau"], fit["s_delay"]))
    print("  보정 후 RMS %.3f℃ · 최악점 %s %.3f℃" % (e1, worst, per[worst]))
    print("  판정: %s" % verdict)
    print("  해석: dT_end→열부하/UA_EFF, s_tau→풍량·믹싱, s_delay→취출 유로")

    out = {}
    if os.path.isfile(OUT_JSON):
        out = json.load(open(OUT_JSON, encoding="utf-8"))
    out[label] = {"measured": args.measured.replace("\\", "/"),
                  "ac": list(ac), "light": args.light,
                  "rms_before": round(rms(r0), 3), "rms_after": round(e1, 3),
                  "fit": {k: round(v, 3) for k, v in fit.items()},
                  "per_sensor_rms": per, "verdict": verdict,
                  "note": "임시 역산(격자 최소제곱) — 진짜 PINN 으로 교체 지점"}
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("  -> data/pinn_check.json [%s]" % label)


if __name__ == "__main__":
    main()
