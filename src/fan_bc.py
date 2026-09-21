"""유동팬 배치를 CFD 경계조건 초안으로 바꾼다.

    data/fan_layout.json   언리얼에서 잡은 팬 위치·방향·풍량
        ↓  (이 스크립트)
    data/fan_params.json   CFD 좌표의 팬 영역 상자 · 운동량 소스 · 재배단 막힘 형상

⚠ 이 스크립트는 **경계조건을 만들 뿐 기류를 예측하지 않는다.** 캐노피 풍속 분포는
   OpenFOAM 을 다시 풀어야 나온다. 팬을 벽면 패치로 두지 않고 유동 영역 안의
   운동량 소스(fvOptions)로 두는 이유는, 팬이 방 안에 떠 있는 내부 순환 장치이고
   질량 보존을 깨지 않아야 하기 때문이다.

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


def load_layout():
    p = os.path.join(REPO, "data", "fan_layout.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def box(centre, size):
    """중심·크기(m) -> topoSet boxToCell 용 min/max."""
    return {"min": [round(centre[i] - size[i] / 2.0, 4) for i in range(3)],
            "max": [round(centre[i] + size[i] / 2.0, 4) for i in range(3)]}


def main():
    lay = load_layout()
    spec = lay["spec"]
    dia = float(spec["diam_m"])
    depth = 0.08
    area = math.pi * (dia / 2.0) ** 2
    q = float(spec["per_fan_CMM"]) / 60.0          # m³/s
    u = q / area                                   # 토출 풍속 m/s
    rack = lay["rack_centre_ue_m"]
    tiers = lay["tier_bed_z_m"]

    zones, notes = [], []
    for f in lay["fans"]:
        if f["role"] == "return":
            # 흡입기도 같은 방향으로 공기를 밀어내는 장치다. 방향 벡터는 급기와 같게 둔다.
            d = [1.0, 0.0, 0.0]
        else:
            d = f["dir_unit"]
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        d = [v / n for v in d]
        c = f["centre_ue_m"]
        cfd_c = [round(c[0] - X_SHIFT, 4), c[1], c[2]]
        # 팬 두께 방향으로 얇은 상자. 흐름 축이 x 이므로 x 만 depth, 나머지는 지름.
        size = [depth if abs(d[0]) > 0.5 else dia,
                depth if abs(d[1]) > 0.5 else dia,
                depth if abs(d[2]) > 0.9 else dia]
        vol = size[0] * size[1] * size[2]
        thrust = RHO * q * u                        # N — 팬이 공기에 주는 힘
        zones.append({
            "id": f["id"],
            "tier": f["tier"],
            "role": f["role"],
            "cellZone_box_cfd_m": box(cfd_c, size),
            "centre_cfd_m": cfd_c,
            "dir_unit": [round(v, 4) for v in d],
            "flow_m3s": round(q, 5),
            "outlet_m_s": round(u, 3),
            "zone_volume_m3": round(vol, 6),
            "thrust_N": round(thrust, 4),
            "momentum_source_N_m3": round(thrust / vol, 1),
        })

    # 재배단 막힘 — 지금 CFD 는 빈 방이라 이 형상을 넣어야 캐노피 기류가 의미를 갖는다
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

    per_tier = lay["per_tier"]
    out = {
        "note": "언리얼 배치에서 만든 CFD 경계조건 초안. 팬은 벽면 패치가 아니라 유동 영역 "
                "안의 운동량 소스로 둔다. 이 값으로 topoSetDict·fvOptions 를 만들고 "
                "OpenFOAM 을 다시 풀어야 캐노피 풍속이 나온다.",
        "coord_note": "CFD x = UE x - 4.0, y·z 동일",
        "layout": spec["layout"],
        "fan_spec": {"diam_m": dia, "depth_m": depth, "area_m2": round(area, 5),
                     "per_fan_CMM": spec["per_fan_CMM"], "per_fan_m3s": round(q, 5),
                     "outlet_m_s": round(u, 3), "rho_kg_m3": RHO,
                     "watt_each": spec["watt_each"], "tilt_deg": spec["tilt_deg"]},
        "fan_zones": zones,
        "rack_blockage": blockage,
        "expected": {
            "canopy_section_m2": per_tier["canopy_section_m2"],
            "canopy_mean_m_s_est": per_tier["canopy_mean_m_s_est"],
            "judge": "캐노피 평균 0.3 m/s 이상, 정체(0.1 m/s 미만) 비율과 상대표준편차로 판정. "
                     "상추는 0.8 m/s 까지 생육이 좋아졌다는 보고가 있다.",
        },
        "openfoam_hint": {
            "topoSetDict": "각 fan_zones[].cellZone_box_cfd_m 을 boxToCell 로 잡아 cellZone 생성",
            "fvOptions": "vectorSemiImplicitSource 로 zone 마다 dir_unit × thrust_N 적용 "
                         "(또는 meanVelocityForce 로 Ubar = dir_unit × outlet_m_s)",
            "blockage": "rack_blockage 는 snappyHexMesh 의 searchableBox 또는 topoSet 후 "
                        "cellSet 제거로 넣는다. 지금 해석은 빈 방이라 반드시 추가해야 한다.",
            "unchanged": "에어컨 취출·리턴 경계(ac_params.json)와 시각표·반출 규격은 그대로 둔다",
        },
    }
    p = os.path.join(REPO, "data", "fan_params.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    print("FAN_BC[%s]: 팬 %d개 · 대당 %.1f CMM(%.2f m/s) · 추력 %.3f N · 소스 %.0f N/m³"
          % (spec["layout"], len(zones), spec["per_fan_CMM"], u,
             zones[0]["thrust_N"], zones[0]["momentum_source_N_m3"]))
    print("  재배단 막힘 상자 %d개 (선반 %d, 기둥 4)" % (len(blockage), len(tiers)))
    print("  캐노피 기대값 %.2f m/s (통과 단면 %.2f m²)"
          % (per_tier["canopy_mean_m_s_est"], per_tier["canopy_section_m2"]))
    print("  -> data/fan_params.json")


if __name__ == "__main__":
    main()
