"""SF_Rehearsal: 스마트팜 재배단을 배치한다. (목적 O4)

실제 구성 (사용자 확인, 2026-09-03)
    **3단 수직 재배단 1대, 방 중앙**

    ← 처음엔 2단 8세트로 만들었으나 실제와 달라 교체.

⚠ 중요 — 이 오브젝트는 CFD 해석에 들어가 있지 않습니다.
   현재 CFD 는 '빈 방' 해석입니다. 화면에 재배단이 보여도 기류는
   재배단이 없는 상태로 계산된 것입니다.
   → docs/OBJECTIVES.md §3 V6 / docs/VERIFICATION.md §5-1

치수는 가정값입니다. 실측이 오면 아래 상수만 고치면 됩니다.

    py ue/ue_exec.py -f ue/sf_make_racks.py
"""
import unreal

S = 100.0                       # m -> cm
LX, LY, LZ = 8.0, 5.7, 2.7      # 방 (평벽 길이, 곡면 정점 깊이, 높이)
CX = LX / 2.0

# ── 재배단 규격 (m) — ⚠ 실측 대기, 현재는 가정값 ──────────────
RACK_X, RACK_Y = 4.0, 2.85      # 배치 위치 = 방 중앙
BED_W = 2.40                    # 선반 가로 (길이 방향)
BED_D = 0.80                    # 선반 깊이
TIER_Z = [0.55, 1.20, 1.85]     # 3단 — 바닥에서 각 단 높이
POST_W = 0.06                   # 기둥 두께
BED_T = 0.05                    # 선반 두께
TOP_MARGIN = 0.15               # 최상단 선반 위로 기둥이 더 올라가는 길이

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def in_room(x, y):
    return y >= 0.0 and ((x - CX) / CX) ** 2 + (y / LY) ** 2 <= 1.0


# 기존 재배단 전부 제거 (2단 8세트 포함)
removed = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("SF_Rack"):
        eas.destroy_actor(a)
        removed += 1

cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
if cube is None:
    raise RuntimeError("/Engine/BasicShapes/Cube 를 못 찾음")


def box(center_m, size_m, label):
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(center_m[0] * S, center_m[1] * S, center_m[2] * S))
    a.set_actor_label(label)
    smc = a.static_mesh_component
    smc.set_static_mesh(cube)
    if mat:
        smc.set_material(0, mat)
    a.set_actor_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    smc.set_mobility(unreal.ComponentMobility.STATIC)
    return a


# 방 안에 들어가는지 확인 (네 모서리)
corners = [(RACK_X + sx * BED_W / 2, RACK_Y + sy * BED_D / 2)
           for sx in (-1, 1) for sy in (-1, 1)]
outside = [c for c in corners if not in_room(*c)]
if outside:
    raise RuntimeError("재배단이 방 밖으로 나감: %s" % outside)

h = TIER_Z[-1] + TOP_MARGIN
made = 0

# 기둥 4개
for k, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
    box((RACK_X + sx * (BED_W / 2 - POST_W / 2),
         RACK_Y + sy * (BED_D / 2 - POST_W / 2),
         h / 2.0),
        (POST_W, POST_W, h), "SF_Rack_post%d" % k)
    made += 1

# 선반 3단
for t, z in enumerate(TIER_Z):
    box((RACK_X, RACK_Y, z), (BED_W, BED_D, BED_T), "SF_Rack_bed%d" % t)
    made += 1

les.save_current_level()
msg = ("SF_RACKS: 3단 재배단 1대, 중앙 (%.1f, %.1f). "
       "액터 %d개 (기둥 4 + 선반 3), 이전 %d개 제거. "
       "선반 %.2f x %.2f m, 단 높이 %s m"
       % (RACK_X, RACK_Y, made, removed, BED_W, BED_D,
          "/".join("%.2f" % z for z in TIER_Z)))
unreal.log(msg)
print(msg)
