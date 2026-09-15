"""SF_Rehearsal: CFD 리허설 프레임 하나를 에디터 뷰포트에 온도색 점 + 기류선으로 그린다.
언리얼 에디터 Python으로 실행:  py "C:/Users/hunvr/Desktop/bobs_projects/smartfarm-ue-rehearsal/ue/sf_viz.py"
지우기:  아래 CLEAR=True 로 두고 다시 실행 (또는 flush 한 줄)."""
import unreal
import csv

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
import sf_config as _CFG
CSV_PATH = _os.path.join(_CFG.DATA_DIR, "frames", "frame_14.csv")
TARGET_POINTS = 3000        # 다운샘플 목표 점 수
TMIN, TMAX = 16.35, 28.85     # 컬러맵 고정 범위(섭씨)
                            #  mock 계약은 20~29 였으나 실제 CFD 는 17.8~28.9.
                            #  19~27 로 좁혀야 후반 프레임(17.8~25.1)의 구조가 보인다.
                            #  frame_00(28.85 균일)은 전부 빨강으로 포화 — 의도된 것.
                            #  ★ 전 프레임 공통 고정. 프레임마다 바꾸면 비교 불가.
POS_SCALE = 100.0           # m -> cm (UE 단위)
DUR = 1.0e6                 # 지속 표시(초)
U_SCALE = 80.0              # 기류선 길이 = |U|(m/s) * 이 값(cm)
DRAW_FLOW = True
CLEAR = False               # True면 기존 디버그 지우고 종료


def temp_color(tc):
    """섭씨 -> LinearColor. ParaView 'Cool to Warm' 과 같은 발산형.

    단순 (fr, 0.15, 1-fr) 보간은 중간값이 전부 탁한 자주색이 되어
    실내처럼 온도차가 좁은 장면에서 구조가 안 보입니다.
    파랑 -> 밝은 회색 -> 빨강 으로 가면 중간 대비가 살아납니다.
    """
    fr = (tc - TMIN) / (TMAX - TMIN)
    fr = 0.0 if fr < 0.0 else (1.0 if fr > 1.0 else fr)
    c0 = (0.23, 0.30, 0.75)     # 차가움
    c1 = (0.87, 0.87, 0.87)     # 중간
    c2 = (0.71, 0.02, 0.15)     # 더움
    if fr < 0.5:
        t = fr * 2.0
        a, b = c0, c1
    else:
        t = (fr - 0.5) * 2.0
        a, b = c1, c2
    return unreal.LinearColor(a[0] + (b[0] - a[0]) * t,
                              a[1] + (b[1] - a[1]) * t,
                              a[2] + (b[2] - a[2]) * t, 1.0)


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
        col = temp_color(tc)
        loc = unreal.Vector(x, y, z)
        unreal.SystemLibrary.draw_debug_point(world, loc, 8.0, col, DUR)
        if DRAW_FLOW:
            end = unreal.Vector(x + float(r["Ux"]) * U_SCALE,
                                y + float(r["Uy"]) * U_SCALE,
                                z + float(r["Uz"]) * U_SCALE)
            unreal.SystemLibrary.draw_debug_line(world, loc, end, col, DUR, 0.5)
        drawn += 1

    # 뷰포트 카메라를 방 전체가 보이는 위치로
    # 방은 x 0~800, y 0~570, z 0~270 cm. 남쪽(-y) 에서 비스듬히 내려다본다.
    try:
        cam_loc = unreal.Vector(400.0, -780.0, 430.0)
        cam_rot = unreal.Rotator(pitch=-15.0, yaw=90.0, roll=0.0)
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        ues.set_level_viewport_camera_info(cam_loc, cam_rot)
    except Exception as e:
        unreal.log_warning("SF_VIZ: camera set skipped (%s)" % e)

    msg = "SF_VIZ: %d/%d points (step=%d), flow=%s" % (drawn, n, step, DRAW_FLOW)
    unreal.log(msg)
    print(msg)


main()
