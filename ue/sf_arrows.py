"""SF_Rehearsal: 속도장 화살표를 **직접 메시로** 만든다.

엔진 기본 Niagara `VectorFieldVisualizationSystem` 을 대체한다. 그쪽 문제:
    · 화살표 · 파티클 구 · 흰 경계상자가 한 시스템에 묶여 있어 개별로 못 끈다
      (이미터 저작이 파이썬에 미노출)
    · 파티클은 방 한가운데 고정된 구에서 제자리 요동만 쳐서 정보가 없다
    · 화살표 색이 고정 빨강이라 방향·길이 말고는 읽을 게 없다

여기서는:
    방향 = 그 지점 바람 방향
    길이 = 속도 크기 (느린 곳도 보이도록 sqrt 스케일)
    색   = 속도 크기, **회색 -> 호박색** 램프
           ★ 유선의 온도 램프(파랑-흰-빨강)와 일부러 다른 계열을 쓴다.
             한 화면에 색 척도가 둘인데 계열이 비슷하면 서로 오독한다.

입력
    data/arrows/arrow_<frame>.csv   (src/pipeline/make_arrows.py 생성)
    data/_nia.json 의 "frame" (없으면 14)

    py ue/ue_exec.py -f ue/sf_arrows.py
"""
import csv
import json
import math
import os
import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

V_REF = 0.45            # 이 속도(m/s)에서 최대 길이/색
L_MIN, L_MAX = 7.0, 34.0    # 화살표 전체 길이 (cm)
R_SHAFT = 1.1           # 자루 반지름 (cm)
HEAD_FRAC = 0.34        # 촉이 차지하는 길이 비율
HEAD_R = 3.0            # 촉 밑면 반지름 (cm)
SIDES = 3

MAT_PATH = "/Game/Materials/M_SF_VertexColor"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()


def speed_color(sp):
    """속도 -> 회색에서 호박색. 온도 램프(파랑-흰-빨강)와 안 겹치는 계열."""
    f = math.sqrt(max(0.0, min(1.0, sp / V_REF)))
    a = (0.24, 0.26, 0.30)      # 정체
    b = (1.00, 0.78, 0.20)      # 빠름
    return unreal.LinearColor(a[0] + (b[0] - a[0]) * f,
                              a[1] + (b[1] - a[1]) * f,
                              a[2] + (b[2] - a[2]) * f, 1.0)


def vertex_color_material():
    """정점색을 그대로 내보내는 Unlit 머티리얼 (sf_streamlines.py 와 공용)."""
    mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
    if mat is not None:
        return mat
    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Materials"):
        unreal.EditorAssetLibrary.make_directory("/Game/Materials")
    mat = at.create_asset("M_SF_VertexColor", "/Game/Materials",
                          unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    lib = unreal.MaterialEditingLibrary
    vc = lib.create_material_expression(
        mat, unreal.MaterialExpressionVertexColor, -350, 0)
    lib.connect_material_property(vc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT_PATH)
    return mat


def frame_axes(t):
    """t 에 수직인 정규직교 두 축."""
    u = (1.0, 0.0, 0.0) if abs(t[2]) > 0.9 else (0.0, 0.0, 1.0)
    a = (t[1] * u[2] - t[2] * u[1],
         t[2] * u[0] - t[0] * u[2],
         t[0] * u[1] - t[1] * u[0])
    L = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2) or 1.0
    a = (a[0] / L, a[1] / L, a[2] / L)
    b = (t[1] * a[2] - t[2] * a[1],
         t[2] * a[0] - t[0] * a[2],
         t[0] * a[1] - t[1] * a[0])
    return a, b


