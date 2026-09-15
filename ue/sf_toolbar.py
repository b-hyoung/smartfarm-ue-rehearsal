"""레벨 에디터 툴바에 재생 버튼 3개를 단다 — 클릭으로 배속 전환.

    [SF 30배속] [SF 10배속] [SF 정지]

등록은 세션 한정이라, 에디터 시작마다 자동 등록되도록
ue/Content/Python/init_unreal.py 가 이 모듈을 부른다.

    py ue/ue_exec.py -f ue/sf_toolbar.py   (수동 등록)
"""
import unreal

import os as _os

_UE_DIR = _os.path.dirname(_os.path.abspath(__file__))   # 하드코딩 제거 - 실행 위치에서 파생
UE_DIR_CMD = ("import sys, importlib; "
              "p = r'%s'; "
              "sys.path.append(p) if p not in sys.path else None; "
              "import sf_play; importlib.reload(sf_play); ") % _UE_DIR

BUTTONS = [
    ("SF_Refresh", "SF 갱신",
     "에어컨(SF_AC_Root)을 옮긴 위치 기준으로 예상 온도·기류 재생성 (임시 수식 예측)",
     "import sf_refresh; importlib.reload(sf_refresh); sf_refresh.run()"),
    ("SF_Play30", "SF 30배속", "32초 재생 (1초 = 실제 30초)", "sf_play.go(30)"),
    ("SF_Play10", "SF 10배속", "90초 재생 (1초 = 실제 10초)", "sf_play.go(10)"),
    ("SF_Stop", "SF 정지", "재생 일시정지", "sf_play.stop()"),
]


def register():
    menus = unreal.ToolMenus.get()
    toolbar = menus.find_menu("LevelEditor.LevelEditorToolBar.User")
    if toolbar is None:
        unreal.log_warning("SF_TOOLBAR: 툴바 메뉴를 못 찾음")
        return
    for name, label, tip, call in BUTTONS:
        e = unreal.ToolMenuEntry(
            name=name, type=unreal.MultiBlockType.TOOL_BAR_BUTTON)
        e.set_label(label)
        e.set_tool_tip(tip)
        e.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, "",
                             UE_DIR_CMD + call)
        toolbar.add_menu_entry("SmartFarm", e)
    menus.refresh_all_widgets()
    unreal.log("SF_TOOLBAR: 버튼 %d개 등록" % len(BUTTONS))
    print("SF_TOOLBAR: 버튼 %d개 등록" % len(BUTTONS))


register()
