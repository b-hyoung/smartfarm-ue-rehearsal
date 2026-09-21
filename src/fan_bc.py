"""유동팬 배치를 CFD 경계조건 초안과 케이스 목록으로 바꾼다.

    data/fan_layout.json   언리얼에서 잡은 팬 위치·방향·풍량
        ↓  (이 스크립트)
    data/fan_params.json   CFD 좌표의 팬 영역·운동량 소스·재배단 막힘·판정면·케이스 목록

⚠ 경계조건을 만들 뿐 기류를 예측하지 않는다. 캐노피 풍속은 OpenFOAM 을 다시 풀어야 나온다.
   팬은 벽면 패치가 아니라 유동 영역 안의 운동량 소스로 둔다. 방 안에 떠 있는 내부 순환
   장치이고, 힘만 주면 미는 쪽과 빨리는 쪽이 함께 풀려 질량 보존이 깨지지 않기 때문이다.

좌표 규약은 기존 계약을 따른다. CFD x = UE x − 4.0, y·z 는 그대로.

실행  py -m src.fan_bc
"""
from __future__ import annotations

import json
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_SHIFT = 4.0            # UE x − 4.0 = CFD x
RHO = 1.17               # 공기 밀도 kg/m³ (약 25 ℃)
BED_W, BED_D = 2.40, 0.80
BED_T, POST = 0.05, 0.06
TOP_MARGIN = 0.15
CANOPY_H = 0.25          # 작물 높이 가정
SAMPLE = 0.02            # 판정면 샘플 간격 m
ABOVE_BED = 0.18         # 선반면에서 팬 축까지
LED_ON = False           # 이번 계산은 조명 발열을 뺀다 (풍속 기준부터 잡는 단계)
LED_Z = [1.28, 1.60]
LED_W_EACH = 240.0
LED_BAR = (BED_W * 0.92, 0.05, 0.035)


def box(centre, size):
    """중심·크기(m) -> topoSet boxToCell 용 min/max."""
    return {"min": [round(centre[i] - size[i] / 2.0, 4) for i in range(3)],
            "max": [round(centre[i] + size[i] / 2.0, 4) for i in range(3)]}


def slots(layout, tilt, n, rack, tiers):
    """배치별 (중심 UE m, 흐름 방향, 역할, 태그). ue/sf_make_fans.py 와 같은 규칙."""
    out = []
    for ti, bz in enumerate(tiers):
        zc = bz + ABOVE_BED
        down = -math.tan(math.radians(tilt))
        if layout in ("pushpull", "ends"):
            ex = BED_W / 2.0 + 0.10
            ys = [rack[1] + BED_D * ((i + 0.5) / n - 0.5) for i in range(n)]
            for i, fy in enumerate(ys):
                out.append(((rack[0] - ex, fy, zc), (1.0, 0.0, down),
                            "supply", "t%d_s%d" % (ti, i)))
                out.append(((rack[0] + ex, fy, zc),
                            (1.0, 0.0, down if layout == "ends" else 0.0),
                            "booster" if layout == "ends" else "return", "t%d_r%d" % (ti, i)))
        elif layout == "side":
            xs = [rack[0] + BED_W * ((i + 0.5) / n - 0.5) for i in range(n)]
            for side in (-1, 1):
                fy = rack[1] + side * (BED_D / 2 + 0.06)
                for i, fx in enumerate(xs):
                    out.append(((fx, fy, zc), (0.0, float(-side), 0.0), "supply",
                                "t%d_%s%d" % (ti, "m" if side < 0 else "p", i)))
        elif layout == "top":
            m = max(2, n * 2)
            for i in range(m):
                fx = rack[0] + BED_W * ((i + 0.5) / m - 0.5)
                out.append(((fx, rack[1], bz + 0.55), (0.0, 0.0, -1.0), "supply",
                            "t%d_d%d" % (ti, i)))
    return out


