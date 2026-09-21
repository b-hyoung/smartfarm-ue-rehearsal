"""재배단 유동팬(순환팬)을 배치하고, 위치·풍량을 데이터로 내보낸다.

무엇을 하나
    2단 재배단에 소형 축류 유동팬을 달아 캐노피(잎 윗면)에 기류를 만든다.
    화면에는 팬 몸체·거치대·흐름 방향 화살표만 두고(바람 표현 없음),
    같은 배치를 숫자로 data/fan_layout.json 에 남긴다.

⚠ 이 스크립트는 **배치와 사양을 정하는 곳**이다. 기류를 예측하지 않는다.
   캐노피 실제 풍속 분포는 CFD 재계산으로만 나온다. 여기 풍량·풍속은
   카탈로그 범위를 근거로 한 가정값이며, 실물 팬이 정해지면 그 값으로 교체한다.

배치 방식 (layout) — 문헌 근거
    "ends"  베드 양 끝(짧은 변)에 팬 2대를 **같은 방향**으로 놓는다. 앞 팬이 캐노피로
            밀어 넣고, 끝의 팬이 그 공기를 받아 다시 밀어 방을 한 바퀴 돌린다(HAF 방식).
            온실 환기 지침은 모든 팬을 같은 방향으로 돌려 순환 고리를 만들고 기류를
            0.25~0.5 m/s 로 유지하라고 한다. 기본 15도 하방.
    "pushpull"  한쪽 송풍 + 반대쪽 흡입. 선반 옆이 막혀 있을 때(스커트·덕트) 유리하다.
            이정민 외(2024)는 컨테이너형 수직농장에서 베드 양 끝에 유동팬을 달았고,
            Fang 외(2020)는 층 길이 방향 급기가 평균 0.65 m/s·CV 33%로 가장 나았다.
    "top"   각 단 상부에서 캐노피로 하방 급기. 문승미 외(2015)는 재배베드 상부
            순환팬 2대를 최적으로 보고했고(0.51 m/s), Zhang & Kacira(2016)는
            캐노피 위 다공관 하방 제트로 평균 0.42 m/s·CV 44%를 얻었다.
    "side"  긴 변 양쪽에서 마주 보게. 문헌에 최적 사례가 없다(중앙 충돌·양 끝 정체).

조정 (data/_fan.json — 없으면 아래 기본값)
    {"layout": "ends", "per_fan_CMM": 5.0, "diam_m": 0.20,
     "n_per_side": 1, "above_bed_m": 0.18, "tilt_deg": 15, "on": true}

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
    "layout": "ends",            # ends | top | side
    "tilt_deg": 15.0,            # 하방 기울기 — 수평보다 베드 내부 유속이 낫다는 보고
    "per_fan_CMM": 5.0,          # 급기 1대당 풍량 (300 CMH)
    "diam_m": 0.20,              # 토출 직경
    "depth_m": 0.08,             # 몸체 두께
    "n_per_side": 1,             # 한 단의 한쪽에 다는 개수
    "above_bed_m": 0.18,         # 선반면에서 팬 축까지 — 캐노피 윗면을 스치게
    "watt_each": 25.0,           # 대당 소비전력 가정
    "on": True,
}
BED_W, BED_D = 2.40, 0.80        # 선반 가로 · 깊이 (재배단 배치와 동일)
TIER_Z = [0.55, 1.35]            # 각 단 선반면 높이
CANOPY_H = 0.25                  # 작물 높이 가정 — 통과 단면 계산용
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

cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
cone = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cone")
box_m = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")


def _spawn(mesh, centre_m, scale, rot, label, color, folder="SF/Fans"):
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(centre_m[0] * S, centre_m[1] * S, centre_m[2] * S), rot)
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

LAYOUT = cfg["layout"]
tilt = float(cfg["tilt_deg"])
n = int(cfg["n_per_side"])
area = math.pi * (cfg["diam_m"] / 2) ** 2
u_out = (cfg["per_fan_CMM"] / 60.0) / area

layout = {
    "note": "언리얼에서 잡은 유동팬 배치 — 풍량·풍속은 가정값(카탈로그 범위). "
            "실물 팬 확정 시 per_fan_CMM·diam_m·watt_each 교체. 캐노피 실제 분포는 CFD 필요.",
    "rack_centre_ue_m": [rack[0], rack[1]],
    "bed_size_m": [BED_W, BED_D],
    "tier_bed_z_m": tiers,
    "spec": {
        "type": "소형 축류 유동팬 (HAF)",
        "layout": LAYOUT,
        "tilt_deg": tilt,
        "diam_m": cfg["diam_m"],
        "per_fan_CMM": cfg["per_fan_CMM"],
        "per_fan_m3s": round(cfg["per_fan_CMM"] / 60.0, 5),
        "outlet_area_m2": round(area, 5),
        "outlet_m_s": round(u_out, 2),
        "watt_each": cfg["watt_each"],
        "on": bool(cfg["on"]),
    },
    "fans": [],
}


def _slots(bz):
    """배치 방식별 (팬 중심, 흐름 방향, 역할, 태그)."""
    zc = bz + cfg["above_bed_m"]
    out = []
    if LAYOUT in ("ends", "pushpull"):
        ex = BED_W / 2.0 + 0.10
        down = -math.tan(math.radians(tilt))
        ys = [rack[1] + BED_D * ((i + 0.5) / n - 0.5) for i in range(n)]
        for i, fy in enumerate(ys):
            out.append(((rack[0] - ex, fy, zc), (1.0, 0.0, down), "supply", "s%d" % i))
            if LAYOUT == "ends":
                # 끝의 팬도 같은 방향 — 지나온 공기를 받아 다시 민다 (이어달리기)
                out.append(((rack[0] + ex, fy, zc), (1.0, 0.0, down), "booster", "b%d" % i))
            else:
                out.append(((rack[0] + ex, fy, zc), (1.0, 0.0, 0.0), "return", "r%d" % i))
    elif LAYOUT == "top":
        zt = bz + 0.55
        m = max(2, n * 2)
        for i in range(m):
            fx = rack[0] + BED_W * ((i + 0.5) / m - 0.5)
            out.append(((fx, rack[1], zt), (0.0, 0.0, -1.0), "supply", "d%d" % i))
    else:
        xs = [rack[0] + BED_W * ((i + 0.5) / n - 0.5) for i in range(n)]
        for side in (-1, 1):
            fy = rack[1] + side * 0.46
            for i, fx in enumerate(xs):
                out.append(((fx, fy, zc), (0.0, float(-side), 0.0), "supply",
                            "%s%d" % ("m" if side < 0 else "p", i)))
    return out


def _rot(d):
    """흐름 방향 -> (몸체 실린더 회전, 화살표 원뿔 회전)."""
    dx, dy, dz = d
    if abs(dz) > 0.9:
        return unreal.Rotator(0.0, 0.0, 0.0), unreal.Rotator(180.0, 0.0, 0.0)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return (unreal.Rotator(0.0, 90.0 + pitch, yaw),
            unreal.Rotator(0.0, -90.0 + pitch, yaw))


for ti, bz in enumerate(tiers):
    for (cx, cy, cz), d, role, tag0 in _slots(bz):
        nrm = math.sqrt(sum(v * v for v in d))
        d = tuple(v / nrm for v in d)
        tag = "t%d_%s" % (ti, tag0)
        rb, rc = _rot(d)
        _spawn(cyl, (cx, cy, cz), (cfg["diam_m"], cfg["diam_m"], cfg["depth_m"]),
               rb, "SF_Fan_%s" % tag,
               (0.32, 0.24, 0.20) if role == "return" else (0.22, 0.24, 0.26))
        if cz - bz > 0.03:
            _spawn(box_m, (cx, cy, (bz + cz) / 2.0), (0.035, 0.035, cz - bz),
                   unreal.Rotator(0.0, 0.0, 0.0), "SF_Fan_%s_post" % tag,
                   (0.30, 0.32, 0.34))
        _spawn(cone, (cx + d[0] * 0.13, cy + d[1] * 0.13, cz + d[2] * 0.13),
               (cfg["diam_m"] * 0.6, cfg["diam_m"] * 0.6, 0.10), rc,
               "SF_Fan_%s_dir" % tag,
               (0.90, 0.55, 0.20) if role == "return" else (0.10, 0.65, 0.90))
        layout["fans"].append({
            "id": "FAN_%s" % tag.upper(),
            "tier": ti,
            "role": role,
            "centre_ue_m": [round(cx, 3), round(cy, 3), round(cz, 3)],
            "dir_unit": [round(v, 3) for v in d],
            "CMM": 0.0 if role == "return" else cfg["per_fan_CMM"],
            "outlet_m_s": 0.0 if role == "return" else round(u_out, 2),
        })

# ── 단별 급기량과 캐노피 평균 통과 풍속(추정) ─────────────────────
stream = [f for f in layout["fans"] if f["role"] == "supply"]
per_tier_CMM = sum(f["CMM"] for f in stream) / max(1, len(tiers))
if LAYOUT in ("ends", "pushpull"):
    canopy_area = BED_D * CANOPY_H          # 길이 방향으로 지나가는 단면
elif LAYOUT == "top":
    canopy_area = BED_W * BED_D             # 위에서 내리꽂는 면적
else:
    canopy_area = BED_W * CANOPY_H
mean_ms = (per_tier_CMM / 60.0) / canopy_area
layout["per_tier"] = {
    "fans_per_tier": len(layout["fans"]) // max(1, len(tiers)),
    "stream_CMM": round(per_tier_CMM, 2),
    "canopy_section_m2": round(canopy_area, 3),
    "canopy_mean_m_s_est": round(mean_ms, 2),
    "note": "평균 통과 풍속 = 캐노피를 지나는 한 줄기 풍량 / 통과 단면. "
            "ends 의 끝 팬은 같은 공기를 이어 미는 것이라 풍량을 더하지 않는다. "
            "ends·pushpull 은 선반 깊이 x 작물 높이, "
            "top 은 선반 면적, side 는 선반 가로 x 작물 높이를 쓴다. "
            "실제 분포는 CFD 결과로 대체할 추정치다.",
}
layout["total"] = {
    "fans": len(layout["fans"]),
    "installed_CMM": round(sum(f["CMM"] for f in layout["fans"]), 2),
    "watt": round(len(layout["fans"]) * cfg["watt_each"], 1),
}
layout["reference"] = [
    "UMass Extension / Farm Energy — HAF 지침: 모든 팬을 같은 방향으로 돌려 순환 고리를 만들고 기류 0.25~0.5 m/s(50~100 fpm) 유지, 팬 간격 12~15 m",
    "이정민 외(2024) 한국콘텐츠학회논문지 24(12) — 컨테이너형 수직농장, 베드 양 끝 유동팬, 베드 내 평균 0.12 m/s, 온도편차 ±3 -> ±1.7 ℃",
    "Fang 외(2020) Biosystems Engineering 200:1-12 — 층 길이 방향 급기가 평균 0.65 m/s·CV 33%, 유공 덕트로 캐노피 위 수평 기류",
    "문승미 외(2015) 인터넷정보학회논문지 16(1):57-66 — 순환팬 배치 12개 비교, 재배베드 상부 2대가 최적(0.51 m/s), 토출 2.9 m/s에서 에너지 효율 최적",
    "Zhang & Kacira(2016) Biosystems Engineering 147:193-205 — 캐노피 위 다공관 하방 제트, 평균 0.42 m/s·CV 44%, 팁번 예방 목적",
    "Kitaya 외(2003) Adv. Space Res. 31(1):177-182 — 기류 0.01->0.3 m/s에서 증산·광합성 2배, 0.3~1.0 m/s에서 거의 일정",
]

txt = eas.spawn_actor_from_class(
    unreal.TextRenderActor,
    unreal.Vector(rack[0] * S, (rack[1] - 1.15) * S, (tiers[-1] + 0.62) * S),
    unreal.Rotator(0, 0, -90))
txt.set_actor_label("SF_FanTxt")
txt.set_folder_path("SF/Fans")
tc = txt.get_editor_property("text_render")
tc.set_editor_property("world_size", 13.0)
tc.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
tc.set_text("유동팬 %d대 [%s] · 급기 %.1f CMM/대, 토출 %.1f m/s · 합 %.0f CMM / %.0f W\n"
            "캐노피 평균 통과 %.2f m/s (추정)"
            % (layout["total"]["fans"], LAYOUT, cfg["per_fan_CMM"], u_out,
               layout["total"]["installed_CMM"], layout["total"]["watt"], mean_ms))

out = os.path.join(REPO, "data", "fan_layout.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(layout, fh, ensure_ascii=False, indent=2)

les.save_current_level()
msg = ("SF_FANS[%s]: %d대 · 급기 %.1f CMM/대(%.1f m/s) · 합 %.0f CMM %.0f W · "
       "캐노피 평균 %.2f m/s(추정) · 이전 %d개 제거"
       % (LAYOUT, layout["total"]["fans"], cfg["per_fan_CMM"], u_out,
          layout["total"]["installed_CMM"], layout["total"]["watt"], mean_ms, removed))
unreal.log(msg)
print(msg)
