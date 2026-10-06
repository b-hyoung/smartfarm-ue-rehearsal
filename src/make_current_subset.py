# -*- coding: utf-8 -*-
"""현재 운전 상황에 맞는 케이스만 골라 대리모델 1차 학습표를 만든다.

현재 상황 = 에어컨 기준 위치(CFD 0, 2) · 마주보기 배치(pushpull) · 한쪽 1대 · 기울기 15° ·
팬 높이 선반면 +0.18 m. 여기서 바뀌는 것은 팬 네 대 각각의 풍량(꺼짐 = 0)뿐이다.

    02 R1 (전부 꺼짐) + 03~08 F1~F6 (풍량) + 09~14 S1~S6 (켜고 끄기) = 13 케이스

빠진 것과 이유
    01 R0        재배단이 없다
    15~17 L1~L3  배치가 다르다 (순환형, 상부 하방)
    18~20 T1~T3  기울기가 다르다 (채점 결과도 없다)
    21~22 N1~N2  대수가 다르다
    23~24 H1~H2  팬 높이가 다르다
    25~30 A1~A6  에어컨 위치가 다르다 (E-003, 저장본 1 장 케이스 포함)

입력  cmm_T0_S cmm_T0_R cmm_T1_S cmm_T1_R  (T0 아래 단, T1 위 단, S 송풍기, R 흡입기)
출력  두 단 캐노피 중간면의 적정 면적·P10·P90·평균 기온·기온 편차 (scores.csv 그대로)

실행
    py -m src.make_current_subset          -> data/fan-dataset/current_subset.csv
"""
from __future__ import annotations

import csv
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
OUT = os.path.join(DATA, "fan-dataset", "current_subset.csv")

FANS = ["FAN_T0_S0", "FAN_T0_R0", "FAN_T1_S0", "FAN_T1_R0"]
HOME = {"ac_xy": (0.0, 2.0), "layout": "pushpull", "n_per_side": 1,
        "tilt_deg": 15.0, "fan_height_above_bed_m": 0.18}
PLANE = "canopy_mid"
METRICS = ["band_ratio", "P10", "P90", "T_mean_C", "T_sd"]


def matches_home(c):
    if not c.get("rack"):
        return False
    ac = tuple((c.get("ac") or {}).get("centre_cfd_m", [0.0, 2.0])[:2])
    if ac != HOME["ac_xy"]:
        return False
    if c.get("layout") != HOME["layout"]:
        return False
    if not c.get("fans_on"):
        return True                      # 전부 꺼짐 — 배치·각도·높이는 의미가 없다
    return ((c.get("n_per_side") or 0) == HOME["n_per_side"]
            and float(c.get("tilt_deg", 0)) == HOME["tilt_deg"]
            and float(c.get("fan_height_above_bed_m", 0)) == HOME["fan_height_above_bed_m"])


def fan_cmm(c):
    on = {z["id"] for z in c.get("fan_zones") or []}
    cmm = float(c.get("per_fan_CMM") or 0.0)
    return [cmm if f in on else 0.0 for f in FANS]


def main():
    with io.open(os.path.join(DATA, "fan_params.json"), encoding="utf-8") as f:
        P = json.load(f)
    with io.open(os.path.join(DATA, "fan-dataset", "scores.csv"), encoding="utf-8") as f:
        S = {}
        for r in csv.DictReader(f):
            if r["plane"].endswith(PLANE):
                S.setdefault(r["run_id"], {})[r["tier"]] = r

    cols = (["run_id", "case", "purpose"] + ["cmm_" + f[4:8] for f in FANS] + ["cmm_total"]
            + ["t%s_%s" % (t, m) for t in ("0", "1") for m in METRICS])
    rows, skipped = [], []
    for c in P["cases"]:
        rid = c["run_id"]
        if not matches_home(c):
            continue
        if rid not in S or set(S[rid]) != {"0", "1"}:
            skipped.append(rid)
            continue
        q = fan_cmm(c)
        row = {"run_id": rid, "case": c.get("case"),
               "purpose": (c.get("purpose") or "").split(" — ")[0].strip(),
               "cmm_total": round(sum(q), 3)}
        row.update({"cmm_" + f[4:8]: v for f, v in zip(FANS, q)})
        for t in ("0", "1"):
            for m in METRICS:
                row["t%s_%s" % (t, m)] = S[rid][t][m]
        rows.append(row)

    with io.open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("%d 케이스 -> %s" % (len(rows), os.path.relpath(OUT, REPO)))
    if skipped:
        print("조건은 맞지만 채점 결과가 없어 뺀 케이스:", ", ".join(skipped))


if __name__ == "__main__":
    main()
