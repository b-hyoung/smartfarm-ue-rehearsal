"""SF_Rehearsal: 리허설용 빈 레벨을 새로 만들고 저장한다.

CFD 방(8.0 x 5.7 x 2.7 m)을 담을 깨끗한 레벨을 준비합니다.
디버그 드로잉만 쓰므로 바닥/조명 정도만 두고 나머지는 비워둡니다.

    py ue/ue_exec.py -f ue/sf_make_level.py
"""
import unreal

LEVEL_PATH = "/Game/Maps/SF_Room"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 새 빈 레벨 (기존이 있으면 덮어쓰지 않고 열기만)
if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
    les.load_level(LEVEL_PATH)
    unreal.log(f"SF_LEVEL: opened existing {LEVEL_PATH}")
else:
    les.new_level(LEVEL_PATH)
    unreal.log(f"SF_LEVEL: created {LEVEL_PATH}")

# ── 최소 구성: 방향광 + 스카이라이트 + 바닥 격자 ──────────────
def spawn(cls, loc, rot=None, label=None):
    a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator())
    if a and label:
        a.set_actor_label(label)
    return a

existing = {a.get_actor_label() for a in eas.get_all_level_actors()}

if "SF_Sun" not in existing:
    sun = spawn(unreal.DirectionalLight,
                unreal.Vector(0, 0, 600),
                unreal.Rotator(pitch=-50, yaw=-35, roll=0), "SF_Sun")
    sun.light_component.set_intensity(3.0)

if "SF_Sky" not in existing:
    spawn(unreal.SkyLight, unreal.Vector(0, 0, 400), None, "SF_Sky")

# 방 바닥 기준면 (8.0 x 5.7 m = 800 x 570 cm), 원점이 방 모서리가 되도록 중앙 배치
if "SF_Floor" not in existing:
    floor = spawn(unreal.StaticMeshActor,
                  unreal.Vector(400.0, 285.0, 0.0), None, "SF_Floor")
    mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    if mesh:
        floor.static_mesh_component.set_static_mesh(mesh)
        # 기본 Plane 은 100x100cm → 8 x 5.7 배
        floor.set_actor_scale3d(unreal.Vector(8.0, 5.7, 1.0))

# 뷰포트 카메라를 방이 보이는 위치로
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(400.0, -700.0, 600.0),
        unreal.Rotator(pitch=-30.0, yaw=60.0, roll=0.0))
except Exception as e:
    unreal.log_warning(f"SF_LEVEL: camera set skipped ({e})")

les.save_current_level()
n = len(eas.get_all_level_actors())
unreal.log(f"SF_LEVEL: saved {LEVEL_PATH}, actors={n}")
print(f"SF_LEVEL: {LEVEL_PATH} ready, actors={n}")
