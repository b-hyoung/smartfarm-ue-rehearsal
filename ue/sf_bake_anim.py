"""15프레임 애니메이션을 굽는다 — 유선 + 화살표, 색은 전부 온도.

    data/ribbons/ribbon_NN.csv   유선 (색=온도, 굵기=속도)
    data/arrows/arrow_NN.csv     속도 글리프 (색=온도, 길이=속도)
        v
    out/anim/f_NN.png            SceneCapture2D 로 직접 렌더 (뷰포트 무관)

한 번의 원격 연결 안에서 15프레임을 다 돈다. 프레임마다 스크립트를 새로 보내면
연결 오버헤드만 1분 넘게 붙는다.

액터는 처음 한 번만 만들고 **메시 섹션만 갈아 끼운다.** 매 프레임 액터를 새로
만들면 느리고 언두 스택이 터진다.

파라미터: data/_anim.json
    {"cam": [x, y, z, pitch, yaw], "fov": 55,
     "hide": ["SF_Rack"], "show": [], "w": 1600, "h": 900}

    py ue/ue_exec.py -f ue/sf_bake_anim.py
"""
import importlib
import json
import os
import sys

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE_DIR = os.path.join(REPO, "ue")
if UE_DIR not in sys.path:
    sys.path.append(UE_DIR)

import sf_geom as G  # noqa: E402

# ⚠ UE 파이썬 세션은 한 번 import 한 모듈을 계속 들고 있다.
#   sf_geom 을 고쳐도 reload 하지 않으면 **옛 코드가 그대로 돈다**
#   (색 범위를 바꿨는데 예전 값으로 구워지는 사고가 실제로 났다).
importlib.reload(G)

OUT_DIR = os.path.join(REPO, "out", "anim")

cfg = {}
cfg_path = os.path.join(REPO, "data", "_anim.json")
if os.path.isfile(cfg_path):
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

CAM = cfg.get("cam", [150, -520, 215, -5, 55])
FOV = float(cfg.get("fov", 55))
HIDE = cfg.get("hide", [])
# ★ 흐름 무늬(시간 기반) 애니메이션.
#   실시간 재생에서는 방향을 알려주지만, 프레임을 하나씩 구워 붙이는 영상에서는
#   캡처 시각이 제각각이라 위상이 매 프레임 랜덤 -> **순수 잡음**이 된다.
#   같은 CFD 프레임을 2초 간격으로 두 번 캡처했더니 18,115픽셀이 달랐고,
#   그건 후반부 실제 온도 변화(27,792픽셀)의 65% 에 해당한다.
FLOW_ANIM = bool(cfg.get("flow_anim", False))
SHOW = cfg.get("show", [])   # 이전 실행에서 숨긴 걸 다시 켤 때
W, H = int(cfg.get("w", 1600)), int(cfg.get("h", 900))
FRAMES = cfg.get("frames", list(range(15)))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world = ues.get_editor_world()


def get_capture():
    loc = unreal.Vector(float(CAM[0]), float(CAM[1]), float(CAM[2]))
    rot = unreal.Rotator(0.0, float(CAM[3]), float(CAM[4]))
    cap = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SF_Capture":
            cap = a
            break
    if cap is None:
        cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
        cap.set_actor_label("SF_Capture")
    cap.set_actor_location_and_rotation(loc, rot, False, True)
    c = cap.get_editor_property("capture_component2d")
    c.set_editor_property("fov_angle", FOV)
    c.set_editor_property("capture_source",
                          unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    c.set_editor_property("capture_every_frame", False)
    c.set_editor_property("capture_on_movement", False)
    return c


def main():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    if HIDE:
        print("SF_ANIM: 숨김 %s -> %d개" % (HIDE, G.set_visible(HIDE, False)))
    if SHOW:
        print("SF_ANIM: 표시 %s -> %d개" % (SHOW, G.set_visible(SHOW, True)))

    _, tube = G.get_proc_actor("SF_Streamlines", "FlowMesh")
    _, arrow = G.get_proc_actor("SF_Arrows", "ArrowMesh")
    _, mark = G.get_proc_actor("SF_Probes", "ProbeMesh")
    _, sl = G.get_proc_actor("SF_Slice", "SliceMesh")
    _, vs = G.get_proc_actor("SF_VSlice", "VSliceMesh")
    _, ol = G.get_proc_actor("SF_Outline", "OutlineMesh")
    G.set_section(ol, G.build_room_outline())   # 방 윤곽은 시간에 안 변한다
    series = G.load_probe_series(REPO)
    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    times = {m["frame"]: float(m["time_s"]) for m in man["frames"]}
    c = get_capture()
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, W, H, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    c.set_editor_property("texture_target", rt)

    for f in FRAMES:
        lines = G.load_ribbon(REPO, f)
        rows = G.load_arrows(REPO, f)
        G.set_section(tube, G.build_tubes(lines), animated=FLOW_ANIM)
        G.set_section(arrow, G.build_arrows(rows),
                      animated=("arrow" if FLOW_ANIM else False))
        G.set_section(sl, G.build_slice(G.load_slice(REPO, f)), translucent=True)
        G.set_section(vs, G.build_vslice(G.load_vslice(REPO, f)), translucent=True)
        G.set_section(mark, G.build_markers(
            G.probe_points_at(series, times[f]), r_sphere=11.0, r_bar=6.5))
        c.capture_scene()
        name = "f_%02d.png" % f
        unreal.RenderingLibrary.export_render_target(world, rt, OUT_DIR, name)
        print("SF_ANIM: %s  유선 %d · 화살표 %d" % (name, len(lines), len(rows)))

    les.save_current_level()
    print("SF_ANIM: done -> %s" % OUT_DIR)


main()
