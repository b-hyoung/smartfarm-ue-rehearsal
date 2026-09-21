"""재배단 유동팬(순환팬)을 배치하고, 위치·풍량을 데이터로 내보낸다.

무엇을 하나
    2단 재배단의 긴 변 양쪽에 소형 축류 유동팬을 달아 캐노피(잎 윗면) 위로
    수평 기류를 만든다. 화면에서는 팬 몸체와 방향 화살표만 두고(바람 표현 없음),
    같은 배치를 숫자로 data/fan_layout.json 에 남긴다.

⚠ 이 스크립트는 **배치와 사양을 정하는 곳**이다. 기류를 예측하지 않는다.
   캐노피 실제 풍속 분포는 CFD 재계산으로만 나온다. 여기서 쓰는 풍량·풍속은
   카탈로그 범위를 근거로 한 가정값이며, 실물 팬이 정해지면 그 값으로 교체한다.

조정 (data/_fan.json — 없으면 아래 기본값)
    {"per_fan_CMM": 8.0, "diam_m": 0.20, "n_per_side": 1,
     "offset_y_m": 0.46, "above_bed_m": 0.18, "dir": "inward", "on": true}
    dir: "inward" 양쪽에서 캐노피 중심으로 / "cross" 양쪽 모두 +y 방향

    py ue/ue_exec.py -f ue/sf_make_fans.py
"""
import json
import math
import os

import unreal

S = 100.0                        # m -> cm
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 기본 가정값 (카탈로그 범위 — 실물 선정 시 교체) ────────────────
DEF = {
    "per_fan_CMM": 8.0,          # 대당 풍량 (480 CMH) — 8인치 축류 유동팬 급
    "diam_m": 0.20,              # 토출 직경
    "depth_m": 0.08,             # 몸체 두께
    "n_per_side": 1,             # 한 단의 한쪽 변에 다는 개수 (2단 x 양쪽 = 4대)
    "offset_y_m": 0.46,          # 재배단 중심에서 팬 면까지 (선반 반깊이 0.40 + 0.06)
    "above_bed_m": 0.18,         # 선반면에서 팬 축까지 — 캐노피 윗면을 스치게
    "watt_each": 25.0,           # 대당 소비전력 가정
    "dir": "inward",
    "on": True,
}
BED_W, BED_D = 2.40, 0.80        # 선반 가로 · 깊이 (sf_make_racks 와 동일)
TIER_Z = [0.55, 1.35]            # 각 단 선반면 높이
CANOPY_H = 0.25                  # 작물 높이 가정 — 캐노피 단면 계산용
RACK_DEFAULT = (4.0, 2.0)

cfg = dict(DEF)
p = os.path.join(REPO, "data", "_fan.json")
if os.path.isfile(p):
    cfg.update(json.load(open(p, encoding="utf-8")))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# ── 재배단 위치는 레벨에서 읽는다 (옮겨 두었으면 팬도 따라간다) ────
rack = RACK_DEFAULT
beds = {}
for a in eas.get_all_level_actors():
    lb = a.get_actor_label()
    if lb.startswith("SF_Rack_bed"):
        loc = a.get_actor_location()
        beds[lb] = (loc.x / S, loc.y / S, loc.z / S)
if "SF_Rack_bed0" in beds:
    rack = (beds["SF_Rack_bed0"][0], beds["SF_Rack_bed0"][1])
tiers = [beds[k][2] for k in sorted(beds)] if beds else list(TIER_Z)

cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
cone = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cone")
box_m = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")


def _spawn(mesh, center_m, scale, rot, label, color, folder="SF/Fans"):
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(center_m[0] * S, center_m[1] * S, center_m[2] * S), rot)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    smc = a.static_mesh_component
    smc.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(*scale))
    smc.set_material(0, mat)
    smc.set_vector_parameter_value_on_materials("Color", unreal.Vector(*color))
    return a


# 이전 배치 제거
removed = 0
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith(("SF_Fan_", "SF_FanTxt")):
        eas.destroy_actor(a)
        removed += 1

layout = {
    "note": "언리얼에서 잡은 유동팬 배치 — 풍량·풍속은 가정값(카탈로그 범위). "
            "실물 팬 확정 시 per_fan_CMM·diam_m·watt_each 교체. 캐노피 실제 분포는 CFD 필요.",
    "rack_centre_ue_m": [rack[0], rack[1]],
    "bed_size_m": [BED_W, BED_D],
    "tier_bed_z_m": tiers,
    "spec": {
        "type": "소형 축류 유동팬 (HAF)",
        "diam_m": cfg["diam_m"],
        "per_fan_CMM": cfg["per_fan_CMM"],
        "per_fan_m3s": round(cfg["per_fan_CMM"] / 60.0, 5),
        "outlet_area_m2": round(math.pi * (cfg["diam_m"] / 2) ** 2, 5),
        "watt_each": cfg["watt_each"],
        "direction": cfg["dir"],
        "on": bool(cfg["on"]),
    },
    "fans": [],
}
area = math.pi * (cfg["diam_m"] / 2) ** 2
u_out = (cfg["per_fan_CMM"] / 60.0) / area
layout["spec"]["outlet_m_s"] = round(u_out, 2)

