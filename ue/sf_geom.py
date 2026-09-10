"""시각화 지오메트리 공용 모듈 — 유선 튜브 / 속도 화살표 / 정점색 머티리얼.

`sf_streamlines.py`, `sf_arrows.py`, `sf_bake_anim.py` 가 같이 쓴다.
UE 원격 실행은 파일을 그냥 exec 하므로, 부르는 쪽에서 이 디렉터리를 sys.path 에
넣어 준 뒤 import 한다.

색 규칙 (한 가지로 통일)
    **색 = 온도**       파랑(16.35℃) → 흰 → 빨강(28.85℃)
                        = ParaView 15분 렌더의 289.5~302 K 와 같은 척도
    **길이·굵기 = 속도**

    유선도 화살표도 색은 전부 온도다. 화면에 색 척도가 하나뿐이어야
    "바람이 어디로 가는데 그 바람이 찬가 더운가"를 헷갈리지 않고 읽는다.
    속도는 색이 아니라 크기로만 말한다.
"""
import csv
import math
import os

import unreal

# ★ 전 프레임 고정. 프레임마다 바꾸면 프레임 간 비교가 거짓말이 된다.
#
#   폭을 데이터에 맞춘다. ParaView 와 맞추려고 16.35~28.85(12.5K) 로 잡았더니
#   1.1 m 단면이 실제로 도는 구간(20.5~28.9)이 램프 가운데에 몰려서
#   **전 프레임이 흰색 근처로 뭉개졌다** — "색이 안 변한다"의 진짜 원인.
#   20.4 = 전 프레임 최저(20.46) 바로 아래, 28.9 = 냉방 전 실온(28.85).
#   이러면 애니메이션이 통째로 빨강 -> 파랑으로 간다.
#   급기(18.2℃)는 파랑에 포화되는데, 제일 찬 것이니 그게 맞다.
TMIN, TMAX = 20.4, 28.9
MAT_PATH = "/Game/Materials/M_SF_VertexColor"
SLICE_MAT_PATH = "/Game/Materials/M_SF_SliceTrans"
FLOW_MAT_PATH = "/Game/Materials/M_SF_FlowAnim"

# 유선 튜브
TUBE_R_MIN, TUBE_R_MAX = 1.2, 3.8
TUBE_V_REF = 1.5
STEP_SKIP = 2

# 화살표
ARROW_V_REF = 0.45
ARROW_L_MIN, ARROW_L_MAX = 9.0, 40.0
ARROW_R_SHAFT = 1.9    # 온도 단면 위에 얹히니 가늘면 안 보인다
ARROW_HEAD_FRAC = 0.34
ARROW_HEAD_R = 4.6

SIDES = 3
_RING = [(math.cos(2 * math.pi * k / SIDES), math.sin(2 * math.pi * k / SIDES))
         for k in range(SIDES)]


# ── 색 ─────────────────────────────────────────────────────────
STOPS = [
    (0.00, (0.06, 0.09, 0.50)),   # 남색  — 제일 참 (20.4C)
    (0.28, (0.10, 0.40, 0.95)),   # 파랑
    (0.46, (0.15, 0.80, 0.85)),   # 청록
    (0.62, (0.65, 0.88, 0.22)),   # 연두
    (0.80, (0.98, 0.70, 0.10)),   # 호박
    (1.00, (0.88, 0.09, 0.06)),   # 빨강 — 제일 더움 (28.9C)
]
# ★ 파랑을 0.20 -> 0.28 로 늦추고 청록을 0.40 -> 0.46 으로 밀었다.
#   그 전에는 900초 시점(방 평균 23.5C = 램프의 36%)이 청록에 걸려서
#   "다 식었는데 왜 파랗지 않냐"가 됐다. 이제 아래쪽 1/3 이 확실히 파랑이다.


