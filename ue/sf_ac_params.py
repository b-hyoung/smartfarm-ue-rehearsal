"""SF_Rehearsal: UE 에서 에어컨을 옮긴 뒤 → 새 CFD 경계조건을 뽑는다.

이게 "에어컨 위치를 바꾸면 바람이 어떻게 달라지나"의 입구입니다.
UE 는 파라미터를 정하는 곳이고, 실제 예측은 CFD 가 다시 풀어야 나옵니다.

    UE 에서 SF_AC_Root 를 드래그
        ↓  (이 스크립트)
    ac_params.json  — 새 취출구/리턴 박스, 베인 각도, 풍량, 전력
        ↓
    topoSetDict / 0.orig/U 재생성 → OpenFOAM 재실행 → 새 CSV → UE

⚠ 이 스크립트는 **경계조건을 만들 뿐 기류를 예측하지 않습니다.**
   화면의 궤적은 옛 위치로 푼 결과입니다. 옮겼으면 반드시 다시 풀어야 합니다.

    py ue/ue_exec.py -f ue/sf_ac_params.py
"""
import json
import math
import os
import unreal

import sys as _sys
_sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sf_config as _CFG
OUT = os.path.join(_CFG.DATA_DIR, "ac_params.json")
S = 100.0
X_SHIFT = 4.0          # UE x  → CFD x 는 -4.0

# ── 기기 사양 (LG TUW090PA2SR 명판 + 카탈로그) ────────────────
SPEC = {
    "model_outdoor": "TUW090PA2SR",
    "type": "4Way ceiling cassette",
    "panel_mm": [950, 35, 950],
    "cooling_W": {"rated": 9000, "mid": 7350, "min": 4450},
    "power_W":   {"rated": 2000, "mid": 1450, "min": 700},
    "airflow_CMM": {"high": 25, "mid": 23, "low": 21},
    "supply_K_assumed": 289.5,
    "slot_area_m2_assumed": 0.12,
}

# 취출 슬롯 배치 (카세트 중심 기준 상대좌표, m) — topoSetDict 와 동일 규격
SLOT_OFFSET = 0.427
SLOT_LONG, SLOT_SHORT = 0.650, 0.060
RETURN_SIZE = 0.570


def power_for(cooling_W):
    """냉방 부하 → 소비전력. 명판 3점(정격/중간/최소)을 선형보간.

    인버터라 부분부하에서 COP 가 더 좋다 (4.5 → 5.1 → 6.4).
    한 점만 쓰면 부분부하 전력을 크게 과대평가한다.
    """
    c = SPEC["cooling_W"]
    p = SPEC["power_W"]
    pts = sorted([(c["min"], p["min"]), (c["mid"], p["mid"]),
                  (c["rated"], p["rated"])])
    if cooling_W <= pts[0][0]:
        return pts[0][1] * cooling_W / pts[0][0]      # 최소 이하는 비례
    if cooling_W >= pts[-1][0]:
        return pts[-1][1]                              # 정격에서 포화
    for (c0, p0), (c1, p1) in zip(pts, pts[1:]):
        if c0 <= cooling_W <= c1:
            t = (cooling_W - c0) / (c1 - c0)
            return p0 + (p1 - p0) * t
    return p["rated"]


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    root = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SF_AC_Root":
            root = a
            break
    if root is None:
        print("SF_ACP: SF_AC_Root 없음. sf_make_ac.py 를 먼저 실행하세요.")
        return

    loc = root.get_actor_location()
    rot = root.get_actor_rotation()
    ux, uy, uz = loc.x / S, loc.y / S, loc.z / S          # UE, m
    yaw = float(rot.yaw)

    # UE → CFD 좌표
    cx, cy, cz = ux - X_SHIFT, uy, uz

    # 슬롯/리턴 박스를 카세트 회전(yaw)에 맞춰 다시 계산
    def rotate(dx, dy):
        r = math.radians(yaw)
        return (dx * math.cos(r) - dy * math.sin(r),
                dx * math.sin(r) + dy * math.cos(r))

    eps = 0.001
    boxes = {}
    for name, dx, dy, sx, sy in [
            ("inletXm", -SLOT_OFFSET, 0.0, SLOT_SHORT, SLOT_LONG),
            ("inletXp", +SLOT_OFFSET, 0.0, SLOT_SHORT, SLOT_LONG),
            ("inletYm", 0.0, -SLOT_OFFSET, SLOT_LONG, SLOT_SHORT),
            ("inletYp", 0.0, +SLOT_OFFSET, SLOT_LONG, SLOT_SHORT)]:
        ox, oy = rotate(dx, dy)
        # 회전 시 가로/세로가 바뀌므로 축정렬 박스로 감싼다 (boxToFace 는 AABB)
        hw, hh = rotate(sx / 2, sy / 2)
        hw, hh = abs(hw), abs(hh)
        boxes[name] = {
            "min": [round(cx + ox - hw, 4), round(cy + oy - hh, 4),
                    round(cz - eps, 4)],
            "max": [round(cx + ox + hw, 4), round(cy + oy + hh, 4),
                    round(cz + eps, 4)],
        }
    boxes["return"] = {
        "min": [round(cx - RETURN_SIZE / 2, 4), round(cy - RETURN_SIZE / 2, 4),
                round(cz - eps, 4)],
        "max": [round(cx + RETURN_SIZE / 2, 4), round(cy + RETURN_SIZE / 2, 4),
                round(cz + eps, 4)],
    }

    cmm = SPEC["airflow_CMM"]["high"]
    q_total = cmm / 60.0                       # m3/s
    cooling = SPEC["cooling_W"]["rated"]
    params = {
        "note": "UE 에서 읽은 에어컨 위치로 만든 CFD 경계조건 초안. "
                "이 값으로 topoSetDict/0.orig/U 를 다시 만들고 OpenFOAM 을 재실행해야 "
                "새 기류 예측이 나온다.",
        "ue_location_m": [round(ux, 4), round(uy, 4), round(uz, 4)],
        "ue_yaw_deg": round(yaw, 2),
        "cfd_centre_m": [round(cx, 4), round(cy, 4), round(cz, 4)],
        "coord_note": "UE x - %.1f = CFD x" % X_SHIFT,
        "topoSet_boxes": boxes,
        "supply": {
            "total_CMM": cmm,
            "total_m3s": round(q_total, 6),
            "per_slot_m3s": round(q_total / 4.0, 6),
            "temperature_K": SPEC["supply_K_assumed"],
            "direction": "patch normal (수직 아래) — ⚠ 실물 베인은 바깥으로 뿜음. "
                         "베인 각도 실측 후 (cos, 0, -sin) 으로 교체 필요",
        },
        "power": {
            "cooling_W": cooling,
            "consumption_W": round(power_for(cooling), 1),
            "COP": round(cooling / power_for(cooling), 2),
            "curve_W": {str(k): round(power_for(v), 1)
                        for k, v in SPEC["cooling_W"].items()},
        },
        "spec": SPEC,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    msg = ("SF_ACP: AC at UE(%.2f, %.2f, %.2f) yaw %.1f  →  CFD(%.2f, %.2f, %.2f)\n"
           "        %d CMM, 취출 %.1f K, 소비전력 %.0f W (COP %.2f)\n"
           "        -> %s"
           % (ux, uy, uz, yaw, cx, cy, cz, cmm,
              SPEC["supply_K_assumed"], params["power"]["consumption_W"],
              params["power"]["COP"], OUT))
    unreal.log(msg)
    print(msg)


main()