def zones_for(layout, tilt, cmm, n, dia, depth, rack, tiers):
    """케이스 하나의 팬 영역 목록. 흐름축 방향만 얇은 상자로 잡는다."""
    area = math.pi * (dia / 2.0) ** 2
    q = cmm / 60.0
    u = (q / area) if q else 0.0
    thrust = RHO * q * u
    zs = []
    for (cx, cy, cz), d, role, tag in slots(layout, tilt, n, rack, tiers):
        nrm = math.sqrt(sum(v * v for v in d)) or 1.0
        d = [v / nrm for v in d]
        size = [depth if abs(d[0]) > 0.5 else dia,
                depth if abs(d[1]) > 0.5 else dia,
                depth if abs(d[2]) > 0.9 else dia]
        vol = size[0] * size[1] * size[2]
        zs.append({
            "id": "FAN_" + tag.upper(),
            "role": role,
            "centre_cfd_m": [round(cx - X_SHIFT, 4), round(cy, 4), round(cz, 4)],
            "cellZone_box_cfd_m": box([cx - X_SHIFT, cy, cz], size),
            "dir_unit": [round(v, 4) for v in d],
            "flow_m3s": round(q, 5),
            "outlet_m_s": round(u, 3),
            "thrust_N": round(thrust, 4),
            "momentum_source_N_m3": round(thrust / vol, 1) if vol else 0.0,
        })
    return zs, round(u, 3), round(thrust, 4)


# 케이스 정의 — (이름, 묶음, 배치, 대당 CMM, 기울기, 한쪽 대수, 재배단, 목적)
CASE_DEFS = [
    ("R0", "G0 기준선", "none", 0.0, 0.0, 1, False,
     "빈 방 — 재배단도 팬도 없다. 기존 해석과 같은 조건이라 재배단 효과를 떼어 볼 수 있다"),
    ("R1", "G0 기준선", "pushpull", 0.0, 15.0, 1, True,
     "재배단만, 팬 꺼짐 — 팬 효과를 재는 기준"),
    ("F1", "G1 풍량", "pushpull", 3.6, 15.0, 1, True, "캐노피 0.3 m/s 를 노린 풍량"),
    ("F2", "G1 풍량", "pushpull", 6.0, 15.0, 1, True, "캐노피 0.5 m/s — 표준안"),
    ("F3", "G1 풍량", "pushpull", 9.6, 15.0, 1, True, "캐노피 0.8 m/s — 상추 생육 최적 보고값"),
    ("F4", "G1 풍량", "pushpull", 12.0, 15.0, 1, True, "캐노피 1.0 m/s — 상한, 과하면 여기서 드러난다"),
    ("L1", "G2 배치", "side", 6.0, 0.0, 1, True, "긴 변 양쪽에서 마주보게 — 중앙 충돌 확인"),
    ("L2", "G2 배치", "ends", 6.0, 15.0, 1, True, "양 끝 팬을 같은 방향으로 — 방 전체 순환형"),
    ("L3", "G2 배치", "top", 6.0, 0.0, 1, True, "각 단 상부에서 캐노피로 하방"),
    ("T1", "G3 각도", "pushpull", 6.0, 0.0, 1, True, "수평 취출 — 기울임이 필요한지 판단"),
    ("T2", "G3 각도", "pushpull", 6.0, 30.0, 1, True, "30도 하방 — 과하면 바닥으로 빠진다"),
    ("N1", "G4 대수", "pushpull", 3.0, 15.0, 2, True,
     "한쪽에 2대로 나눠 달기. 합계 풍량은 F2 와 같다 — 길이 방향 균일도 비교"),
]