def _ramp(fr):
    """구간 선형보간. 파랑-흰-빨강 발산형은 중간이 흰색이라,
    방 평균온도 근처가 전부 흰색으로 뭉개져서 공간 차이가 안 보였다.
    가운데에도 색이 계속 바뀌는 램프로 바꾼다."""
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if fr <= b:
            t = (fr - a) / (b - a) if b > a else 0.0
            return tuple(ca[i] + (cb[i] - ca[i]) * t for i in range(3))
    return STOPS[-1][1]


def temp_color(tc, quantize=None):
    """섭씨 -> LinearColor.

    quantize: 이 간격(K)으로 온도를 끊어 **등온 띠**를 만든다.
        매끄러운 그라디언트는 경계가 없어서 "여기는 덥고 저기는 시원하다"가
        눈에 안 들어온다. 0.5K 씩 끊으면 지도의 등고선처럼 읽힌다.
    """
    if quantize:
        tc = round(tc / quantize) * quantize
    fr = (tc - TMIN) / (TMAX - TMIN)
    fr = 0.0 if fr < 0.0 else (1.0 if fr > 1.0 else fr)
    c = _ramp(fr)
    return unreal.LinearColor(c[0], c[1], c[2], 1.0)


def vertex_color_material():
    """정점색을 그대로 내보내는 Unlit 머티리얼 (정적 — 마커·기본용).

    ProceduralMesh 의 정점색은 **그걸 읽는 머티리얼**이 있어야 화면에 나온다.
    엔진 기본 BasicShapeMaterial 은 정점색을 안 읽어서 전부 회색이 된다.
    Unlit 인 이유: 조명이 어두워도 온도색이 그대로 보여야 한다.
    """
    mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
    if mat is not None:
        return mat
    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Materials"):
        unreal.EditorAssetLibrary.make_directory("/Game/Materials")
    at = unreal.AssetToolsHelpers.get_asset_tools()
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


