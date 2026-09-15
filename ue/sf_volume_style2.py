"""VDB 볼륨 머티리얼 v2 — SVT '파라미터' 노드 + 방 전체 온도색 안개.

엔진 소스(HeterogeneousVolumeComponent.cpp 653행)가 밝힌 규칙:
    컴포넌트는 머티리얼의 SVT **파라미터**에서 텍스처를 찾고, 거기로
    프레임 스트리밍·트랜스폼 동기화를 돌린다. 일반 Sample 노드(하드코딩)면
    이 경로가 끊겨 "재생 안 됨 / 1/10 크기" 가 된다.
    → MaterialExpressionSparseVolumeTextureSampleParameter("SVT") 사용.

표현 ("안에 들어가면 검정" 해결):
    presence = t > 0.02          # 방 안(데이터 있는 곳)
    cold     = saturate((0.5 - t) * 2.5)
    색       = lerp(옅은 주황(더움), 파랑(참), cold)
    발광     = 색 * (0.35 + 2.2*cold)
    소광     = presence * (0.05 + 0.5*cold)
    → 방 전체가 항상 옅은 온도색 안개로 차 있고(안이 안 검음),
      찬 공기는 진파랑으로 밀고 들어온다.

    py ue/ue_exec.py -f ue/sf_volume_style2.py
"""
import unreal

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
import sf_config as _CFG
MAT_PATH = _CFG.MAT["volume_fog2"]

lib = unreal.MaterialEditingLibrary
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
if mat is None:
    svt = unreal.load_asset(_CFG.SVT_PATH)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset("M_SF_VolumeFog2", "/Game/Materials",
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

    # ★ 파라미터 노드 — 컴포넌트가 이걸 찾아 프레임을 꽂아준다
    sam = node(unreal.MaterialExpressionSparseVolumeTextureSampleParameter,
               -1300, 0, parameter_name="SVT", sparse_volume_texture=svt)
    t = node(unreal.MaterialExpressionComponentMask, -1100, 0,
             r=True, g=False, b=False, a=False)
    wire(sam, "Attributes A", t, "")

    # presence = saturate((t - 0.02) * 50)
    c002 = node(unreal.MaterialExpressionConstant, -1100, 130, r=0.02)
    psub = node(unreal.MaterialExpressionSubtract, -960, 90)
    wire(t, "", psub, "A")
    wire(c002, "", psub, "B")
    c50 = node(unreal.MaterialExpressionConstant, -960, 200, r=50.0)
    pmul = node(unreal.MaterialExpressionMultiply, -830, 90)
    wire(psub, "", pmul, "A")
    wire(c50, "", pmul, "B")
    presence = node(unreal.MaterialExpressionSaturate, -710, 90)
    wire(pmul, "", presence, "")

    # cold = saturate((0.5 - t) * 2.5)
    ch = node(unreal.MaterialExpressionConstant, -1100, 300, r=0.5)
    csub = node(unreal.MaterialExpressionSubtract, -960, 300)
    wire(ch, "", csub, "A")
    wire(t, "", csub, "B")
    cg = node(unreal.MaterialExpressionConstant, -960, 410, r=2.5)
    cmul = node(unreal.MaterialExpressionMultiply, -830, 300)
    wire(csub, "", cmul, "A")
    wire(cg, "", cmul, "B")
    cold = node(unreal.MaterialExpressionSaturate, -710, 300)
    wire(cmul, "", cold, "")

    warm = node(unreal.MaterialExpressionConstant3Vector, -710, -170,
                constant=unreal.LinearColor(1.0, 0.45, 0.15, 1.0))
    coolc = node(unreal.MaterialExpressionConstant3Vector, -710, -30,
                 constant=unreal.LinearColor(0.08, 0.35, 1.0, 1.0))
    col = node(unreal.MaterialExpressionLinearInterpolate, -540, -90)
    wire(warm, "", col, "A")
    wire(coolc, "", col, "B")
    wire(cold, "", col, "Alpha")

    # 발광 = 색 * (0.35 + 2.2*cold)
    b0 = node(unreal.MaterialExpressionConstant, -540, 160, r=0.35)
    b1 = node(unreal.MaterialExpressionConstant, -540, 260, r=2.2)
    bm = node(unreal.MaterialExpressionMultiply, -420, 210)
    wire(cold, "", bm, "A")
    wire(b1, "", bm, "B")
    ba = node(unreal.MaterialExpressionAdd, -300, 180)
    wire(b0, "", ba, "A")
    wire(bm, "", ba, "B")
    emis = node(unreal.MaterialExpressionMultiply, -180, -30)
    wire(col, "", emis, "A")
    wire(ba, "", emis, "B")
    lib.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # 소광 = presence * (0.05 + 0.5*cold)
    d0 = node(unreal.MaterialExpressionConstant, -420, 420, r=0.05)
    d1 = node(unreal.MaterialExpressionConstant, -420, 520, r=0.5)
    dm = node(unreal.MaterialExpressionMultiply, -300, 470)
    wire(cold, "", dm, "A")
    wire(d1, "", dm, "B")
    da = node(unreal.MaterialExpressionAdd, -190, 440)
    wire(d0, "", da, "A")
    wire(dm, "", da, "B")
    ext = node(unreal.MaterialExpressionMultiply, -80, 400)
    wire(presence, "", ext, "A")
    wire(da, "", ext, "B")
    lib.connect_material_property(ext, "", unreal.MaterialProperty.MP_OPACITY)

    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT_PATH)
    print("SF_V2: %s 생성" % MAT_PATH)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SF_Volume":
        a.set_actor_location(unreal.Vector(0, 0, 0), False, False)
        a.set_actor_scale3d(unreal.Vector(1, 1, 1))
        comp = a.get_components_by_class(unreal.HeterogeneousVolumeComponent)[0]
        comp.set_material(0, mat)
        print("SF_V2: 적용 + 액터 identity")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