def main():
    lay = json.load(open(os.path.join(REPO, "data", "fan_layout.json"), encoding="utf-8"))
    spec = lay["spec"]
    dia, depth = float(spec["diam_m"]), 0.08
    rack = lay["rack_centre_ue_m"]
    tiers = lay["tier_bed_z_m"]
    area = math.pi * (dia / 2.0) ** 2

    # ── 판정면 — 어디서 재는지부터 고정한다 ──────────────────
    nx = int(round(BED_W / SAMPLE)) + 1
    ny = int(round(BED_D / SAMPLE)) + 1
    planes = []
    for i, bz in enumerate(tiers):
        for label, dz in (("mid", CANOPY_H / 2.0), ("top", CANOPY_H)):
            planes.append({
                "name": "tier%d_canopy_%s" % (i, label),
                "z_cfd_m": round(bz + dz, 3),
                "x_range_cfd_m": [round(rack[0] - X_SHIFT - BED_W / 2, 3),
                                  round(rack[0] - X_SHIFT + BED_W / 2, 3)],
                "y_range_m": [round(rack[1] - BED_D / 2, 3), round(rack[1] + BED_D / 2, 3)],
                "sample_grid": [nx, ny], "n_points": nx * ny,
            })

    # ── 재배단 막힘 ────────────────────────────────────────
    blockage = []
    for i, bz in enumerate(tiers):
        blockage.append({"name": "bed%d" % i,
                         "box_cfd_m": box([rack[0] - X_SHIFT, rack[1], bz - BED_T / 2],
                                          [BED_W, BED_D, BED_T])})
    ph = tiers[-1] + TOP_MARGIN
    for sx in (-1, 1):
        for sy in (-1, 1):
            blockage.append({
                "name": "post_%s%s" % ("m" if sx < 0 else "p", "m" if sy < 0 else "p"),
                "box_cfd_m": box([rack[0] - X_SHIFT + sx * (BED_W / 2 - POST / 2),
                                  rack[1] + sy * (BED_D / 2 - POST / 2), ph / 2],
                                 [POST, POST, ph])})

    heat = []
    if LED_ON:
        led_vol = LED_BAR[0] * LED_BAR[1] * LED_BAR[2]
        for i, lz in enumerate(LED_Z[:len(tiers)]):
            heat.append({"name": "led%d" % i,
                         "box_cfd_m": box([rack[0] - X_SHIFT, rack[1], lz], list(LED_BAR)),
                         "watt": LED_W_EACH,
                         "volumetric_W_m3": round(LED_W_EACH / led_vol, 0)})

    # ── 케이스 ────────────────────────────────────────────
    cases = []
    for name, grp, layout, cmm, tilt, n, rack_on, why in CASE_DEFS:
        if layout == "none":
            cases.append({"case": name, "group": grp, "layout": "none", "rack": False,
                          "fans": 0, "per_fan_CMM": 0.0, "purpose": why})
            continue
        zs, u, f = zones_for(layout, tilt, cmm, n, dia, depth, rack, tiers)
        sup = [z for z in zs if z["role"] == "supply"]
        cases.append({
            "case": name, "group": grp, "layout": layout, "rack": rack_on,
            "tilt_deg": tilt, "n_per_side": n, "fans": len(zs),
            "per_fan_CMM": cmm, "outlet_m_s": u, "thrust_N": f,
            "momentum_source_N_m3": zs[0]["momentum_source_N_m3"] if zs else 0.0,
            "stream_CMM_per_tier": round(cmm * len(sup) / max(1, len(tiers)), 2),
            "purpose": why,
            "fan_zones": zs if cmm else [],
        })

    out = {
        "note": "언리얼 배치에서 만든 CFD 경계조건 초안과 케이스 목록. 팬은 유동 영역 안의 "
                "운동량 소스로 둔다. 이 값으로 topoSetDict·fvOptions 를 만들고 OpenFOAM 을 "
                "다시 풀어야 캐노피 풍속이 나온다.",
        "coord_note": "CFD x = UE x - 4.0, y·z 동일",
        "lighting": {"included": LED_ON,
                     "note": "이번 계산은 조명 발열을 뺀다. 풍속 기준을 먼저 잡고 "
                             "조명은 스펙시트가 오면 넣는다."},
        "fan_spec": {"diam_m": dia, "depth_m": depth, "area_m2": round(area, 5),
                     "rho_kg_m3": RHO, "watt_each": spec["watt_each"],
                     "above_bed_m": ABOVE_BED},
        "rack_blockage": blockage,
        "heat_sources": heat,
        "judge_planes": planes,
        "airflow_criteria": {
            "where": "각 단 판정면 두 장 — 캐노피 중간(선반면 +0.125 m)과 윗면(+0.25 m). "
                     "방 전체 평균이 아니라 이 면에서만 잰다.",
            "band_m_s": [0.3, 1.0],
            "band_basis": "Kitaya 외(2003)는 0.01 -> 0.3 m/s 에서 증산·광합성이 두 배가 되고 "
                          "0.3~1.0 m/s 에서 거의 일정하다고 보고했다. Zhang & Kacira(2016)는 "
                          "0.3 미만과 1.0 초과를 피할 구간으로 두고 판정했다.",
            "metrics": [
                {"name": "적정구간 비율", "how": "판정면 점 중 0.3~1.0 m/s 인 비율",
                 "target": "높을수록 좋음", "ref": "Zhang & Kacira(2016) 최적안 64%"},
                {"name": "정체 비율", "how": "0.1 m/s 미만 점 비율", "target": "낮을수록 좋음",
                 "ref": "Gu & Goto(2024) 유입 풍속을 올려 62.4% -> 7.2%"},
                {"name": "상대표준편차", "how": "판정면 풍속 표준편차 / 평균",
                 "target": "낮을수록 좋음",
                 "ref": "Zhang & Kacira(2016) 44%, Sohn 외(2023) 33%, 배기구 추가 시 10%"},
                {"name": "평균 풍속", "how": "판정면 풍속 평균",
                 "target": "0.3 m/s 이상, 상추는 0.8 m/s 까지 유리",
                 "ref": "문승미 외(2015) 목표 0.3~0.5, 왕 외(2025) 0.8 m/s 에서 생육 최고"},
                {"name": "층간 차이", "how": "위 단과 아래 단 평균 풍속의 차",
                 "target": "작을수록 좋음", "ref": "다단 구조의 흔한 실패 지점"},
            ],
            "caution": "팬 토출 풍속과 캐노피 풍속은 다른 값이다. 기준은 캐노피 쪽이다.",
        },
        "cases": cases,
        "run_order": {
            "1_screening": "R0·R1·F1~F4 를 정상상태로 먼저 돌려 풍량 곡선을 잡는다",
            "2_layout": "풍량이 정해지면 그 값으로 L1~L3 을 돌려 배치를 고른다",
            "3_tuning": "고른 배치에서 T1·T2·N1 으로 각도와 대수를 다듬는다",
            "4_transient": "최종 조합만 900초 과도해석으로 돌려 기존 규격대로 반출한다",
        },
        "openfoam_hint": {
            "topoSetDict": "각 fan_zones[].cellZone_box_cfd_m 을 boxToCell 로 잡아 cellZone 생성",
            "fvOptions": "vectorSemiImplicitSource 로 zone 마다 dir_unit × thrust_N 적용 "
                         "(또는 meanVelocityForce 로 Ubar = dir_unit × outlet_m_s)",
            "blockage": "rack_blockage 는 snappyHexMesh 의 searchableBox 로 넣는다. "
                        "R0 만 빼고 모든 케이스에 들어간다.",
            "heat": "heat_sources 는 이번에 비어 있다. 조명을 넣을 때 cellZone + "
                    "scalarSemiImplicitSource(에너지)로 준다.",
            "sampling": "judge_planes 를 sample(surfaces, plane)로 뽑아 magU 를 저장하면 "
                        "적정구간 비율·정체 비율·상대표준편차를 그대로 계산할 수 있다.",
            "unchanged": "에어컨 취출·리턴 경계와 시각표·반출 규격은 그대로 둔다",
        },
    }
    p = os.path.join(REPO, "data", "fan_params.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    print("FAN_BC: 케이스 %d개 · 판정면 %d장(면당 %d점) · 재배단 막힘 %d개 · 조명 %s"
          % (len(cases), len(planes), planes[0]["n_points"], len(blockage),
             "포함" if LED_ON else "제외"))
    for c in cases:
        print("  %-3s %-8s %-9s 팬%2d  %5.1f CMM  %6s m/s  %7s N/m3  %s"
              % (c["case"], c["group"], c["layout"], c.get("fans", 0), c["per_fan_CMM"],
                 c.get("outlet_m_s", "-"), c.get("momentum_source_N_m3", "-"),
                 c["purpose"][:32]))
    print("  -> data/fan_params.json")


if __name__ == "__main__":
    main()
