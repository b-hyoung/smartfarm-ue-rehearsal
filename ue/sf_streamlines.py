"""SF_Rehearsal: CFD 유선을 **진짜 메시**로 만든다 — 온도색 튜브

왜 이걸 만드나
    · `sf_flow.py` 의 궤적은 `draw_debug_line` 이라 에디터에서만 보인다.
      PIE/빌드/시퀀서/SceneCapture 에 안 나오므로 산출물이 못 된다.
    · 엔진 기본 Niagara `VectorFieldVisualizationSystem` 의 파티클은 방 한가운데
      고정된 구에서 태어나 제자리 요동만 친다. 기류를 읽을 수 없다.
      (이미터 저작이 파이썬에 미노출이라 발생 위치·형상을 못 바꾼다 — 확인함)

    그래서 유선을 ProceduralMesh 튜브로 직접 굽는다. 실제 지오메트리라 어디서든 보이고,
    각 점의 색이 **그 자리의 온도**다. "바람이 어디로 가서 온도가 어떻게 되는지"가
    한 화면에 들어온다.

    굵기 = 그 지점의 속도. 얇으면 정체, 굵으면 빠른 흐름.

입력
    data/ribbons/ribbon_<frame>.csv   (src/pipeline/make_ribbons.py 가 생성, 좌표 cm / T 섭씨)
    data/_nia.json 의 "frame" 을 읽는다 (없으면 14)

    py ue/ue_exec.py -f ue/sf_streamlines.py
"""
import csv
import json
import math
import os
import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TMIN, TMAX = 19.0, 27.0     # ★ sf_viz / sf_animate 와 같은 고정 범위.
                            #   프레임마다 바꾸면 프레임 간 비교가 거짓말이 된다.
STEP_SKIP = 2               # 궤적 점 솎기 (원본 160스텝 x 0.08s)
R_MIN, R_MAX = 1.2, 3.8     # 튜브 반지름 (cm) — 속도에 비례
V_REF = 1.5                 # 이 속도(m/s)에서 R_MAX
SIDES = 3                   # 튜브 단면 각수. 3이면 정점이 1/2 로 준다.

MAT_PATH = "/Game/Materials/M_SF_VertexColor"

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()


def temp_color(tc):
    """섭씨 -> LinearColor. 파랑 -> 밝은 회색 -> 빨강 (발산형).

    단순 (fr, 0.15, 1-fr) 보간은 중간값이 탁한 자주색이 되어
    온도차가 좁은 실내에서 구조가 안 보인다. sf_viz.py 와 같은 램프.
    """
    fr = (tc - TMIN) / (TMAX - TMIN)
    fr = 0.0 if fr < 0.0 else (1.0 if fr > 1.0 else fr)
    c0 = (0.23, 0.30, 0.75)
    c1 = (0.87, 0.87, 0.87)
    c2 = (0.71, 0.02, 0.15)
    if fr < 0.5:
        t, a, b = fr * 2.0, c0, c1
    else:
        t, a, b = (fr - 0.5) * 2.0, c1, c2
    return unreal.LinearColor(a[0] + (b[0] - a[0]) * t,
                              a[1] + (b[1] - a[1]) * t,
                              a[2] + (b[2] - a[2]) * t, 1.0)


def vertex_color_material():
    """정점색을 그대로 발광으로 내보내는 Unlit 머티리얼.

    ProceduralMesh 의 정점색은 **그걸 읽는 머티리얼**이 있어야 화면에 나온다.
    엔진 기본 BasicShapeMaterial 은 정점색을 안 읽어서 전부 회색이 된다.
    Unlit 으로 두는 이유: 조명이 어두워도 온도색이 그대로 보여야 한다.
    """
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


def load_lines(frame):
    path = os.path.join(REPO, "data", "ribbons", "ribbon_%02d.csv" % frame)
    if not os.path.isfile(path):
        raise RuntimeError("ribbon 파일 없음: %s  (py -m src.pipeline.make_ribbons %d)"
                           % (path, frame))
    lines = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lines.setdefault(int(r["pid"]), []).append(
                (float(r["x"]), float(r["y"]), float(r["z"]),
                 float(r["T"]), float(r["speed"])))
    return [v[::STEP_SKIP] for v in lines.values() if len(v) >= 4]


