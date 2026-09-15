"""VDB 볼륨 표현 — "냉기 안개" 전이함수 머티리얼.

왜: 방 전체를 온도색 안개로 채우면 겉껍질만 보인다 (꽉 찬 볼륨의 숙명).
    과학 시각화의 표준 해법 = 전이함수: 관심 없는 값은 투명, 관심 값만 보이게.

여기서는 냉기만 보이게 한다:
    t   = SVT temperature (0~1, 18.5~29℃ 정규화)
    c   = saturate((THRESH - t) * GAIN)     # t < THRESH(≈23.2℃)부터 안개 발생
    색  = lerp(옅은 하늘색, 진파랑, c)       # 찰수록 진파랑
    발광 = 색 * c * BRIGHT
    소광 = c * DENSITY

읽는 법: 취출 냉기가 천장을 타고 흘러 방 중간에 쏟아지는 게 안개 줄기로,
시간이 가면 안개가 방을 채운다 = 냉방 완료. 더운 공기는 투명해 내부가 보인다.

    py ue/ue_exec.py -f ue/sf_volume_style.py
"""
import unreal

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
import sf_config as _CFG
MAT_PATH = _CFG.MAT["volume_fog"]
THRESH = 0.45      # 정규화 온도 문턱 (0.45 ≈ 23.2℃)
GAIN = 3.0
BRIGHT = 3.0
DENSITY = 0.7

lib = unreal.MaterialEditingLibrary
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
if mat is None:
    svt = unreal.load_asset(_CFG.SVT_PATH)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset("M_SF_VolumeFog", "/Game/Materials",
                          unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_VOLUME)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)

    def node(cls, x, y, **props):
        e = lib.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def wire(a, ao, b, bi):
        lib.connect_material_expressions(a, ao, b, bi)

    sam = node(unreal.MaterialExpressionSparseVolumeTextureSample, -1200, 0,
               sparse_volume_texture=svt)
    t = node(unreal.MaterialExpressionComponentMask, -1000, 0,
             r=True, g=False, b=False, a=False)
    wire(sam, "Attributes A", t, "")

    # c = saturate((THRESH - t) * GAIN)
    th = node(unreal.MaterialExpressionConstant, -1000, 140, r=THRESH)
    sub = node(unreal.MaterialExpressionSubtract, -850, 60)
    wire(th, "", sub, "A")
    wire(t, "", sub, "B")
    gain = node(unreal.MaterialExpressionConstant, -850, 180, r=GAIN)
    mul = node(unreal.MaterialExpressionMultiply, -700, 60)
    wire(sub, "", mul, "A")
    wire(gain, "", mul, "B")
    c = node(unreal.MaterialExpressionSaturate, -570, 60)
    wire(mul, "", c, "")

    # 색: 옅은 하늘색 -> 진파랑
    lite = node(unreal.MaterialExpressionConstant3Vector, -570, -160,
                constant=unreal.LinearColor(0.45, 0.75, 1.0, 1.0))
    deep = node(unreal.MaterialExpressionConstant3Vector, -570, -20,
                constant=unreal.LinearColor(0.02, 0.12, 0.9, 1.0))
    col = node(unreal.MaterialExpressionLinearInterpolate, -400, -80)
    wire(lite, "", col, "A")
    wire(deep, "", col, "B")
    wire(c, "", col, "Alpha")

    bright = node(unreal.MaterialExpressionConstant, -400, 100, r=BRIGHT)
    cb = node(unreal.MaterialExpressionMultiply, -260, 40)
    wire(c, "", cb, "A")
    wire(bright, "", cb, "B")
    emis = node(unreal.MaterialExpressionMultiply, -130, -40)
    wire(col, "", emis, "A")
    wire(cb, "", emis, "B")
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    dens = node(unreal.MaterialExpressionConstant, -260, 220, r=DENSITY)
    ext = node(unreal.MaterialExpressionMultiply, -130, 160)
    wire(c, "", ext, "A")
    wire(dens, "", ext, "B")
    lib.connect_material_property(ext, "", unreal.MaterialProperty.MP_OPACITY)

    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT_PATH)
    print("SF_STYLE: %s 생성" % MAT_PATH)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SF_Volume":
        comp = a.get_components_by_class(unreal.HeterogeneousVolumeComponent)[0]
        comp.set_material(0, mat)
        print("SF_STYLE: SF_Volume 에 적용")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