n = int(cfg["n_per_side"])
xs = [rack[0] + BED_W * ((i + 0.5) / n - 0.5) for i in range(n)]
for ti, bz in enumerate(tiers):
    zc = bz + cfg["above_bed_m"]
    for side in (-1, 1):                       # -1: y 작은 쪽, +1: y 큰 쪽
        fy = rack[1] + side * cfg["offset_y_m"]
        # 분출 방향: inward = 캐노피 중심 쪽, cross = 둘 다 +y
        dy = -side if cfg["dir"] == "inward" else 1
        yaw = 90.0 if dy > 0 else -90.0
        for i, fx in enumerate(xs):
            tag = "t%d_%s%d" % (ti, "m" if side < 0 else "p", i)
            # 몸체 — 실린더를 눕혀 토출면이 y 를 향하게
            _spawn(cube, (fx, fy, zc),
                   (cfg["diam_m"], cfg["diam_m"], cfg["depth_m"]),
                   unreal.Rotator(90.0, 0.0, 0.0), "SF_Fan_%s" % tag,
                   (0.22, 0.24, 0.26))
            # 거치대 — 선반면에서 팬 축까지 세우는 기둥
            _spawn(box_m, (fx, fy, bz + cfg["above_bed_m"] / 2.0),
                   (0.035, 0.035, cfg["above_bed_m"]),
                   unreal.Rotator(0.0, 0.0, 0.0), "SF_Fan_%s_post" % tag,
                   (0.30, 0.32, 0.34))
            # 방향 화살표 — 토출면 앞 10 cm
            _spawn(cone, (fx, fy + dy * 0.12, zc),
                   (cfg["diam_m"] * 0.6, cfg["diam_m"] * 0.6, 0.10),
                   unreal.Rotator(90.0 * dy, 0.0, 0.0), "SF_Fan_%s_dir" % tag,
                   (0.10, 0.65, 0.90))
            layout["fans"].append({
                "id": "FAN_%s" % tag.upper(),
                "tier": ti,
                "side": "y-" if side < 0 else "y+",
                "centre_ue_m": [round(fx, 3), round(fy, 3), round(zc, 3)],
                "dir_unit": [0.0, float(dy), 0.0],
                "CMM": cfg["per_fan_CMM"],
                "outlet_m_s": round(u_out, 2),
            })

# ── 한 단이 캐노피로 밀어 넣는 총량과 평균 통과 풍속(추정) ─────────
per_side_CMM = n * cfg["per_fan_CMM"]
canopy_area = BED_W * CANOPY_H                      # 캐노피 통과 단면 (m²)
mean_ms = (per_side_CMM / 60.0) / canopy_area
layout["per_tier"] = {
    "fans_per_tier": 2 * n,
    "per_side_CMM": round(per_side_CMM, 2),
    "tier_total_CMM": round(2 * per_side_CMM, 2),
    "canopy_section_m2": round(canopy_area, 3),
    "canopy_mean_m_s_est": round(mean_ms, 2),
    "note": "평균 통과 풍속 = 한쪽 풍량 / (선반 가로 x 작물 높이 0.25 m). "
            "실제 분포는 CFD 결과로 대체할 추정치다.",
}
layout["total"] = {
    "fans": len(layout["fans"]),
    "CMM": round(len(layout["fans"]) * cfg["per_fan_CMM"], 2),
    "watt": round(len(layout["fans"]) * cfg["watt_each"], 1),
}

# 화면 라벨
txt = eas.spawn_actor_from_class(
    unreal.TextRenderActor,
    unreal.Vector(rack[0] * S, (rack[1] - 1.15) * S, (tiers[-1] + 0.62) * S),
    unreal.Rotator(0, 0, -90))
txt.set_actor_label("SF_FanTxt")
txt.set_folder_path("SF/Fans")
tc = txt.get_editor_property("text_render")
tc.set_editor_property("world_size", 13.0)
tc.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
tc.set_text("유동팬 %d대 · 대당 %.1f CMM(토출 %.1f m/s) · 합 %.0f CMM / %.0f W\n"
            "캐노피 평균 통과 %.2f m/s (추정)"
            % (layout["total"]["fans"], cfg["per_fan_CMM"], u_out,
               layout["total"]["CMM"], layout["total"]["watt"], mean_ms))

out = os.path.join(REPO, "data", "fan_layout.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(layout, fh, ensure_ascii=False, indent=2)

les.save_current_level()
msg = ("SF_FANS: %d대 배치 (단 %d x 양쪽 x %d) · 대당 %.1f CMM(%.1f m/s) · "
       "합 %.0f CMM %.0f W · 캐노피 평균 %.2f m/s(추정) · 이전 %d개 제거"
       % (layout["total"]["fans"], len(tiers), n, cfg["per_fan_CMM"], u_out,
          layout["total"]["CMM"], layout["total"]["watt"], mean_ms, removed))
unreal.log(msg)
print(msg)
