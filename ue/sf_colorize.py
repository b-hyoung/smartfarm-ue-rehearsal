"""SF_Rehearsal: 오브젝트에 색을 입힌다.

전부 기본 회색이면 무엇이 무엇인지 구분이 안 됩니다.
색은 장식이 아니라 **역할 표시**로 씁니다.

    바닥      중성 회색          — 배경
    재배단    따뜻한 목재색       — 오브젝트
    판넬/본체 밝은 회백색         — 기기 몸체
    취출 슬롯 파랑               — 여기서 찬 바람이 나온다
    리턴 그릴 주황               — 여기로 빨아들인다

    py ue/ue_exec.py -f ue/sf_colorize.py
"""
import unreal

# (라벨 접두사, 색 RGB, 러프니스, 메탈릭)
RULES = [
    ("SF_FloorD",       (0.38, 0.40, 0.43), 0.85, 0.0),
    ("SF_Rack_bed",     (0.62, 0.47, 0.31), 0.75, 0.0),   # 선반 — 목재
    ("SF_Rack_post",    (0.28, 0.29, 0.32), 0.55, 0.6),   # 기둥 — 금속
    ("SF_AC_Panel",     (0.90, 0.90, 0.88), 0.45, 0.0),
    ("SF_AC_Body",      (0.72, 0.73, 0.75), 0.55, 0.3),
    ("SF_AC_Slot",      (0.15, 0.45, 0.85), 0.35, 0.0),   # 취출 — 파랑
    ("SF_AC_Return",    (0.90, 0.45, 0.12), 0.35, 0.0),   # 리턴 — 주황
]

MAT_DIR = "/Game/Materials"
BASE = "/Engine/BasicShapes/BasicShapeMaterial"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()

base = unreal.EditorAssetLibrary.load_asset(BASE)
if base is None:
    raise RuntimeError("기본 머티리얼을 못 찾음: " + BASE)

if not unreal.EditorAssetLibrary.does_directory_exist(MAT_DIR):
    unreal.EditorAssetLibrary.make_directory(MAT_DIR)


def get_mi(name, rgb, rough, metal):
    """머티리얼 인스턴스를 만들어 색을 굽는다.

    set_vector_parameter_value_on_materials 는 파라미터 이름이 맞아야만 먹는데
    엔진 기본 머티리얼의 파라미터명이 버전마다 다릅니다. 인스턴스를 만들어
    두는 편이 확실하고, 나중에 에디터에서 손보기도 쉽습니다.
    """
    path = "%s/%s" % (MAT_DIR, name)
    mi = unreal.EditorAssetLibrary.load_asset(path)
    lib = unreal.MaterialEditingLibrary
    if mi is None:
        f = unreal.MaterialInstanceConstantFactoryNew()
        # 5.8 팩토리에는 initial_parent 가 노출돼 있지 않다.
        # 빈 인스턴스를 만든 뒤 부모를 따로 붙인다.
        mi = at.create_asset(name, MAT_DIR,
                             unreal.MaterialInstanceConstant, f)
        lib.set_material_instance_parent(mi, base)
    if mi.get_editor_property("parent") is None:
        lib.set_material_instance_parent(mi, base)
    col = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    for pname in ("Color", "BaseColor", "Base Color", "Tint"):
        try:
            lib.set_material_instance_vector_parameter_value(mi, pname, col)
        except Exception:
            pass
    for pname, val in (("Roughness", rough), ("Metallic", metal)):
        try:
            lib.set_material_instance_scalar_parameter_value(mi, pname, val)
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_asset(path)
    return mi


cache = {}
applied = {}
for a in eas.get_all_level_actors():
    label = a.get_actor_label()
    for prefix, rgb, rough, metal in RULES:
        if not label.startswith(prefix):
            continue
        key = prefix
        if key not in cache:
            cache[key] = get_mi("MI_%s" % prefix.replace("SF_", ""),
                                rgb, rough, metal)
        mi = cache[key]
        comps = a.get_components_by_class(unreal.MeshComponent)
        for c in comps:
            for i in range(max(1, c.get_num_materials())):
                c.set_material(i, mi)
        applied[prefix] = applied.get(prefix, 0) + 1
        break

les.save_current_level()
msg = "SF_COLOR: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(applied.items()))
unreal.log(msg)
print(msg)
