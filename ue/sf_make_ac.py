"""SF_Rehearsal: 에어컨(4Way 천장 카세트)을 오브젝트로 배치한다.

목적
    · 화면에서 에어컨이 어디 있는지 보이게
    · **옮기면 그 위치를 읽어 CFD 경계조건을 다시 만들 수 있게** (sf_ac_params.py)

⚠ 좌표는 지어낸 게 아니라 CFD 케이스의 실제 경계와 같습니다.
   system/topoSetDict 의 boxToFace 박스를 UE 좌표(x+4.0, m→cm)로 옮긴 값입니다.
   화면의 취출구와 계산의 취출구가 어긋나면 시각화가 거짓말이 됩니다.

    CFD                                   UE (x+4)
    inletXm  x -0.457..-0.397             3.543..3.603
    inletXp  x  0.397.. 0.457             4.397..4.457
    inletYm  y  1.543.. 1.603             (동일)
    inletYp  y  2.397.. 2.457             (동일)
    return      -0.285..0.285 / 1.715..2.285   3.715..4.285 / 1.715..2.285

실물 규격 (LG 카탈로그): 판넬 950 x 35 x 950 mm, 본체 840 x 288 x 840 mm

    py ue/ue_exec.py -f ue/sf_make_ac.py
"""
import unreal

S = 100.0
LZ = 2.70                      # 천장 높이 (m)

AC_CX, AC_CY = 4.0, 2.0        # 카세트 중심 (UE 좌표, m)
PANEL = 0.95                   # 판넬 한 변
PANEL_T = 0.035
BODY = 0.84                    # 천장 속 본체
BODY_H = 0.288

# 취출 슬롯 4개 — (중심x, 중심y, 가로, 세로)  ※ topoSetDict 와 동일
SLOTS = [
    ("Xm", AC_CX - 0.427, AC_CY,          0.060, 0.650),
    ("Xp", AC_CX + 0.427, AC_CY,          0.060, 0.650),
    ("Ym", AC_CX,         AC_CY - 0.427,  0.650, 0.060),
    ("Yp", AC_CX,         AC_CY + 0.427,  0.650, 0.060),
]
RETURN = (AC_CX, AC_CY, 0.570, 0.570)      # 중앙 흡입 그릴

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

removed = 0
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith("SF_AC"):
        eas.destroy_actor(a)
        removed += 1

cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")


def box(label, cx, cy, cz, sx, sy, sz, color=None):
    a = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(cx * S, cy * S, cz * S))
    a.set_actor_label(label)
    c = a.static_mesh_component
    c.set_static_mesh(cube)
    if mat:
        c.set_material(0, mat)
    a.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    c.set_mobility(unreal.ComponentMobility.MOVABLE)   # 옮길 수 있어야 함
    if color:
        c.set_vector_parameter_value_on_materials("Color", color)
    return a


# ── 루트: 이걸 옮기면 전체가 따라온다 ──────────────────────────
root = eas.spawn_actor_from_class(
    unreal.Actor, unreal.Vector(AC_CX * S, AC_CY * S, LZ * S))
root.set_actor_label("SF_AC_Root")
root.tags = [unreal.Name("SF_AC"), unreal.Name("TUW090PA2SR")]

parts = []
# 천장 속 본체
parts.append(box("SF_AC_Body", AC_CX, AC_CY, LZ + BODY_H / 2,
                 BODY, BODY, BODY_H))
# 판넬 (천장면)
parts.append(box("SF_AC_Panel", AC_CX, AC_CY, LZ - PANEL_T / 2,
                 PANEL, PANEL, PANEL_T))
# 취출 슬롯 4개
for name, cx, cy, sx, sy in SLOTS:
    parts.append(box("SF_AC_Slot_%s" % name, cx, cy, LZ - PANEL_T - 0.02,
                     sx, sy, 0.04))
# 중앙 리턴
parts.append(box("SF_AC_Return", RETURN[0], RETURN[1], LZ - PANEL_T - 0.02,
                 RETURN[2], RETURN[3], 0.04))

for p in parts:
    p.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD, False)

les.save_current_level()
msg = ("SF_AC: 4Way 카세트 배치 (%.2f, %.2f, %.2f). "
       "루트 SF_AC_Root + 부품 %d개 (본체/판넬/슬롯4/리턴). 이전 %d개 제거.\n"
       "       루트를 옮긴 뒤 sf_ac_params.py 를 돌리면 새 경계조건이 나옵니다."
       % (AC_CX, AC_CY, LZ, len(parts), removed))
unreal.log(msg)
print(msg)
