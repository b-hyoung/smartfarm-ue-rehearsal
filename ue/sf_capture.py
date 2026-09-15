"""SceneCapture2D 로 화면을 굽는다. — 뷰포트에 의존하지 않는 렌더 경로

왜 이걸 쓰나
    HighResShot / take_high_res_screenshot 은 **에디터 뷰포트가 실제로 다시 그려질 때**만
    저장된다. 에디터가 백그라운드면 Slate 스로틀링 때문에 몇 분이 지나도 파일이 안 나오고,
    set_level_viewport_camera_info 는 활성 뷰포트가 없으면 조용히 무시된다(에러도 안 남).
    SceneCapture2D 는 뷰포트와 무관하게 렌더 타깃에 직접 그리므로 둘 다 피해간다.
    애니메이션 프레임을 연속으로 굽는 데도 이쪽이 맞다.

파라미터
    data/_cap.json  {"cam": [x, y, z, pitch, yaw], "out": "...png", "fov": 60}
    ⚠ 이 스크립트는 **UE 프로세스 안에서** 돈다. 호출한 쪽의 환경변수는 안 보인다.
      그래서 파일로 넘긴다.

    sh ue/cap.sh "400,285,1500,-89,0" top
"""
import json
import os
import sys

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sf_config as CFG  # noqa: E402

DEFAULT_OUT = os.path.join(CFG.SHOT_DIR, "capture.png")

cfg = {}
cfg_path = os.path.join(REPO, "data", "_cap.json")
if os.path.isfile(cfg_path):
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

cam = cfg.get("cam", [-700, -650, 700, -20, 40])
OUT = cfg.get("out", DEFAULT_OUT)
FOV = float(cfg.get("fov", 60))
W, H = int(cfg.get("w", 1600)), int(cfg.get("h", 900))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = ues.get_editor_world()

loc = unreal.Vector(float(cam[0]), float(cam[1]), float(cam[2]))
rot = unreal.Rotator(0.0, float(cam[3]), float(cam[4]))

# 렌더 타깃 — 에셋으로 만들 필요 없다. 트랜지언트면 충분하고 프로젝트를 안 더럽힌다.
rt = unreal.RenderingLibrary.create_render_target2d(
    world, W, H, unreal.TextureRenderTargetFormat.RTF_RGBA8)

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
c.set_editor_property("texture_target", rt)
c.set_editor_property("fov_angle", FOV)
c.set_editor_property("capture_source",
                      unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
c.set_editor_property("capture_every_frame", False)
c.set_editor_property("capture_on_movement", False)
c.capture_scene()

out_dir = os.path.dirname(OUT)
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
unreal.RenderingLibrary.export_render_target(world, rt, out_dir,
                                             os.path.basename(OUT))
print("SF_CAP: %s  cam=(%.0f,%.0f,%.0f) pitch=%.0f yaw=%.0f fov=%.0f"
      % (OUT, loc.x, loc.y, loc.z, rot.pitch, rot.yaw, FOV))
