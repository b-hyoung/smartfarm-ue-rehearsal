"""SF_Rehearsal: CFD 리허설 프레임 하나를 에디터 뷰포트에 온도색 점 + 기류선으로 그린다.
언리얼 에디터 Python으로 실행:  py "C:/Users/ACE/Desktop/SF_Rehearsal/sf_viz.py"
지우기:  아래 CLEAR=True 로 두고 다시 실행 (또는 flush 한 줄)."""
import unreal
import csv

CSV_PATH = r"C:\Users\ACE\Desktop\smartfarm-ue-rehearsal\data\frames\frame_14.csv"
TARGET_POINTS = 3000        # 다운샘플 목표 점 수
TMIN, TMAX = 20.0, 29.0     # 컬러맵 고정 범위(섭씨)
POS_SCALE = 100.0           # m -> cm (UE 단위)
DUR = 1.0e6                 # 지속 표시(초)
U_SCALE = 80.0              # 기류선 길이 = |U|(m/s) * 이 값(cm)
DRAW_FLOW = True
CLEAR = False               # True면 기존 디버그 지우고 종료


def get_world():
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return ues.get_editor_world()


def main():
    world = get_world()
    unreal.SystemLibrary.flush_persistent_debug_lines(world)
    if CLEAR:
        unreal.log("SF_VIZ: cleared.")
        print("SF_VIZ: cleared.")
        return

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    step = max(1, n // TARGET_POINTS)
    sel = rows[::step]

    drawn = 0
    for r in sel:
        x = float(r["x"]) * POS_SCALE
        y = float(r["y"]) * POS_SCALE
        z = float(r["z"]) * POS_SCALE
        tc = float(r["T"]) - 273.15
        fr = (tc - TMIN) / (TMAX - TMIN)
        fr = 0.0 if fr < 0.0 else (1.0 if fr > 1.0 else fr)
        col = unreal.LinearColor(fr, 0.15, 1.0 - fr, 1.0)   # 파랑(차가움)->빨강(더움)
        loc = unreal.Vector(x, y, z)
        unreal.SystemLibrary.draw_debug_point(world, loc, 8.0, col, DUR)
        if DRAW_FLOW:
            end = unreal.Vector(x + float(r["Ux"]) * U_SCALE,
                                y + float(r["Uy"]) * U_SCALE,
                                z + float(r["Uz"]) * U_SCALE)
            unreal.SystemLibrary.draw_debug_line(world, loc, end, col, DUR, 0.5)
        drawn += 1

    # 뷰포트 카메라를 방 쪽으로 (best-effort)
    try:
        cam_loc = unreal.Vector(400.0, -700.0, 600.0)
        cam_rot = unreal.Rotator(pitch=-30.0, yaw=60.0, roll=0.0)
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)
    except Exception as e:
        unreal.log_warning("SF_VIZ: camera set skipped (%s)" % e)

    msg = "SF_VIZ: %d/%d points (step=%d), flow=%s" % (drawn, n, step, DRAW_FLOW)
    unreal.log(msg)
    print(msg)


main()
