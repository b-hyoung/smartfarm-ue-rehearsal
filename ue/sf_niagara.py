"""SF_Rehearsal: CFD 속도장을 **진짜 Niagara** 로 흐르게 한다.

    data/fga/flow_NN.fga            CFD 속도장 (48x34x16, cm 단위)
        v VectorFieldStaticFactory
    /Game/VectorFields/VF_flow_NN   VectorField 에셋
        v User 파라미터
    /Niagara/VectorFields/VectorFieldVisualizationSystem
        v
    SF_Niagara_Flow (NiagaraActor)

파라미터 (data/_nia.json 으로 넘긴다 — 원격 실행이라 환경변수는 안 통한다)
    {"frame": 14, "spawn": [400, 200, 250], "intensity": 1.0}

    spawn      파티클이 태어나는 곳 = **액터 위치**. 취출구 밑에 두면 급기가 어디로
               가는지 보인다. 방 한가운데 두면 그냥 제자리에서 요동만 친다.
    intensity  User.FieldIntensity. 속도장 배율. 1.0 이면 파티클 수명 안에
               거의 못 움직여서 무리가 제자리에 뭉쳐 있다.

⚠ 이 컴포넌트는 한 번 활성화되면 파라미터를 바꿔도 다시 안 푼다
  (activate/deactivate 로도 안 됨). 그래서 매번 액터를 지우고 새로 스폰한다.

    py ue/ue_exec.py -f ue/sf_niagara.py
"""
import json
import os
import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FGA_DIR = os.path.join(REPO, "data", "fga")
VF_DIR = "/Game/VectorFields"
SYS = "/Niagara/VectorFields/VectorFieldVisualizationSystem"

S = 100.0
LX, LY, LZ = 8.0, 5.7, 2.7      # m — fga 가 덮는 박스
BOX_BASE = 563.0                # 이 시스템이 그리는 기본 박스 한 변 (cm, 실측)

cfg = {}
cfg_path = os.path.join(REPO, "data", "_nia.json")
if os.path.isfile(cfg_path):
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

FRAME = int(cfg.get("frame", 14))
SPAWN = cfg.get("spawn", [LX / 2 * S, LY / 2 * S, LZ / 2 * S])
INTENSITY = float(cfg.get("intensity", 1.0))

at = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def import_fga(idx):
    """flow_NN.fga -> VectorFieldStatic 에셋. 이미 있으면 재사용."""
    name = "VF_flow_%02d" % idx
    path = "%s/%s" % (VF_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)

    src = os.path.join(FGA_DIR, "flow_%02d.fga" % idx)
    if not os.path.isfile(src):
        raise RuntimeError("fga 없음: " + src)

    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = VF_DIR
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.factory = unreal.VectorFieldStaticFactory()
    at.import_asset_tasks([task])

    obj = unreal.EditorAssetLibrary.load_asset(path)
    if obj is None:
        raise RuntimeError("임포트 실패: " + path)
    return obj


def main():
    system = unreal.EditorAssetLibrary.load_asset(SYS)
    if system is None:
        raise RuntimeError("Niagara 시스템 없음: " + SYS)

    vf = import_fga(FRAME)

    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label().startswith("SF_Niagara"):
            eas.destroy_actor(a)

    spawn = unreal.Vector(float(SPAWN[0]), float(SPAWN[1]), float(SPAWN[2]))
    actor = eas.spawn_actor_from_class(unreal.NiagaraActor, spawn,
                                       unreal.Rotator(0, 0, 0))
    actor.set_actor_label("SF_Niagara_Flow")
    comp = actor.get_editor_property("niagara_component")
    comp.set_asset(system)

    # 이 시스템의 실제 User 파라미터 (uasset 문자열 테이블에서 확인):
    #   VectorField, FieldLocation, FieldRotation, FieldScale, FieldCoordinates,
    #   FieldIntensity, FieldApplyFalloff, FieldFalloffDistance,
    #   FieldUseExponentialFalloff
    # ⚠ set_variable_* 는 이름이 틀려도 예외를 안 낸다(오버라이드에 그냥 기록).
    #    "성공했다"의 근거로 쓰지 말 것 — 눈으로 확인해야 한다.
    comp.set_variable_object("VectorField", vf)
    # 위치 계열은 LWC 라 FNiagaraPosition. set_variable_vec3 는 조용히 무시된다.
    comp.set_variable_position("FieldLocation",
                               unreal.Vector(LX / 2 * S, LY / 2 * S, LZ / 2 * S))
    comp.set_variable_vec3("FieldScale",
                           unreal.Vector(LX * S / BOX_BASE, LY * S / BOX_BASE,
                                         LZ * S / BOX_BASE))
    comp.set_variable_float("FieldIntensity", INTENSITY)
    comp.set_variable_bool("FieldApplyFalloff", False)

    comp.set_visibility(True, True)
    comp.set_editor_property("auto_activate", True)
    comp.activate(True)

    les.save_current_level()
    msg = ("SF_NIA: frame=%d spawn=(%.0f,%.0f,%.0f) intensity=%.1f  vf=%s"
           % (FRAME, spawn.x, spawn.y, spawn.z, INTENSITY, vf.get_name()))
    unreal.log(msg)
    print(msg)


main()