def frame_axes(tx, ty, tz):
    """접선에 수직인 정규직교 두 축. 접선이 z 축과 나란하면 기준축을 바꾼다."""
    ux, uy, uz = (1.0, 0.0, 0.0) if abs(tz) > 0.9 else (0.0, 0.0, 1.0)
    ax, ay, az = ty * uz - tz * uy, tz * ux - tx * uz, tx * uy - ty * ux
    L = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
    ax, ay, az = ax / L, ay / L, az / L
    bx, by, bz = ty * az - tz * ay, tz * ax - tx * az, tx * ay - ty * ax
    return (ax, ay, az), (bx, by, bz)


def build(lines):
    verts, tris, normals, uvs, colors = [], [], [], [], []
    ring = [(math.cos(2 * math.pi * k / SIDES), math.sin(2 * math.pi * k / SIDES))
            for k in range(SIDES)]

    for pts in lines:
        base = len(verts)
        n = len(pts)
        for i, (x, y, z, T, sp) in enumerate(pts):
            j0 = max(0, i - 1)
            j1 = min(n - 1, i + 1)
            tx = pts[j1][0] - pts[j0][0]
            ty = pts[j1][1] - pts[j0][1]
            tz = pts[j1][2] - pts[j0][2]
            L = math.sqrt(tx * tx + ty * ty + tz * tz)
            if L < 1e-6:
                tx, ty, tz, L = 1.0, 0.0, 0.0, 1.0
            tx, ty, tz = tx / L, ty / L, tz / L
            a, b = frame_axes(tx, ty, tz)
            f = sp / V_REF
            f = 0.0 if f < 0.0 else (1.0 if f > 1.0 else f)
            r = R_MIN + (R_MAX - R_MIN) * f
            col = temp_color(T)
            for (cs, sn) in ring:
                nx = a[0] * cs + b[0] * sn
                ny = a[1] * cs + b[1] * sn
                nz = a[2] * cs + b[2] * sn
                verts.append(unreal.Vector(x + nx * r, y + ny * r, z + nz * r))
                normals.append(unreal.Vector(nx, ny, nz))
                uvs.append(unreal.Vector2D(i / float(n - 1), 0.0))
                colors.append(col)
        for i in range(n - 1):
            p = base + i * SIDES
            q = p + SIDES
            for k in range(SIDES):
                k2 = (k + 1) % SIDES
                tris += [p + k, q + k, q + k2,
                         p + k, q + k2, p + k2]
    return verts, tris, normals, uvs, colors


def main():
    frame = 14
    cfg_path = os.path.join(REPO, "data", "_nia.json")
    if os.path.isfile(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            frame = int(json.load(f).get("frame", 14))

    lines = load_lines(frame)
    verts, tris, normals, uvs, colors = build(lines)

    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == "SF_Streamlines":
            eas.destroy_actor(a)

    actor = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    actor.set_actor_label("SF_Streamlines")

    # Actor.add_component_by_class 는 파이썬에 미노출 → SubobjectDataSubsystem 경로
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_instance(actor)
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", handles[0])
    params.set_editor_property("new_class", unreal.ProceduralMeshComponent)
    params.set_editor_property("blueprint_context", None)
    new_handle, fail = sds.add_new_subobject(params)
    if not fail.is_empty():
        raise RuntimeError("컴포넌트 추가 실패: %s" % fail)
    sds.rename_subobject(new_handle, unreal.Text("FlowMesh"))
    pmc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(
        sds.k2_find_subobject_data_from_handle(new_handle))

    _t = unreal.ProcMeshTangent()      # 위치인자를 안 받음 → 속성으로
    _t.set_editor_property("tangent_x", unreal.Vector(1.0, 0.0, 0.0))
    tangents = [_t] * len(verts)

    # (index, verts, tris, normals, uv0, uv1, uv2, uv3, colors, tangents, collision)
    pmc.create_mesh_section_linear_color(
        0, verts, tris, normals, uvs, [], [], [], colors, tangents, False)
    pmc.set_material(0, vertex_color_material())

    les.save_current_level()
    msg = ("SF_STREAM: frame=%d 유선 %d개 · 정점 %d · 삼각형 %d · T %.0f~%.0f C"
           % (frame, len(lines), len(verts), len(tris) // 3, TMIN, TMAX))
    unreal.log(msg)
    print(msg)


main()
