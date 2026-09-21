"""유동팬 배치를 CFD 경계조건 초안과 케이스 목록으로 바꾼다.

    data/fan_layout.json   언리얼에서 잡은 팬 위치·방향·풍량
    data/ac_params.json    에어컨 취출·리턴 경계 (위치를 옮기면 같은 크기로 평행이동)
        ↓  (이 스크립트)
    data/fan_params.json   CFD 좌표의 팬 영역·재배단 막힘·판정면·에어컨 경계·케이스 목록

⚠ 경계조건을 만들 뿐 기류를 예측하지 않는다. 캐노피 풍속은 OpenFOAM 을 다시 풀어야 나온다.
   팬은 벽면 패치가 아니라 유동 영역 안의 운동량 소스로 둔다. 방 안에 떠 있는 내부 순환
   장치이고, 힘만 주면 미는 쪽과 빨리는 쪽이 함께 풀려 질량 보존이 깨지지 않기 때문이다.

에어컨은 어느 케이스에서도 끄지 않는다. 위치만 옮긴다.
재배단 위치는 전 케이스 고정이다.

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
ABOVE_BED = 0.18         # 선반면에서 팬 축까지 (기본)
AC_HOME = (4.0, 2.0)     # ac_params.json 이 기록된 에어컨 위치
LED_ON = False           # 이번 계산은 조명 발열을 뺀다 (풍속 기준부터 잡는 단계)
LED_Z = [1.28, 1.60]
LED_W_EACH = 240.0
LED_BAR = (BED_W * 0.92, 0.05, 0.035)


MESH_CELL = 0.10         # blockMesh 균일 격자 한 변(m). 상자를 여기에 맞춘다.


def box(centre, size):
    """중심·크기(m) -> topoSet boxToCell 용 min/max."""
    return {"min": [round(centre[i] - size[i] / 2.0, 4) for i in range(3)],
            "max": [round(centre[i] + size[i] / 2.0, 4) for i in range(3)]}


def zone_box(centre, size, cell=MESH_CELL):
    """셀 영역용 상자. 격자보다 얇으면 셀 중심을 하나도 못 잡으므로 최소 한 셀은 덮게 키운다.

    boxToCell 은 셀 중심이 상자 안에 있는 셀만 고른다. 균일 격자에서 한 변보다
    짧은 상자는 정렬에 따라 0개가 잡힌다. 한 변의 1.2배까지 키우면 어디에 놓든
    축마다 최소 한 줄은 들어온다. 운동량 소스는 volumeMode absolute 라
    상자가 커져도 팬이 내는 총 추력(N)은 그대로다.
    """
    return box(centre, [max(size[i], cell * 1.2) for i in range(3)])


def slots(layout, tilt, n, rack, tiers, above_bed=ABOVE_BED):
    """배치별 (중심 UE m, 흐름 방향, 역할, 태그). ue/sf_make_fans.py 와 같은 규칙."""
    out = []
    for ti, bz in enumerate(tiers):
        zc = bz + above_bed
        down = -math.tan(math.radians(tilt))
        if layout in ("pushpull", "ends"):
            ex = BED_W / 2.0 + 0.10
            ys = [rack[1] + BED_D * ((i + 0.5) / n - 0.5) for i in range(n)]
            for i, fy in enumerate(ys):
                out.append(((rack[0] - ex, fy, zc), (1.0, 0.0, down),
                            "supply", "t%d_s%d" % (ti, i)))
                out.append(((rack[0] + ex, fy, zc),
                            (1.0, 0.0, down if layout == "ends" else 0.0),
                            "booster" if layout == "ends" else "return",
                            "t%d_r%d" % (ti, i)))
        elif layout == "top":
            m = max(2, n * 2)
            for i in range(m):
                fx = rack[0] + BED_W * ((i + 0.5) / m - 0.5)
                out.append(((fx, rack[1], bz + 0.55), (0.0, 0.0, -1.0), "supply",
                            "t%d_d%d" % (ti, i)))
    return out


def zones_for(layout, tilt, cmm, n, dia, depth, rack, tiers, on=None, above_bed=ABOVE_BED):
    """케이스 하나의 팬 영역 목록. 흐름축 방향만 얇은 상자로 잡는다.

    on = {"tiers": [...], "roles": [...]} 로 켤 팬만 고른다.
    꺼진 팬은 영역을 만들지 않는다. 몸체가 아주 약간 막기는 하지만 무시한다.
    """
    on = on or {}
    on_tiers, on_roles = on.get("tiers"), on.get("roles")
    on_pairs = on.get("pairs")          # [(tier, role), ...] 로 콕 집어 켜기
    area = math.pi * (dia / 2.0) ** 2
    q = cmm / 60.0
    u = (q / area) if q else 0.0
    thrust = RHO * q * u
    zs, off = [], []
    for (cx, cy, cz), d, role, tag in slots(layout, tilt, n, rack, tiers, above_bed):
        ti = int(tag[1])
        skip = False
        if on_pairs is not None:
            skip = [ti, role] not in [list(p) for p in on_pairs]
        else:
            skip = ((on_tiers is not None and ti not in on_tiers) or
                    (on_roles is not None and role not in on_roles))
        if skip:
            off.append("FAN_" + tag.upper())
            continue
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
            "cellZone_box_cfd_m": zone_box([cx - X_SHIFT, cy, cz], size),
            "fan_box_cfd_m": box([cx - X_SHIFT, cy, cz], size),
            "dir_unit": [round(v, 4) for v in d],
            "flow_m3s": round(q, 5),
            "outlet_m_s": round(u, 3),
            "thrust_N": round(thrust, 4),
            "momentum_source_N_m3": round(thrust / vol, 1) if vol else 0.0,
            "box_note": "fan_box 는 실제 팬 치수, cellZone_box 는 격자(0.10 m)에 "
                        "맞춰 키운 것이다. 총 추력은 같다.",
        })
    return zs, round(u, 3), round(thrust, 4), off


def blockage_for(rack, tiers):
    """재배단 막힘 상자 — 선반 2장과 기둥 4개."""
    out = []
    for i, bz in enumerate(tiers):
        out.append({"name": "bed%d" % i,
                    "box_cfd_m": box([rack[0] - X_SHIFT, rack[1], bz - BED_T / 2],
                                     [BED_W, BED_D, BED_T])})
    ph = tiers[-1] + TOP_MARGIN
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append({"name": "post_%s%s" % ("m" if sx < 0 else "p", "m" if sy < 0 else "p"),
                        "box_cfd_m": box([rack[0] - X_SHIFT + sx * (BED_W / 2 - POST / 2),
                                          rack[1] + sy * (BED_D / 2 - POST / 2), ph / 2],
                                         [POST, POST, ph])})
    return out


def planes_for(rack, tiers):
    """판정면 — 단마다 캐노피 중간과 윗면 두 장."""
    nx = int(round(BED_W / SAMPLE)) + 1
    ny = int(round(BED_D / SAMPLE)) + 1
    out = []
    for i, bz in enumerate(tiers):
        for label, dz in (("mid", CANOPY_H / 2.0), ("top", CANOPY_H)):
            out.append({
                "name": "tier%d_canopy_%s" % (i, label),
                "z_cfd_m": round(bz + dz, 3),
                "x_range_cfd_m": [round(rack[0] - X_SHIFT - BED_W / 2, 3),
                                  round(rack[0] - X_SHIFT + BED_W / 2, 3)],
                "y_range_m": [round(rack[1] - BED_D / 2, 3), round(rack[1] + BED_D / 2, 3)],
                "sample_grid": [nx, ny], "n_points": nx * ny,
            })
    return out


def ac_for(ac_pos, tmpl):
    """에어컨 경계 — 기록된 상자를 통째로 평행이동한다. 끄는 케이스는 없다."""
    dx = ac_pos[0] - AC_HOME[0]
    dy = ac_pos[1] - AC_HOME[1]
    boxes = {}
    for k, b in tmpl["topoSet_boxes"].items():
        boxes[k] = {"min": [round(b["min"][0] + dx, 4), round(b["min"][1] + dy, 4), b["min"][2]],
                    "max": [round(b["max"][0] + dx, 4), round(b["max"][1] + dy, 4), b["max"][2]]}
    return {"centre_ue_m": [ac_pos[0], ac_pos[1], 2.7],
            "centre_cfd_m": [round(ac_pos[0] - X_SHIFT, 4), ac_pos[1], 2.7],
            "shift_from_home_m": [round(dx, 4), round(dy, 4)],
            "topoSet_boxes_cfd_m": boxes,
            "supply": tmpl["supply"], "on": True}


ALL_ON = {"tiers": [0, 1], "roles": ["supply", "return", "booster"]}

# (이름, 묶음, 배치, 대당 CMM, 기울기, 한쪽 대수, 재배단 유무, 켤 팬, 팬 높이, 재배단 위치, 에어컨 위치, 목적)
CASE_DEFS = [
    # ── G0 기준선 ────────────────────────────────────────────────
    ("R0", "G0 기준선", "none", 0.0, 0.0, 1, False, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "빈 방 — 재배단도 팬도 없다. 기존 해석과 같은 조건이라 재배단 효과를 떼어 볼 수 있다"),
    ("R1", "G0 기준선", "pushpull", 0.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "재배단만, 팬 꺼짐 — 팬 효과를 재는 기준"),
    # ── G1 풍량 ─────────────────────────────────────────────────
    ("F1", "G1 풍량", "pushpull", 3.6, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "캐노피 0.3 m/s 를 노린 풍량 — 하한"),
    ("F2", "G1 풍량", "pushpull", 4.8, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "캐노피 0.4 m/s"),
    ("F3", "G1 풍량", "pushpull", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "캐노피 0.5 m/s — 표준안"),
    ("F4", "G1 풍량", "pushpull", 7.2, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "캐노피 0.6 m/s"),
    ("F5", "G1 풍량", "pushpull", 9.6, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "캐노피 0.8 m/s — 상추 생육 최적 보고값"),
    ("F6", "G1 풍량", "pushpull", 12.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "캐노피 1.0 m/s — 상한, 과하면 여기서 드러난다"),
    # ── G2 켜고 끄기 (팬만, 에어컨은 계속 켠다) ──────────────────
    ("S1", "G2 켜고 끄기", "pushpull", 6.0, 15.0, 1, True,
     {"tiers": [0], "roles": ["supply", "return"]}, ABOVE_BED, None, (4.0, 2.0),
     "아래 단만 켬 — 위 단이 아래 단 기류에 묻어가는지"),
    ("S2", "G2 켜고 끄기", "pushpull", 6.0, 15.0, 1, True,
     {"tiers": [1], "roles": ["supply", "return"]}, ABOVE_BED, None, (4.0, 2.0),
     "위 단만 켬 — 위에서 분 바람이 아래 단으로 떨어지는지"),
    ("S3", "G2 켜고 끄기", "pushpull", 6.0, 15.0, 1, True,
     {"tiers": [0, 1], "roles": ["supply"]}, ABOVE_BED, None, (4.0, 2.0),
     "송풍기만 켬, 흡입기 끔 — 흡입기가 정말 필요한지"),
    ("S4", "G2 켜고 끄기", "pushpull", 6.0, 15.0, 1, True,
     {"tiers": [0, 1], "roles": ["return"]}, ABOVE_BED, None, (4.0, 2.0),
     "흡입기만 켬, 송풍기 끔 — 당기기만으로 캐노피가 뚫리는지"),
    ("S5", "G2 켜고 끄기", "pushpull", 6.0, 15.0, 1, True,
     {"pairs": [[0, "supply"], [1, "return"]]}, ABOVE_BED, None, (4.0, 2.0),
     "아래 단 송풍 + 위 단 흡입만 — 두 단을 하나의 흐름으로 묶을 수 있는지"),
    ("S6", "G2 켜고 끄기", "pushpull", 12.0, 15.0, 1, True,
     {"tiers": [0, 1], "roles": ["supply"]}, ABOVE_BED, None, (4.0, 2.0),
     "송풍기만 켜고 풍량 두 배 — 대수를 줄이는 대신 세게 부는 안"),
    # ── G3 배치 ─────────────────────────────────────────────────
    ("L1", "G3 배치", "ends", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "양 끝 팬을 같은 방향으로 — 방 전체를 도는 순환형"),
    ("L2", "G3 배치", "top", 6.0, 0.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "각 단 상부에서 캐노피로 하방, 단당 2대"),
    ("L3", "G3 배치", "top", 3.0, 0.0, 2, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "상부 하방을 단당 4대로 나눔 — 합계 풍량은 L2 와 같다"),
    # ── G4 각도 ─────────────────────────────────────────────────
    ("T1", "G4 각도", "pushpull", 6.0, 0.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "수평 취출 — 기울임이 필요한지 판단"),
    ("T2", "G4 각도", "pushpull", 6.0, 30.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "30도 하방 — 과하면 바닥으로 빠진다"),
    ("T3", "G4 각도", "pushpull", 6.0, 45.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "45도 하방 — 캐노피를 찌르는 쪽으로 기울인 극단"),
    # ── G5 대수 ─────────────────────────────────────────────────
    ("N1", "G5 대수", "pushpull", 3.0, 15.0, 2, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "한쪽에 2대씩 총 8대. 합계 풍량은 F3 과 같다 — 길이 방향 균일도 비교"),
    ("N2", "G5 대수", "pushpull", 2.0, 15.0, 3, True, ALL_ON, ABOVE_BED, None, (4.0, 2.0),
     "한쪽에 3대씩 총 12대. 합계 풍량은 F3 과 같다 — 덕트에 가까운 분산 급기"),
    # ── G6 팬 높이 ──────────────────────────────────────────────
    ("H1", "G6 높이", "pushpull", 6.0, 15.0, 1, True, ALL_ON, 0.10, None, (4.0, 2.0),
     "선반면 +0.10 m — 캐노피 속으로 더 낮게"),
    ("H2", "G6 높이", "pushpull", 6.0, 15.0, 1, True, ALL_ON, 0.30, None, (4.0, 2.0),
     "선반면 +0.30 m — 캐노피 위를 스치도록 더 높게"),
    # ── G7 에어컨 위치 (끄지 않는다, 위치만 옮긴다) ──────────────
    ("A1", "G7 에어컨", "pushpull", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (2.0, 1.5),
     "에어컨을 좌측 전방으로 — 재배단에서 멀어질 때"),
    ("A2", "G7 에어컨", "pushpull", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (6.0, 3.5),
     "에어컨을 우측 후방으로 — 반원 안쪽에 가깝게"),
    ("A3", "G7 에어컨", "pushpull", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 3.5),
     "재배단 바로 뒤 — 급기가 재배단을 정면으로 치는 배치"),
    ("A4", "G7 에어컨", "pushpull", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (2.5, 2.0),
     "재배단과 같은 y, 좌측 — 길이 방향으로 밀어 주는 배치"),
    ("A5", "G7 에어컨", "pushpull", 6.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (6.0, 1.2),
     "평벽 쪽 우측 — 재배단 대각선"),
    ("A6", "G7 에어컨", "pushpull", 0.0, 15.0, 1, True, ALL_ON, ABOVE_BED, None, (4.0, 3.5),
     "A3 과 같은 에어컨 위치에 팬만 끔 — 에어컨 위치 효과만 떼어 보기"),
]


def main():
    lay = json.load(open(os.path.join(REPO, "data", "fan_layout.json"), encoding="utf-8"))
    acp = json.load(open(os.path.join(REPO, "data", "ac_params.json"), encoding="utf-8"))
    spec = lay["spec"]
    dia, depth = float(spec["diam_m"]), 0.08
    rack0 = tuple(lay["rack_centre_ue_m"])
    tiers = lay["tier_bed_z_m"]
    area = math.pi * (dia / 2.0) ** 2

    planes0 = planes_for(rack0, tiers)
    blockage0 = blockage_for(rack0, tiers)

    heat = []
    if LED_ON:
        led_vol = LED_BAR[0] * LED_BAR[1] * LED_BAR[2]
        for i, lz in enumerate(LED_Z[:len(tiers)]):
            heat.append({"name": "led%d" % i,
                         "box_cfd_m": box([rack0[0] - X_SHIFT, rack0[1], lz], list(LED_BAR)),
                         "watt": LED_W_EACH,
                         "volumetric_W_m3": round(LED_W_EACH / led_vol, 0)})

    cases = []
    for idx, (name, grp, layout, cmm, tilt, n, rack_on, on, above,
              rack_alt, ac_pos, why) in enumerate(CASE_DEFS, start=1):
        rack = tuple(rack_alt) if rack_alt else rack0
        entry = {
            "no": idx, "case": name, "run_id": "%02d_%s" % (idx, name),
            "group": grp, "layout": layout, "rack": rack_on,
            "rack_centre_ue_m": list(rack) if rack_on else None,
            "ac": ac_for(ac_pos, acp),
            "per_fan_CMM": cmm, "tilt_deg": tilt, "n_per_side": n,
            "fan_height_above_bed_m": above,
            "purpose": why,
        }
        if rack_on and rack != rack0:
            entry["rack_blockage_override"] = blockage_for(rack, tiers)
            entry["judge_planes_override"] = planes_for(rack, tiers)
        if layout == "none":
            entry.update({"fans_on": 0, "fans_off": [], "fan_zones": []})
            cases.append(entry)
            continue
        zs, u, f, off = zones_for(layout, tilt, cmm, n, dia, depth, rack, tiers, on, above)
        sup = [z for z in zs if z["role"] in ("supply", "booster")]
        entry.update({
            "fans_on": len(zs) if cmm else 0, "fans_off": off,
            "outlet_m_s": u, "thrust_N": f,
            "momentum_source_N_m3": zs[0]["momentum_source_N_m3"] if zs else 0.0,
            "stream_CMM_per_tier": round(cmm * len(sup) / max(1, len(tiers)), 2),
            "fan_zones": zs if cmm else [],
        })
        cases.append(entry)

    out = {
        "note": "언리얼 배치에서 만든 CFD 경계조건 초안과 케이스 목록. 팬은 유동 영역 안의 "
                "운동량 소스로 둔다. 이 값으로 topoSetDict·fvOptions 를 만들고 OpenFOAM 을 "
                "다시 풀어야 캐노피 풍속이 나온다.",
        "coord_note": "CFD x = UE x - 4.0, y·z 동일",
        "ac_note": "에어컨은 어느 케이스에서도 끄지 않는다. 위치만 옮기며, 취출·리턴 상자는 "
                   "기록된 형상을 그대로 평행이동한다.",
        "rack_note": "재배단 위치는 전 케이스 고정이다. 막힘 상자와 판정면도 하나로 쓴다.",
        "numbering": "cases[].no 가 1~%d 통번호, cases[].run_id 가 실행 폴더 이름이다 "
                     "(예: 01_R0). 결과 파일도 같은 이름으로 모으면 대조가 쉽다." % len(CASE_DEFS),
        "lighting": {"included": LED_ON,
                     "note": "이번 계산은 조명 발열을 뺀다. 풍속 기준을 먼저 잡고 "
                             "조명은 스펙시트가 오면 넣는다."},
        "fan_spec": {"diam_m": dia, "depth_m": depth, "area_m2": round(area, 5),
                     "rho_kg_m3": RHO, "watt_each": spec["watt_each"],
                     "above_bed_m_default": ABOVE_BED},
        "rack_default": {"centre_ue_m": list(rack0), "bed_size_m": [BED_W, BED_D],
                         "tier_bed_z_m": tiers},
        "rack_blockage": blockage0,
        "heat_sources": heat,
        "judge_planes": planes0,
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
            "1_screening": "R0·R1·F1~F6 을 정상상태로 돌려 풍량 곡선을 잡는다",
            "2_onoff": "정해진 풍량으로 S1~S6 을 돌려 켤 팬을 고른다",
            "3_layout": "L1~L3, T1~T3, N1·N2, H1·H2 로 배치·각도·대수·높이를 정한다",
            "4_ac": "A1~A6 으로 에어컨 위치를 비교한다. 에어컨은 끄지 않는다",
            "5_transient": "최종 조합만 900초 과도해석으로 돌려 기존 규격대로 반출한다",
        },
        "openfoam_hint": {
            "topoSetDict": "각 fan_zones[].cellZone_box_cfd_m 을 boxToCell 로 잡아 cellZone 생성",
            "fvOptions": "vectorSemiImplicitSource 로 zone 마다 dir_unit × thrust_N 적용 "
                         "(또는 meanVelocityForce 로 Ubar = dir_unit × outlet_m_s)",
            "ac": "cases[].ac.topoSet_boxes_cfd_m 으로 취출 4개와 리턴을 다시 잡는다. "
                  "풍량·급기온도는 supply 항목 그대로 쓴다",
            "blockage": "rack_blockage 는 snappyHexMesh 의 searchableBox 로 넣는다. "
                        "R0 만 빼고 모든 케이스에 같은 좌표로 들어간다",
            "heat": "heat_sources 는 이번에 비어 있다. 조명을 넣을 때 cellZone + "
                    "scalarSemiImplicitSource(에너지)로 준다.",
            "sampling": "judge_planes 를 sample(surfaces, plane)로 뽑아 magU 를 저장하면 "
                        "적정구간 비율·정체 비율·상대표준편차를 그대로 계산할 수 있다",
            "unchanged": "시각표와 반출 규격은 그대로 둔다",
        },
    }
    p = os.path.join(REPO, "data", "fan_params.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    print("FAN_BC: 케이스 %d개 · 판정면 %d장(면당 %d점) · 재배단 막힘 %d개 · 조명 %s"
          % (len(cases), len(planes0), planes0[0]["n_points"], len(blockage0),
             "포함" if LED_ON else "제외"))
    grp = None
    for c in cases:
        if c["group"] != grp:
            grp = c["group"]
            print("  [%s]" % grp)
        print("    %2d %-3s %-9s 팬 켬%2d 끔%2d  %5.1f CMM  기울기%4.0f°  에어컨(%.1f, %.1f)  %s"
              % (c["no"], c["case"], c["layout"], c.get("fans_on", 0),
                 len(c.get("fans_off", [])), c["per_fan_CMM"], c["tilt_deg"],
                 c["ac"]["centre_ue_m"][0], c["ac"]["centre_ue_m"][1], c["purpose"][:28]))
    print("  -> data/fan_params.json")


if __name__ == "__main__":
    main()
