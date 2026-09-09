"""활성 레벨 뷰포트를 PNG 로 저장. 애니메이션 프레임 굽는 데도 씀."""
import unreal, os, time

OUT_DIR = r"C:\Users\hunvr\Desktop\smartfarm-cfd\out\ue_shots"
NAME    = os.environ.get("SF_SHOT_NAME", "shot")

os.makedirs(OUT_DIR, exist_ok=True)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
# 뷰포트 리얼타임 켜기 — 안 켜면 갱신이 안 돼 이전 프레임이 찍힌다
try:
    les.editor_set_game_view(False)
except Exception:
    pass
try:
    les.editor_request_end_play()
except Exception:
    pass

path = os.path.join(OUT_DIR, NAME + ".png")
if os.path.exists(path):
    os.remove(path)
ok = unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, path)
print("SHOT: requested ->", path, "ok=", ok)
