"""SF_Rehearsal: 실제 CFD 공간 형상(D자)에 맞춘 바닥 메시를 만든다.

기존 SF_Floor 는 8.0 x 5.7 m 직사각형 Plane 이었는데,
실제 공간은 **평벽 + 반타원**(D자) 입니다.

    평벽(직선)  y = 0,  x = 0 ~ 8.0 m
    곡면       (x-4)^2/4^2 + y^2/5.7^2 = 1,  y >= 0   → 정점 (4.0, 5.7)

blockMeshDict 의 arc 3개가 만드는 형상과 같습니다.
UE 단위는 cm 이므로 전부 x100.

    py ue/ue_exec.py -f ue/sf_make_floor.py
"""
import math
import unreal

# ── 방 치수 (m) — geometry.json / blockMeshDict 와 동일 ─────────
LX, LY = 8.0, 5.7          # 평벽 길이(현), 곡면 정점까지 깊이
CX = LX / 2.0              # 반타원 중심 x
SEG = 96                   # 호 분할 수
S = 100.0                  # m -> cm

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 기존 사각 바닥 제거
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ("SF_Floor", "SF_FloorD"):
        eas.destroy_actor(a)

# ── D자 폴리곤: 중심 + 경계점(호 → 현) ──────────────────────────
verts = [unreal.Vector(CX * S, (LY / 2.0) * S, 0.0)]     # 0번 = 중심
ring = []
for i in range(SEG + 1):
    t = math.pi * (1.0 - i / float(SEG))     # pi -> 0  (x: 0 -> LX)
    x = CX + CX * math.cos(t)
    y = LY * math.sin(t)
    ring.append((x, y))
for (x, y) in ring:
    verts.append(unreal.Vector(x * S, y * S, 0.0))

# 삼각형 부채꼴 (중심 0번 기준). 마지막 경계점 → 첫 경계점으로 닫으면
# 그 변이 곧 평벽(y=0 현)이 된다.
tris = []
n = len(ring)
for i in range(1, n):
    tris += [0, i, i + 1]
tris += [0, n, 1]

normals = [unreal.Vector(0.0, 0.0, 1.0)] * len(verts)
uvs = [unreal.Vector2D(v.x / (LX * S), v.y / (LY * S)) for v in verts]
colors = [unreal.LinearColor(0.62, 0.65, 0.70, 1.0)] * len(verts)
# ProcMeshTangent 는 위치인자를 안 받음 → 속성으로 채운다
_t = unreal.ProcMeshTangent()
_t.set_editor_property("tangent_x", unreal.Vector(1.0, 0.0, 0.0))
_t.set_editor_property("flip_tangent_y", False)
tangents = [_t] * len(verts)

# ── 액터 + ProceduralMeshComponent ────────────────────────────
actor = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
actor.set_actor_label("SF_FloorD")

# Python 에서 Actor.add_component_by_class 는 노출돼 있지 않습니다.
# 에디터 정식 경로인 SubobjectDataSubsystem 으로 컴포넌트를 붙입니다.
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_instance(actor)
params = unreal.AddNewSubobjectParams()
params.set_editor_property("parent_handle", handles[0])
params.set_editor_property("new_class", unreal.ProceduralMeshComponent)
params.set_editor_property("blueprint_context", None)
new_handle, fail = sds.add_new_subobject(params)
if not fail.is_empty():
    raise RuntimeError("컴포넌트 추가 실패: %s" % fail)
sds.rename_subobject(new_handle, unreal.Text("FloorMesh"))
pmc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(
    sds.k2_find_subobject_data_from_handle(new_handle))
# 시그니처: (index, verts, tris, normals, uv0, uv1, uv2, uv3, colors, tangents, collision)
pmc.create_mesh_section_linear_color(
    0, verts, tris, normals, uvs, [], [], [], colors, tangents, True)

# 기본 머티리얼 (없으면 체커 대신 회색)
mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
if mat:
    pmc.set_material(0, mat)

les.save_current_level()
print("SF_FLOOR: D-shape floor built  verts=%d tris=%d" % (len(verts), len(tris) // 3))
unreal.log("SF_FLOOR: D-shape floor built verts=%d tris=%d" % (len(verts), len(tris) // 3))
