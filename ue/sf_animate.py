"""SF_Rehearsal: 15프레임 냉각 애니메이션. (목적 O3)

프레임을 순서대로 그리고 각 프레임을 PNG 로 굽는다.
디버그 드로우는 지속시간을 짧게 주면 다음 프레임에서 자연히 사라지므로,
프레임마다 flush 하고 다시 그린다.

환경변수
    SF_FRAME      한 프레임만 그릴 때 (0~14). 없으면 전체 순회
    SF_SHOT       1 이면 프레임마다 스크린샷 저장
    SF_POINTS     다운샘플 목표 점 수 (기본 2500)

    py ue/ue_exec.py -f ue/sf_animate.py
"""
import csv
import os
import unreal

import sys as _sys
_sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sf_config as _CFG
REPO = _CFG.REPO
FRAME_DIR = os.path.join(REPO, "data", "frames")
SHOT_DIR = _CFG.ANIM_SHOT_DIR

TMIN, TMAX = 16.35, 28.85     # ★ 전 프레임 고정. 프레임마다 바꾸면 비교 불가
POS_SCALE = 100.0
TARGET_POINTS = int(os.environ.get("SF_POINTS", "2500"))
DUR = 1.0e6                 # 지속 표시 (flush 로 지움)
U_SCALE = 60.0
DRAW_FLOW = False           # 애니메이션에선 선이 많으면 읽기 어려움


def temp_color(tc):
    """섭씨 -> LinearColor. 파랑 -> 밝은 회색 -> 빨강 (발산형)."""
    fr = (tc - TMIN) / (TMAX - TMIN)
    fr = 0.0 if fr < 0.0 else (1.0 if fr > 1.0 else fr)
    c0, c1, c2 = (0.23, 0.30, 0.75), (0.87, 0.87, 0.87), (0.71, 0.02, 0.15)
    if fr < 0.5:
        t, a, b = fr * 2.0, c0, c1
    else:
        t, a, b = (fr - 0.5) * 2.0, c1, c2
    return unreal.LinearColor(a[0] + (b[0] - a[0]) * t,
                              a[1] + (b[1] - a[1]) * t,
                              a[2] + (b[2] - a[2]) * t, 1.0)


def world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


_cache = {}


def load(idx):
    if idx in _cache:
        return _cache[idx]
    path = os.path.join(FRAME_DIR, "frame_%02d.csv" % idx)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    step = max(1, len(rows) // TARGET_POINTS)
    sel = [(float(r["x"]) * POS_SCALE, float(r["y"]) * POS_SCALE,
            float(r["z"]) * POS_SCALE, float(r["T"]) - 273.15,
            float(r["Ux"]), float(r["Uy"]), float(r["Uz"]))
           for r in rows[::step]]
    _cache[idx] = (sel, len(rows), step)
    return _cache[idx]


def draw(idx):
    w = world()
    unreal.SystemLibrary.flush_persistent_debug_lines(w)
    sel, n, step = load(idx)
    for (x, y, z, tc, ux, uy, uz) in sel:
        col = temp_color(tc)
        loc = unreal.Vector(x, y, z)
        unreal.SystemLibrary.draw_debug_point(w, loc, 9.0, col, DUR)
        if DRAW_FLOW:
            unreal.SystemLibrary.draw_debug_line(
                w, loc, unreal.Vector(x + ux * U_SCALE, y + uy * U_SCALE,
                                      z + uz * U_SCALE), col, DUR, 0.5)
    return len(sel), n, step


def main():
    os.makedirs(SHOT_DIR, exist_ok=True)
    one = os.environ.get("SF_FRAME")
    shot = os.environ.get("SF_SHOT") == "1"
    frames = [int(one)] if one is not None else list(range(15))

    for i in frames:
        drawn, n, step = draw(i)
        msg = "SF_ANIM: frame_%02d  %d/%d pts (step=%d)" % (i, drawn, n, step)
        unreal.log(msg)
        print(msg)
        # ⚠ 에디터 뷰포트는 포커스가 없으면 다시 그리지 않는다.
        #    강제 무효화하지 않으면 창을 캡처해도 '이전 프레임'이 찍힌다.
        try:
            unreal.get_editor_subsystem(
                unreal.LevelEditorSubsystem).editor_invalidate_viewports()
        except Exception as e:
            unreal.log_warning("invalidate: %s" % e)
        if shot:
            unreal.AutomationLibrary.take_high_res_screenshot(
                1400, 900, os.path.join(SHOT_DIR, "anim_%02d.png" % i))


main()