def slice_material(opacity=0.72):
    """온도 단면용 — 정점색 Unlit **반투명**.

    완전 불투명하면 아래 유선이 통째로 가리고, 너무 투명하면 검은 배경이
    비쳐서 색이 죽는다(0.55 로 했더니 전부 흐릿한 회색이 됐다).
    수평·수직 단면이 겹치면 0.82 x2 = 0.97 로 사실상 불투명해져서 0.72 로 낮췄다.
    """
    mat = unreal.EditorAssetLibrary.load_asset(SLICE_MAT_PATH)
    if mat is not None:
        return mat
    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Materials"):
        unreal.EditorAssetLibrary.make_directory("/Game/Materials")
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset("M_SF_SliceTrans", "/Game/Materials",
                          unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    lib = unreal.MaterialEditingLibrary
    vc = lib.create_material_expression(
        mat, unreal.MaterialExpressionVertexColor, -350, 0)
    lib.connect_material_property(vc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op = lib.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -350, 180)
    op.set_editor_property("r", opacity)
    lib.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(SLICE_MAT_PATH)
    return mat


def curtain_material(opacity=0.35):
    """취출 커튼용 — 정점색 Unlit 반투명, 단면보다 훨씬 투명.

    사용자 결정(2026-09-10): 주인공은 방 공기의 온도 카펫이고, 바람(커튼)은
    공간을 가리지 않게 투명도를 높여 보조로 둔다.
    """
    path = "/Game/Materials/M_SF_CurtainTrans"
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if mat is not None:
        return mat
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset("M_SF_CurtainTrans", "/Game/Materials",
                          unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    lib = unreal.MaterialEditingLibrary
    vc = lib.create_material_expression(
        mat, unreal.MaterialExpressionVertexColor, -350, 0)
    lib.connect_material_property(vc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op = lib.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -350, 180)
    op.set_editor_property("r", opacity)
    lib.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def flow_anim_material(name="M_SF_FlowAnim", stripes=6.0, speed=1.2):
    """유선 관을 따라 **무늬가 흘러가는** Unlit 머티리얼.

    왜 필요한가
        정지 이미지인 관은 "여기로 공기가 지나간다"는 말은 하지만
        **어느 쪽으로** 흐르는지는 말하지 않는다. 화살표를 봐야 알 수 있는데
        관과 화살표를 번갈아 보는 건 읽기 비용이 크다.
        관 자체에 흐름 방향을 실으면 한눈에 읽힌다.

        build_tubes 가 UV0.u 에 관의 진행률(0~1)을 넣어 두었다. 그걸 시간으로
        밀면 무늬가 관을 따라 이동한다. 지오메트리는 그대로다 — 공짜다.

        밝기 = 0.5 + 0.9 * frac(u*stripes - Time*speed)^3
        3제곱이라 앞머리만 밝고 꼬리가 어두워서 진행 방향이 보인다.

        stripes: 관은 길어서 6줄, 화살표는 짧아서 1줄이 맞다.
                 화살표에 6줄을 주면 그냥 지저분해진다.
    """
    path = "/Game/Materials/" + name
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if mat is not None:
        return mat
    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Materials"):
        unreal.EditorAssetLibrary.make_directory("/Game/Materials")
    at = unreal.AssetToolsHelpers.get_asset_tools()
    mat = at.create_asset(name, "/Game/Materials",
                          unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    lib = unreal.MaterialEditingLibrary

    def node(cls, x, y, **props):
        e = lib.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            e.set_editor_property(k, v)
        return e

    def wire(a, ao, b, bi):
        lib.connect_material_expressions(a, ao, b, bi)

    tc = node(unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    umask = node(unreal.MaterialExpressionComponentMask, -1050, 0,
                 r=True, g=False, b=False, a=False)
    wire(tc, "", umask, "")

    n_str = node(unreal.MaterialExpressionConstant, -1050, 120, r=stripes)
    umul = node(unreal.MaterialExpressionMultiply, -900, 0)
    wire(umask, "", umul, "A")
    wire(n_str, "", umul, "B")

    tnode = node(unreal.MaterialExpressionTime, -1050, 260)
    n_spd = node(unreal.MaterialExpressionConstant, -1050, 380, r=speed)
    tmul = node(unreal.MaterialExpressionMultiply, -900, 300)
    wire(tnode, "", tmul, "A")
    wire(n_spd, "", tmul, "B")

    sub = node(unreal.MaterialExpressionSubtract, -750, 120)
    wire(umul, "", sub, "A")
    wire(tmul, "", sub, "B")

    fr = node(unreal.MaterialExpressionFrac, -620, 120)
    wire(sub, "", fr, "")

    ex = node(unreal.MaterialExpressionConstant, -620, 260, r=3.0)
    pw = node(unreal.MaterialExpressionPower, -480, 120)
    wire(fr, "", pw, "Base")
    wire(ex, "", pw, "Exp")

    amp = node(unreal.MaterialExpressionConstant, -480, 260, r=0.9)
    amul = node(unreal.MaterialExpressionMultiply, -340, 120)
    wire(pw, "", amul, "A")
    wire(amp, "", amul, "B")

    base = node(unreal.MaterialExpressionConstant, -340, 260, r=0.5)
    add = node(unreal.MaterialExpressionAdd, -220, 120)
    wire(amul, "", add, "A")
    wire(base, "", add, "B")

    vc = node(unreal.MaterialExpressionVertexColor, -220, -80)
    fin = node(unreal.MaterialExpressionMultiply, -80, 0)
    wire(vc, "", fin, "A")
    wire(add, "", fin, "B")

    lib.connect_material_property(fin, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


# ── 기하 도우미 ────────────────────────────────────────────────
def arrow_anim_material():
    """화살표용 — 꼬리에서 촉으로 밝은 마루가 한 번 지나간다.

    화살표는 방향만 말하고 정지해 있으면 "지금 흐르는 중"이라는 느낌이 없다.
    줄무늬 1개를 빠르게 흘려서 각 화살표가 스스로 진행 방향을 가리키게 한다.
    """
    return flow_anim_material("M_SF_ArrowAnim", stripes=1.0, speed=0.9)


def frame_axes(t):
    """t 에 수직인 정규직교 두 축. t 가 z 축과 나란하면 기준축을 바꾼다."""
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


# ── 데이터 읽기 ────────────────────────────────────────────────
def load_ribbon(repo, frame):
    path = os.path.join(repo, "data", "ribbons", "ribbon_%02d.csv" % frame)
    if not os.path.isfile(path):
        return []
    lines = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lines.setdefault(int(r["pid"]), []).append(
                (float(r["x"]), float(r["y"]), float(r["z"]),
                 float(r["T"]), float(r["speed"])))
    return [v[::STEP_SKIP] for v in lines.values() if len(v) >= 4]


def load_probe_series(repo):
    """probes.csv -> {지점: {"xy": (x,y), "z": {높이: [(t, T), ...]}}}"""
    out = {}
    path = os.path.join(repo, "data", "probes.csv")
    if not os.path.isfile(path):
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = out.setdefault(r["point"], {"xy": (float(r["ue_x"]),
                                                   float(r["ue_y"])), "z": {}})
            p["z"].setdefault(round(float(r["z"]), 2), []).append(
                (float(r["t_s"]), float(r["T_C"])))
    return out


def probe_points_at(series, t_s, heights=(0.1, 1.1, 1.7)):
    """build_markers 에 넣을 [(x_cm, y_cm, [(z_cm, T), ...])].

    probes 는 1.15초 간격이라 가장 가까운 시각을 그대로 쓴다 (보간 불필요).
    """
    pts = []
    for name in ("A", "B", "C", "D"):
        p = series.get(name)
        if p is None:
            continue
        stack = []
        for z in heights:
            ser = p["z"].get(round(z, 2))
            if not ser:
                continue
            stack.append((z * 100.0, min(ser, key=lambda kv: abs(kv[0] - t_s))[1]))
        if stack:
            pts.append((p["xy"][0] * 100.0, p["xy"][1] * 100.0, stack))
    return pts


def load_slice(repo, frame):
    """slice_NN.csv -> {(ix, iy): (x, y, T)}"""
    path = os.path.join(repo, "data", "slices", "slice_%02d.csv" % frame)
    if not os.path.isfile(path):
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(int(r["ix"]), int(r["iy"]))] = (float(r["x"]), float(r["y"]),
                                                 float(r["T"]))
    return out


def build_slice(grid, z=110.0, quantize=0.5):
    """격자 -> 사각형 메시. 네 꼭지점이 다 있는 칸만 만든다(방 밖은 자연히 빠진다).

    quantize: 등온 띠 간격(K). 0.5 면 20.5 / 21.0 / 21.5 ... 로 색이 계단처럼 끊긴다.
    """
    verts, tris, normals, uvs, colors = [], [], [], [], []
    index = {}
    for key, (x, y, T) in grid.items():
        index[key] = len(verts)
        verts.append(unreal.Vector(x, y, z))
        normals.append(unreal.Vector(0.0, 0.0, 1.0))
        uvs.append(unreal.Vector2D(0.0, 0.0))
        colors.append(temp_color(T, quantize))
    for (ix, iy) in grid:
        a = index.get((ix, iy))
        b = index.get((ix + 1, iy))
        c = index.get((ix, iy + 1))
        d = index.get((ix + 1, iy + 1))
        if None in (a, b, c, d):
            continue
        tris += [a, c, d, a, d, b]
    return verts, tris, normals, uvs, colors


def load_vslice(repo, frame):
    """vslice_NN.csv -> {(ix, iz): (x, z, T)}  (y = Y_VSLICE 면)"""
    path = os.path.join(repo, "data", "slices", "vslice_%02d.csv" % frame)
    if not os.path.isfile(path):
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(int(r["ix"]), int(r["iz"]))] = (float(r["x"]), float(r["z"]),
                                                 float(r["T"]))
    return out


def build_vslice(grid, y=200.0, quantize=0.5):
    """수직 온도 단면 (에어컨을 지나는 y=2.0m 면).

    수평 단면 하나로는 "한 높이"만 보인다. 이 면이 있어야 찬 공기가 내려오고
    더운 공기가 천장에 남는 **성층**이 보인다.
    """
    verts, tris, normals, uvs, colors = [], [], [], [], []
    index = {}
    for key, (x, z, T) in grid.items():
        index[key] = len(verts)
        verts.append(unreal.Vector(x, y, z))
        normals.append(unreal.Vector(0.0, -1.0, 0.0))
        uvs.append(unreal.Vector2D(0.0, 0.0))
        colors.append(temp_color(T, quantize))
    for (ix, iz) in grid:
        a = index.get((ix, iz))
        b = index.get((ix + 1, iz))
        c = index.get((ix, iz + 1))
        d = index.get((ix + 1, iz + 1))
        if None in (a, b, c, d):
            continue
        tris += [a, c, d, a, d, b]
    return verts, tris, normals, uvs, colors


def load_arrows(repo, frame):
    path = os.path.join(repo, "data", "arrows", "arrow_%02d.csv" % frame)
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append((float(r["x"]), float(r["y"]), float(r["z"]),
                        float(r["ux"]), float(r["uy"]), float(r["uz"]),
                        float(r["speed"]), float(r["T"])))
    return out


# ── 메시 빌드 ──────────────────────────────────────────────────
def build_tubes(lines):
    """유선 -> 3면 튜브. 색 = 온도, 굵기 = 속도."""
    verts, tris, normals, uvs, colors = [], [], [], [], []
    for pts in lines:
        base = len(verts)
        n = len(pts)
        for i, (x, y, z, T, sp) in enumerate(pts):
            j0, j1 = max(0, i - 1), min(n - 1, i + 1)
            tx = pts[j1][0] - pts[j0][0]
            ty = pts[j1][1] - pts[j0][1]
            tz = pts[j1][2] - pts[j0][2]
            L = math.sqrt(tx * tx + ty * ty + tz * tz)
            if L < 1e-6:
                tx, ty, tz, L = 1.0, 0.0, 0.0, 1.0
            t = (tx / L, ty / L, tz / L)
            a, b = frame_axes(t)
            f = max(0.0, min(1.0, sp / TUBE_V_REF))
            r = TUBE_R_MIN + (TUBE_R_MAX - TUBE_R_MIN) * f
            col = temp_color(T)
            for (cs, sn) in _RING:
                nx = a[0] * cs + b[0] * sn
                ny = a[1] * cs + b[1] * sn
                nz = a[2] * cs + b[2] * sn
                verts.append(unreal.Vector(x + nx * r, y + ny * r, z + nz * r))
                normals.append(unreal.Vector(nx, ny, nz))
                uvs.append(unreal.Vector2D(i / float(n - 1), 0.0))
                colors.append(col)
        for i in range(n - 1):
            p, q = base + i * SIDES, base + (i + 1) * SIDES
            for k in range(SIDES):
                k2 = (k + 1) % SIDES
                tris += [p + k, q + k, q + k2, p + k, q + k2, p + k2]
    return verts, tris, normals, uvs, colors


ARROW_Z_LIFT = 13.0     # 화살표를 단면 평면보다 이만큼 위로 (cm)


def build_arrows(rows):
    """속도 글리프. **색 = 온도**, 길이 = 속도(sqrt 스케일로 느린 곳도 보이게).

    화살표와 온도 단면이 둘 다 1.1 m 라 그대로 두면 화살표가 면에 묻혀 안 보인다.
    표시만 ARROW_Z_LIFT 만큼 띄운다 (값 자체는 1.1 m 것이다).
    """
    verts, tris, normals, uvs, colors = [], [], [], [], []
    for (x, y, z, ux, uy, uz, sp, T) in rows:
        z = z + ARROW_Z_LIFT
        f = math.sqrt(max(0.0, min(1.0, sp / ARROW_V_REF)))
        L = ARROW_L_MIN + (ARROW_L_MAX - ARROW_L_MIN) * f
        t = (ux, uy, uz)
        a, b = frame_axes(t)
        col = temp_color(T)
        base = len(verts)

        def at_(s):
            return (x + t[0] * (s - L / 2.0),
                    y + t[1] * (s - L / 2.0),
                    z + t[2] * (s - L / 2.0))

        def ring_at(s, r):
            p = at_(s)
            # UV0.u = 화살표를 따라간 진행률. 흐름 무늬가 꼬리에서 촉으로 흐르게 한다.
            u = s / L
            for (cs, sn) in _RING:
                nx = a[0] * cs + b[0] * sn
                ny = a[1] * cs + b[1] * sn
                nz = a[2] * cs + b[2] * sn
                verts.append(unreal.Vector(p[0] + nx * r, p[1] + ny * r,
                                           p[2] + nz * r))
                normals.append(unreal.Vector(nx, ny, nz))
                uvs.append(unreal.Vector2D(u, 0.0))
                colors.append(col)

        s_head = L * (1.0 - ARROW_HEAD_FRAC)
        ring_at(0.0, ARROW_R_SHAFT)         # 0,1,2 자루 뒤
        ring_at(s_head, ARROW_R_SHAFT)      # 3,4,5 자루 앞
        ring_at(s_head, ARROW_HEAD_R)       # 6,7,8 촉 밑면
        tip = at_(L)
        verts.append(unreal.Vector(tip[0], tip[1], tip[2]))   # 9 촉 끝
        normals.append(unreal.Vector(t[0], t[1], t[2]))
        uvs.append(unreal.Vector2D(1.0, 0.0))
        colors.append(col)

        for k in range(SIDES):
            k2 = (k + 1) % SIDES
            tris += [base + k, base + 3 + k, base + 3 + k2,
                     base + k, base + 3 + k2, base + k2]     # 자루 옆면
            tris += [base + 6 + k, base + 9, base + 6 + k2]  # 촉 옆면
        # 단면이 삼각형이라 뒷막음은 삼각형 하나면 끝난다
        tris += [base + 6, base + 8, base + 7]
        tris += [base + 0, base + 1, base + 2]
    return verts, tris, normals, uvs, colors


def build_markers(points, r_sphere=8.0, r_bar=4.0, bar_top=180.0, nseg=24,
                  neutral=True):
    """A/B/C/D 측정점 마커.

    neutral=True: **중립 회색 위치 표시**만 한다 (기본).
        온도색으로 칠했더니 (a) 프레임마다 색이 튀어 깜빡이는 것처럼 보이고
        (b) 1.1m 반투명 단면과 정확히 교차해서 정렬 아티팩트가 났다.
        온도 숫자는 우상단 그래프가 이미 말하고 있으므로 여기서는 위치만 맡는다.
    neutral=False: 기둥을 높이별 온도색으로 (예전 동작).

    points: [(x, y, [(z, T), ...])]  좌표 cm / T 섭씨

    기둥을 높이에 따라 온도색으로 칠한다(측정 높이 사이는 선형보간).
    "여기는 위아래 다 차갑다 / 여기는 바닥만 차갑다" 가 한눈에 보인다.
    측정한 높이에는 구를 하나씩 얹어 어디를 실제로 잰 값인지 표시한다.
    """
    verts, tris, normals, uvs, colors = [], [], [], [], []

    def T_at(stack, z):
        """측정 높이 사이는 선형보간, 바깥은 가장 가까운 값으로."""
        zs = [p[0] for p in stack]
        if z <= zs[0]:
            return stack[0][1]
        if z >= zs[-1]:
            return stack[-1][1]
        for (z0, t0), (z1, t1) in zip(stack, stack[1:]):
            if z0 <= z <= z1:
                f = (z - z0) / (z1 - z0) if z1 > z0 else 0.0
                return t0 + (t1 - t0) * f
        return stack[-1][1]

    def add_bar(x, y, stack):
        base = len(verts)
        for i in range(nseg + 1):
            zz = bar_top * i / nseg
            col = temp_color(T_at(stack, zz))
            for (cs, sn) in _RING:
                verts.append(unreal.Vector(x + cs * r_bar, y + sn * r_bar, zz))
                normals.append(unreal.Vector(cs, sn, 0.0))
                uvs.append(unreal.Vector2D(0.0, i / float(nseg)))
                colors.append(col)
        for i in range(nseg):
            p = base + i * SIDES
            q = p + SIDES
            for k in range(SIDES):
                k2 = (k + 1) % SIDES
                # 중첩 함수 안에서 `tris +=` 를 쓰면 tris 가 지역변수로 잡혀 터진다
                tris.extend([p + k, q + k, q + k2, p + k, q + k2, p + k2])

    def add_bar_flat(x, y, col):
        """단색 기둥."""
        base = len(verts)
        for zz in (0.0, bar_top):
            for (cs, sn) in _RING:
                verts.append(unreal.Vector(x + cs * r_bar, y + sn * r_bar, zz))
                normals.append(unreal.Vector(cs, sn, 0.0))
                uvs.append(unreal.Vector2D(0.0, 0.0))
                colors.append(col)
        for k in range(SIDES):
            k2 = (k + 1) % SIDES
            tris.extend([base + k, base + SIDES + k, base + SIDES + k2,
                         base + k, base + SIDES + k2, base + k2])

    def add_sphere(x, y, z, col):
        """저해상도 UV 구. 마커라 매끈할 필요가 없다."""
        NU, NV = 10, 6
        base = len(verts)
        for i in range(NV + 1):
            th = math.pi * i / NV
            for j in range(NU):
                ph = 2 * math.pi * j / NU
                nx = math.sin(th) * math.cos(ph)
                ny = math.sin(th) * math.sin(ph)
                nz = math.cos(th)
                verts.append(unreal.Vector(x + nx * r_sphere, y + ny * r_sphere,
                                           z + nz * r_sphere))
                normals.append(unreal.Vector(nx, ny, nz))
                uvs.append(unreal.Vector2D(j / float(NU), i / float(NV)))
                colors.append(col)
        for i in range(NV):
            for j in range(NU):
                a = base + i * NU + j
                b = base + i * NU + (j + 1) % NU
                c = a + NU
                d = b + NU
                tris.extend([a, c, d, a, d, b])

    grey = unreal.LinearColor(0.62, 0.65, 0.70, 1.0)
    for (x, y, stack) in points:
        if neutral:
            flat = [(z, None) for (z, _T) in stack]
            add_bar_flat(x, y, grey)
            for (z, _T) in stack:
                add_sphere(x, y, z, grey)
        else:
            add_bar(x, y, stack)
            for (z, T) in stack:
                add_sphere(x, y, z, temp_color(T))
    return verts, tris, normals, uvs, colors


def build_room_outline(lx=800.0, ly=570.0, lz=270.0, seg=72, r=2.6,
                       posts=0, ceiling=False):
    """방 윤곽선 — 바닥 테두리 + 천장 테두리 + 세로 기둥 몇 개.

    바닥을 어둡게 해서 온도 단면이 잘 보이게 했더니 **공간 형태가 안 읽힌다.**
    벽을 세우면 안이 안 보이니, 가는 선으로 테두리만 그린다.
    D자: 평벽 y=0 (x 0~lx), 곡면은 반타원.

    ⚠ 천장 링과 세로 기둥은 기본으로 끈다. 위에서 내려다보는 시점에서는
      천장(z=2.7m)이 카메라에 더 가까워 바닥보다 크게 잡히고, 화면을
      가로질러 오히려 방해가 된다. 바닥 테두리 하나면 형태는 충분히 읽힌다.
    """
    verts, tris, normals, uvs, colors = [], [], [], [], []
    col = unreal.LinearColor(0.55, 0.58, 0.65, 1.0)
    cx = lx / 2.0

    ring = []
    for i in range(seg + 1):
        t = math.pi * (1.0 - i / float(seg))     # pi -> 0
        ring.append((cx + cx * math.cos(t), ly * math.sin(t)))

    def tube(pts, z):
        base = len(verts)
        for (x, y) in pts:
            for k in range(SIDES):
                a = 2 * math.pi * k / SIDES
                verts.append(unreal.Vector(x + r * math.cos(a),
                                           y + r * math.sin(a), z))
                normals.append(unreal.Vector(math.cos(a), math.sin(a), 0.0))
                uvs.append(unreal.Vector2D(0.0, 0.0))
                colors.append(col)
        for i in range(len(pts) - 1):
            p = base + i * SIDES
            q = p + SIDES
            for k in range(SIDES):
                k2 = (k + 1) % SIDES
                tris.extend([p + k, q + k, q + k2, p + k, q + k2, p + k2])

    closed = ring + [ring[0]]
    tube(closed, 1.0)          # 바닥 테두리
    if ceiling:
        tube(closed, lz)
    for i in range(posts):     # 세로 기둥 — 필요할 때만
        (x, y) = ring[int(i * seg / posts)]
        base = len(verts)
        for z in (1.0, lz):
            for k in range(SIDES):
                a = 2 * math.pi * k / SIDES
                verts.append(unreal.Vector(x + r * math.cos(a),
                                           y + r * math.sin(a), z))
                normals.append(unreal.Vector(math.cos(a), math.sin(a), 0.0))
                uvs.append(unreal.Vector2D(0.0, 0.0))
                colors.append(col)
        for k in range(SIDES):
            k2 = (k + 1) % SIDES
            tris.extend([base + k, base + SIDES + k, base + SIDES + k2,
                         base + k, base + SIDES + k2, base + k2])
    return verts, tris, normals, uvs, colors


# ── 액터 / 컴포넌트 ────────────────────────────────────────────
def get_proc_actor(label, comp_name):
    """라벨로 ProceduralMesh 액터를 찾고, 없으면 만든다.

    애니메이션을 구울 때 매 프레임 액터를 새로 만들면 느리고 언두 스택이 터진다.
    액터는 한 번만 만들고 메시 섹션만 갈아 끼운다.
    """
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            for c in a.get_components_by_class(unreal.ProceduralMeshComponent):
                return a, c
    actor = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    actor.set_actor_label(label)
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
    sds.rename_subobject(new_handle, unreal.Text(comp_name))
    pmc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(
        sds.k2_find_subobject_data_from_handle(new_handle))
    # 시각화 글리프는 그림자를 던지면 안 된다 — 바닥이 얼룩덜룩해져서
    # 온도색을 읽는 데 방해가 된다.
    pmc.set_editor_property("cast_shadow", False)
    pmc.set_editor_property("receives_decals", False)
    return actor, pmc


def set_section(pmc, data, animated=False, translucent=False):
    """animated=흐름 무늬(유선), translucent=반투명(온도 단면), 기본=정적."""
    verts, tris, normals, uvs, colors = data
    pmc.clear_all_mesh_sections()
    if not verts:
        return
    _t = unreal.ProcMeshTangent()      # 위치인자를 안 받음 → 속성으로
    _t.set_editor_property("tangent_x", unreal.Vector(1.0, 0.0, 0.0))
    # (index, verts, tris, normals, uv0, uv1, uv2, uv3, colors, tangents, collision)
    pmc.create_mesh_section_linear_color(
        0, verts, tris, normals, uvs, [], [], [], colors, [_t] * len(verts), False)
    if translucent:
        pmc.set_material(0, slice_material())
    elif animated == "arrow":
        pmc.set_material(0, arrow_anim_material())
    elif animated:
        pmc.set_material(0, flow_anim_material())
    else:
        pmc.set_material(0, vertex_color_material())


def set_visible(labels, visible):
    """에디터 뷰포트와 렌더 양쪽에서 감춘다.

    ⚠ set_actor_hidden_in_game 만 쓰면 SceneCapture/PIE 에만 먹고
      에디터 뷰포트에는 그대로 보인다.
    """
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in eas.get_all_level_actors():
        for pre in labels:
            if a.get_actor_label().startswith(pre):
                a.set_actor_hidden_in_game(not visible)
                a.set_is_temporarily_hidden_in_editor(not visible)
                n += 1
                break
    return n