def build(rows):
    verts, tris, normals, uvs, colors = [], [], [], [], []
    ring = [(math.cos(2 * math.pi * k / SIDES), math.sin(2 * math.pi * k / SIDES))
            for k in range(SIDES)]

    for (x, y, z, ux, uy, uz, sp, _T) in rows:
        f = math.sqrt(max(0.0, min(1.0, sp / V_REF)))
        L = L_MIN + (L_MAX - L_MIN) * f
        t = (ux, uy, uz)
        a, b = frame_axes(t)
        col = speed_color(sp)

        # 글리프를 표본점 **중심**에 놓는다. 꼬리를 점에 두면 격자가 밀려 보인다.
        def at_(s):
            return (x + t[0] * (s - L / 2.0),
                    y + t[1] * (s - L / 2.0),
                    z + t[2] * (s - L / 2.0))

        s_head = L * (1.0 - HEAD_FRAC)
        base = len(verts)

        def ring_at(s, r):
            p = at_(s)
            for (cs, sn) in ring:
                nx = a[0] * cs + b[0] * sn
                ny = a[1] * cs + b[1] * sn
                nz = a[2] * cs + b[2] * sn
                verts.append(unreal.Vector(p[0] + nx * r, p[1] + ny * r,
                                           p[2] + nz * r))
                normals.append(unreal.Vector(nx, ny, nz))
                uvs.append(unreal.Vector2D(0.0, 0.0))
                colors.append(col)

        ring_at(0.0, R_SHAFT)          # 0,1,2  자루 뒤
        ring_at(s_head, R_SHAFT)       # 3,4,5  자루 앞
        ring_at(s_head, HEAD_R)        # 6,7,8  촉 밑면
        tip = at_(L)                   # 9      촉 끝
        verts.append(unreal.Vector(tip[0], tip[1], tip[2]))
        normals.append(unreal.Vector(t[0], t[1], t[2]))
        uvs.append(unreal.Vector2D(1.0, 0.0))
        colors.append(col)

        for k in range(SIDES):
            k2 = (k + 1) % SIDES
            # 자루 옆면
            tris += [base + k, base + 3 + k, base + 3 + k2,
                     base + k, base + 3 + k2, base + k2]
            # 촉 옆면
            tris += [base + 6 + k, base + 9, base + 6 + k2]
        # 단면이 삼각형이라 뒷막음은 삼각형 하나면 끝난다
        # (안 막으면 뒤에서 봤을 때 뻥 뚫려 보인다)
        tris += [base + 6, base + 8, base + 7]
        tris += [base + 0, base + 1, base + 2]
    return verts, tris, normals, uvs, colors


def main():
    frame = 14
    cfg = os.path.join(REPO, "data", "_nia.json")
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8") as f:
            frame = int(json.load(f).get("frame", 14))

    path = os.path.join(REPO, "data", "arrows", "arrow_%02d.csv" % frame)
    if not os.path.isfile(path):
        raise RuntimeError("arrow 파일 없음: %s  (py -m src.pipeline.make_arrows %d)"
                           % (path, frame))
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((float(r["x"]), float(r["y"]), float(r["z"]),
                         float(r["ux"]), float(r["uy"]), float(r["uz"]),
                         float(r["speed"]), float(r["T"])))

    verts, tris, normals, uvs, colors = build(rows)

    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == "SF_Arrows":
            eas.destroy_actor(a)

    actor = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    actor.set_actor_label("SF_Arrows")

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_instance(actor)
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", handles[0])
    params.set_editor_property("new_class", unreal.ProceduralMeshComponent)
    params.set_editor_property("blueprint_context", None)
    new_handle, fail = sds.add_new_subobject(params)
    if not fail.is_empty():
        raise RuntimeError("컴포넌트 추가 실패: %s" % fail)
    sds.rename_subobject(new_handle, unreal.Text("ArrowMesh"))
    pmc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(
        sds.k2_find_subobject_data_from_handle(new_handle))

    _t = unreal.ProcMeshTangent()
    _t.set_editor_property("tangent_x", unreal.Vector(1.0, 0.0, 0.0))
    tangents = [_t] * len(verts)
    pmc.create_mesh_section_linear_color(
        0, verts, tris, normals, uvs, [], [], [], colors, tangents, False)
    pmc.set_material(0, vertex_color_material())

    # 엔진 기본 Niagara 시각화는 끈다 — 파티클 구와 경계상자를 못 떼어내기 때문.
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SF_Niagara_Flow":
            a.set_actor_hidden_in_game(True)

    les.save_current_level()
    sp = [r[6] for r in rows]
    msg = ("SF_ARROW: frame=%d 화살표 %d개 · 정점 %d · 삼각형 %d · "
           "|V| %.3f~%.3f m/s (색: 회색 0 -> 호박 %.2f)"
           % (frame, len(rows), len(verts), len(tris) // 3,
              min(sp), max(sp), V_REF))
    unreal.log(msg)
    print(msg)


main()
