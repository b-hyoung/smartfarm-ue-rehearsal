"""out/vdb 의 .vdb 시퀀스를 Sparse Volume Texture 로 임포트하고
Heterogeneous Volume 액터 + 볼륨 머티리얼을 세운다.

    py ue/ue_exec.py -f ue/sf_import_vdb.py

- 시퀀스(sf_temp.0000~0014.vdb)는 첫 파일 하나만 지정하면 임포터가
  이름 패턴(.####.)으로 애니메이션 SVT 를 만든다.
- 머티리얼 M_SF_Volume: Volume 도메인, SVT 의 temperature(0~1)를
  온도 색램프(파랑→빨강)로, 소광은 상수.
"""
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDB0 = os.path.join(REPO, "out", "vdb", "sf_temp.0000.vdb")
SVT_DIR = "/Game/Volumes"
MAT_PATH = "/Game/Materials/M_SF_Volume"

# ── 1) VDB 시퀀스 임포트 ─────────────────────────────────────
if not unreal.EditorAssetLibrary.does_directory_exist(SVT_DIR):
    unreal.EditorAssetLibrary.make_directory(SVT_DIR)

task = unreal.AssetImportTask()
task.filename = VDB0
task.destination_path = SVT_DIR
task.automated = True
task.save = True
task.replace_existing = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
paths = list(task.imported_object_paths or [])
print("SF_VDB: imported -> %s" % paths)

svt = None
if paths:
    svt = unreal.load_asset(paths[0])
if svt is None:
    # 임포터가 경로를 안 돌려주는 버전 대비: 폴더에서 찾는다
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path(SVT_DIR, recursive=True):
        if "SparseVolumeTexture" in str(a.asset_class_path.asset_name):
            svt = a.get_asset()
            break
print("SF_VDB: SVT=%s (%s)" % (svt.get_name() if svt else None,
                               svt.get_class().get_name() if svt else "-"))

# ── 2) 볼륨 머티리얼 ────────────────────────────────────────
lib = unreal.MaterialEditingLibrary
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
if mat is None and svt is not None:
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset("M_SF_Volume", "/Game/Materials",
                          unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_VOLUME)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)

    def node(cls, x, y, **props):
        e = lib.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    sam = node(unreal.MaterialExpressionSparseVolumeTextureSample, -900, 0,
               sparse_volume_texture=svt)
    # temperature(0~1) -> 색램프: lerp(파랑, 빨강, t) 2단이면 방향은 읽힌다
    cold = node(unreal.MaterialExpressionConstant3Vector, -650, -150,
                constant=unreal.LinearColor(0.05, 0.25, 1.0, 1.0))
    hot = node(unreal.MaterialExpressionConstant3Vector, -650, 30,
               constant=unreal.LinearColor(1.0, 0.15, 0.05, 1.0))
    lerp = node(unreal.MaterialExpressionLinearInterpolate, -450, -60)
    lib.connect_material_expressions(cold, "", lerp, "A")
    lib.connect_material_expressions(hot, "", lerp, "B")
    lib.connect_material_expressions(sam, "Attributes A", lerp, "Alpha")
    lib.connect_material_property(lerp, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    ext = node(unreal.MaterialExpressionConstant, -450, 140, r=0.35)
    lib.connect_material_property(ext, "", unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT_PATH)
    print("SF_VDB: 머티리얼 생성 %s" % MAT_PATH)

# ── 3) Heterogeneous Volume 액터 ────────────────────────────
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() == "SF_Volume":
        eas.destroy_actor(a)
act = eas.spawn_actor_from_class(unreal.HeterogeneousVolume,
                                 unreal.Vector(0, 0, 0))
act.set_actor_label("SF_Volume")
comp = act.get_components_by_class(unreal.HeterogeneousVolumeComponent)[0]
if mat is not None:
    comp.set_material(0, mat)
print("SF_VDB: SF_Volume 액터 배치 완료")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
