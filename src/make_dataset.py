# -*- coding: utf-8 -*-
"""팬 스터디를 학습용 데이터셋(CSV)으로 묶는다 — PINO / PINN 입력용.

지금까지 케이스 정보는 세 군데에 흩어져 있었다.

    data/fan_params.json   케이스 조건 (중첩 JSON)
    data/judge.json        채점 결과 (중첩 JSON)
    <케이스>/postProcessing/canopy/<t>/U_*.raw   실제 장(場)

docs/FAN-RESULTS.md 는 "누가 언제 무엇을 돌렸나" 작업일지라 학습에 쓸 표가 아니다.
이 스크립트가 셋을 납작한 CSV 로 편다.

    data/fan-dataset/cases.csv    케이스 1 건 = 1 행. 방·재배단·팬·에어컨·격자·물리 조건 전부
    data/fan-dataset/scores.csv   (케이스 × 판정면) = 1 행. 분위수·평균·편차
    out/dataset/fields/<run_id>.csv
                              (판정면 × 시각 × 점) = 1 행. x y z Ux Uy Uz |U| T
                              용량이 커서 커밋하지 않는다(out/ 는 gitignore). 필요할 때 다시 만든다

좌표는 CFD 좌표다. UE x = CFD x + 4.0, y·z 는 같다.

⚠ 이 데이터에는 알려진 오류가 붙어 있다. cases.csv 의 err_* 열에 표시해 두었고
   docs/DATASET.md 와 docs/FAN-CFD-ERRATA.md 에 내용이 있다. 학습에 쓰기 전에 반드시 읽어라.

실행
    py -m src.make_dataset                 메타·점수만 (빠름)
    py -m src.make_dataset --fields        장(場) CSV 까지
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.environ.get("SF_WIND_ROOT",
                      os.path.expanduser("~/smartfarm-cfd/cases/fan-study"))
OUT_META = os.path.join(REPO, "data", "fan-dataset")
OUT_FIELD = os.path.join(REPO, "out", "dataset", "fields")     # 전체 (방 전체 단면 × 전 시각)
OUT_CASE = os.path.join(REPO, "data", "fan-dataset", "fields")     # 케이스별 (베드 × 채점 구간)

ROOM = {"shape": "half_ellipse", "Lx_m": 8.0, "Ly_m": 5.7, "Lz_m": 2.7,
        "volume_m3": 96.65, "flat_wall": "y=0", "semi_axis_a_m": 4.0, "semi_axis_b_m": 5.7}
BED_W, BED_D = 2.40, 0.80
TIERS = [0.55, 1.35]                 # 선반면 z (CFD)
PLANES = ["tier0_canopy_mid", "tier0_canopy_top",
          "tier1_canopy_mid", "tier1_canopy_top"]
WINDOW = list(range(300, 451, 30))


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as f:
        return json.load(f)


def wall_times():
    """times.csv -> {run_id: 벽시계 초}. 없으면 빈 dict."""
    p = os.path.join(RUNS, "times.csv")
    if not os.path.exists(p):
        return {}
    out = {}
    with io.open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if (r.get("wall_s") or "").isdigit():
                out[r["run_id"]] = int(r["wall_s"])
    return out


def mesh_cells(rid):
    """log.checkMesh 에서 셀 수. 다른 컴퓨터에서 받은 케이스는 없을 수 있다."""
    p = os.path.join(RUNS, rid, "log.checkMesh")
    if not os.path.exists(p):
        return ""
    m = re.search(r"^\s*cells:\s+(\d+)", io.open(p, encoding="utf-8", errors="replace").read(),
                  re.M)
    return m.group(1) if m else ""


def end_time(rid):
    """실제로 저장된 마지막 시각."""
    d = os.path.join(RUNS, rid, "postProcessing", "canopy")
    if not os.path.isdir(d):
        return ""
    ts = [float(x) for x in os.listdir(d) if x.replace(".", "").isdigit()]
    return ("%g" % max(ts)) if ts else ""


def snaps_in_window(rid):
    d = os.path.join(RUNS, rid, "postProcessing", "canopy")
    if not os.path.isdir(d):
        return 0
    return sum(1 for t in WINDOW if os.path.isdir(os.path.join(d, str(t))))


def fan_positions(c):
    """켜진 팬의 (x, y, z, 방향) 목록. slots() 규칙과 같다. 한 단 몫이 아니라 전부."""
    layout = c.get("layout", "none")
    n = c.get("n_per_side") or 0
    if not c.get("per_fan_CMM") or layout == "none":
        return []
    out = []
    h = c.get("fan_height_above_bed_m", 0.18)
    tilt = math.radians(c.get("tilt_deg", 0.0))
    for ti, bz in enumerate(TIERS):
        if layout == "top":
            k = max(2, n * 2)
            for i in range(k):
                out.append((round(-BED_W / 2 + BED_W * (i + 0.5) / k, 3), 2.0,
                            round(bz + 0.55, 3), 0.0, 0.0, -1.0))
        else:
            for i in range(n):
                fy = round(2.0 + BED_D * ((i + 0.5) / n - 0.5), 3)
                for sx in (-1, 1):
                    out.append((sx * (BED_W / 2 + 0.10), fy, round(bz + h, 3),
                                round(-sx * math.cos(tilt), 3), 0.0, round(-math.sin(tilt), 3)))
    return out


CASE_COLS = [
    # 식별
    "run_id", "no", "case", "group", "purpose",
    # 방 (모든 케이스 공통 — 학습 입력에 방 형상을 같이 주기 위해 행마다 반복한다)
    "room_shape", "room_Lx_m", "room_Ly_m", "room_Lz_m", "room_volume_m3",
    # 재배단
    "rack_present", "rack_x_cfd_m", "rack_y_cfd_m", "bed_w_m", "bed_d_m",
    "tier0_z_m", "tier1_z_m", "tier_pitch_m",
    "canopy_h_m", "canopy_d_1_m2", "canopy_f_1_m", "rack_top_open",
    # 팬
    "fan_layout", "fan_n_per_side", "fans_on", "fan_cmm_each", "fan_cmm_total",
    "fan_tilt_deg", "fan_height_above_bed_m", "fan_dia_m", "fan_depth_m",
    "fan_outlet_m_s", "fan_thrust_N", "fan_src_N_m3", "fan_positions",
    # 에어컨
    "ac_on", "ac_x_cfd_m", "ac_y_cfd_m", "ac_z_m", "ac_total_cmm",
    "ac_supply_T_K", "ac_direction", "ac_slot_area_modeled_m2", "ac_outlet_modeled_m_s",
    # 물리
    "solver", "turbulence", "lighting_included", "wall_T_K", "rackwall_T_K",
    "wall_heat_W", "rackwall_heat_W",
    # 격자·수치
    "mesh_base_m", "mesh_refined_m", "mesh_cells",
    # 실행
    "endTime_s", "snapshots_in_window", "wall_clock_s",
    # 알려진 오류
    "err_E004_ac_vertical", "err_E005_ac_slot_2x", "err_E006_rackwall_heat",
]


def build_cases(P):
    fs = P.get("fan_spec", {})
    can = P.get("canopy", {}) or {}
    ref = P.get("refine", {}) or {}
    wt = wall_times()
    rows = []
    for c in P["cases"]:
        rid = c["run_id"]
        ac = c.get("ac", {}) or {}
        acc = ac.get("centre_cfd_m", [0.0, 2.0, 2.7])
        sup = ac.get("supply", {}) or {}
        pos = fan_positions(c)
        rows.append({
            "run_id": rid, "no": c.get("no"), "case": c.get("case"),
            "group": c.get("group", ""), "purpose": (c.get("purpose") or "").strip(),

            "room_shape": ROOM["shape"], "room_Lx_m": ROOM["Lx_m"],
            "room_Ly_m": ROOM["Ly_m"], "room_Lz_m": ROOM["Lz_m"],
            "room_volume_m3": ROOM["volume_m3"],

            "rack_present": int(bool(c.get("rack"))),
            "rack_x_cfd_m": 0.0, "rack_y_cfd_m": 2.0,
            "bed_w_m": BED_W, "bed_d_m": BED_D,
            "tier0_z_m": TIERS[0], "tier1_z_m": TIERS[1],
            "tier_pitch_m": round(TIERS[1] - TIERS[0], 3),
            "canopy_h_m": can.get("height_m", 0.25),
            "canopy_d_1_m2": can.get("d_1_per_m2", 25.0),
            "canopy_f_1_m": can.get("f_1_per_m", 1.3),
            "rack_top_open": 1,          # 위 단 위로 막힘이 없다

            "fan_layout": c.get("layout", "none"),
            "fan_n_per_side": c.get("n_per_side") or 0,
            "fans_on": c.get("fans_on", 0),
            "fan_cmm_each": c.get("per_fan_CMM", 0.0) or 0.0,
            "fan_cmm_total": round((c.get("per_fan_CMM") or 0.0) * (c.get("fans_on") or 0), 3),
            "fan_tilt_deg": c.get("tilt_deg", 0.0),
            "fan_height_above_bed_m": c.get("fan_height_above_bed_m", 0.18),
            "fan_dia_m": fs.get("diam_m", 0.2), "fan_depth_m": fs.get("depth_m", 0.08),
            "fan_outlet_m_s": c.get("outlet_m_s", 0.0),
            "fan_thrust_N": c.get("thrust_N", 0.0),
            "fan_src_N_m3": c.get("momentum_source_N_m3", 0.0),
            "fan_positions": ";".join("%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % p for p in pos),

            "ac_on": int(bool(ac.get("on", True))),
            "ac_x_cfd_m": acc[0], "ac_y_cfd_m": acc[1],
            "ac_z_m": acc[2] if len(acc) > 2 else 2.7,
            "ac_total_cmm": sup.get("total_CMM", 25),
            "ac_supply_T_K": sup.get("temperature_K", 289.5),
            "ac_direction": "vertical_down",      # ⚠ 실물은 4Way 베인 25°. E-004
            "ac_slot_area_modeled_m2": 0.060,     # ⚠ 실측. 가정 0.030 의 2 배. E-005
            "ac_outlet_modeled_m_s": 1.74,        # = (25/4)/60 / 0.060

            "solver": "buoyantPimpleFoam", "turbulence": "kEpsilon",
            "lighting_included": int(bool((P.get("lighting") or {}).get("included", False))),
            "wall_T_K": 302.0, "rackwall_T_K": 302.0,
            "wall_heat_W": 1458.5,        # 05_F3 600 s 실측 (wallHeatFlux)
            "rackwall_heat_W": 278.3,     # 05_F3 600 s 실측. E-006

            "mesh_base_m": P.get("mesh_cell_m", 0.10),
            "mesh_refined_m": ref.get("refined_cell_m", 0.05),
            "mesh_cells": mesh_cells(rid),

            "endTime_s": end_time(rid),
            "snapshots_in_window": snaps_in_window(rid),
            "wall_clock_s": wt.get(rid, ""),

            "err_E004_ac_vertical": 1, "err_E005_ac_slot_2x": 1,
            "err_E006_rackwall_heat": int(bool(c.get("rack"))),
        })
    return rows


SCORE_COLS = ["run_id", "plane", "tier", "plane_z_m", "window_from_s", "window_to_s",
              "snapshots", "n_points", "P10", "P50", "P90", "mean", "cov",
              "band_ratio", "stagnant_ratio", "spread", "P10_drift_pct",
              "T_mean_C", "T_sd", "pass_low", "pass_high"]


def build_scores(J, P):
    zof = {p["name"]: p["z_cfd_m"] for p in P.get("judge_planes", [])}
    rows = []
    for c in J.get("cases", []):
        w = c.get("window_s", [None, None])
        for name, s in (c.get("planes") or {}).items():
            rows.append({
                "run_id": c["run_id"], "plane": name,
                "tier": 0 if name.startswith("tier0") else 1,
                "plane_z_m": zof.get(name, ""),
                "window_from_s": w[0], "window_to_s": w[1],
                "snapshots": s.get("snapshots"), "n_points": s.get("n"),
                "P10": s.get("P10"), "P50": s.get("P50"), "P90": s.get("P90"),
                "mean": s.get("mean"), "cov": s.get("cov"),
                "band_ratio": s.get("band_ratio"), "stagnant_ratio": s.get("stagnant_ratio"),
                "spread": s.get("spread"), "P10_drift_pct": s.get("P10_drift_pct"),
                "T_mean_C": s.get("T_mean_C"), "T_sd": s.get("T_sd"),
                "pass_low": int(bool(c.get("pass_low"))), "pass_high": int(bool(c.get("pass_high"))),
            })
    return rows


FIELD_COLS = ["run_id", "plane", "tier", "t_s", "x_m", "y_m", "z_m",
              "Ux", "Uy", "Uz", "magU", "T_K", "in_bed", "in_window"]

# 판정면은 방 전체 단면을 자른 것이라 재배 베드 바깥 점도 들어 있다.
# 채점은 베드 안만 쓰지만(E-002), 학습에는 방 전체가 오히려 쓸모 있어 전부 남기고
# in_bed 로 구분만 해 둔다. in_window 는 채점 구간(300~450 s) 여부다.
BED_X = (-1.2, 1.2)
BED_Y = (1.6, 2.4)


def write_fields(rid, window_only=False, bed_only=False, outdir=None):
    """한 케이스의 판정면 원시값을 CSV 한 장으로. (면 × 시각 × 점)

    window_only=True 면 채점 구간 300~450 s 여섯 장만 쓴다. 용량이 1/3 로 준다.
    """
    base = os.path.join(RUNS, rid, "postProcessing", "canopy")
    if not os.path.isdir(base):
        return 0
    d = outdir or OUT_FIELD
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, rid + ".csv")
    rows = 0
    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELD_COLS)
        for t in sorted(os.listdir(base), key=lambda s: float(s) if s.replace(".", "").isdigit() else 1e9):
            if not t.replace(".", "").isdigit():
                continue
            tv = float(t)
            if window_only and int(tv) not in WINDOW:
                continue
            for pl in PLANES:
                fu = os.path.join(base, t, "U_%s.raw" % pl)
                ft = os.path.join(base, t, "T_%s.raw" % pl)
                if not os.path.exists(fu):
                    continue
                T = {}
                if os.path.exists(ft):
                    for line in io.open(ft, encoding="utf-8", errors="replace"):
                        if not line.strip() or line[0] == "#":
                            continue
                        p = line.split()
                        if len(p) >= 4:
                            T[(round(float(p[0]), 4), round(float(p[1]), 4),
                               round(float(p[2]), 4))] = p[3]
                for line in io.open(fu, encoding="utf-8", errors="replace"):
                    if not line.strip() or line[0] == "#":
                        continue
                    p = line.split()
                    if len(p) < 6:
                        continue
                    x, y, z = (round(float(p[0]), 4), round(float(p[1]), 4),
                               round(float(p[2]), 4))
                    in_bed = int(BED_X[0] <= x <= BED_X[1] and BED_Y[0] <= y <= BED_Y[1])
                    if bed_only and not in_bed:
                        continue
                    ux, uy, uz = float(p[3]), float(p[4]), float(p[5])
                    w.writerow([rid, pl, 0 if pl.startswith("tier0") else 1, t,
                                x, y, z, "%.5g" % ux, "%.5g" % uy, "%.5g" % uz,
                                "%.5g" % math.sqrt(ux * ux + uy * uy + uz * uz),
                                T.get((x, y, z), ""), in_bed, int(int(tv) in WINDOW)])
                    rows += 1
    return rows


def dump(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("%-42s %6d 행  %5d KB" % (os.path.relpath(path, REPO), len(rows),
                                    os.path.getsize(path) // 1024))


def main():
    global RUNS
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", action="store_true", help="장(場) CSV 까지 만든다 (느리고 크다)")
    ap.add_argument("--window-only", action="store_true",
                    help="장(場)을 채점 구간 300~450 s 여섯 장으로 줄인다")
    ap.add_argument("--runs", default=RUNS)
    a = ap.parse_args()
    RUNS = a.runs

    P, J = load("fan_params.json"), load("judge.json")
    dump(os.path.join(OUT_META, "cases.csv"), CASE_COLS, build_cases(P))
    dump(os.path.join(OUT_META, "scores.csv"), SCORE_COLS, build_scores(J, P))

    # 케이스별 CSV — 재배 베드 × 채점 구간만. 작아서 저장소에 같이 둔다.
    print()
    ids = sorted(d for d in os.listdir(RUNS)
                 if d[:1].isdigit() and os.path.isdir(os.path.join(RUNS, d)))
    total = 0
    for rid in ids:
        n = write_fields(rid, window_only=True, bed_only=True, outdir=OUT_CASE)
        if n:
            kb = os.path.getsize(os.path.join(OUT_CASE, rid + ".csv")) // 1024
            print("  data/fan-dataset/fields/%-13s %7d 행  %5d KB" % (rid + ".csv", n, kb))
            total += n
    print("케이스별 합계 %d 행" % total)

    if a.fields:
        print()
        total = 0
        for rid in ids:
            n = write_fields(rid, a.window_only)
            if n:
                print("  out/dataset/fields/%-13s %9d 행" % (rid + ".csv", n))
                total += n
        print("전체 장(場) 합계 %d 행" % total)
    else:
        print("\n방 전체 단면·전 시각이 필요하면 --fields"
              " (케이스당 약 35 MB, out/ 는 커밋하지 않는다)")


if __name__ == "__main__":
    main()
