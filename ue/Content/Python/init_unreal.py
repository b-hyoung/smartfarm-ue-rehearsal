"""에디터 시작 시 자동 실행 — SF 재생 툴바 버튼 등록."""
import os
import sys

UE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if UE_DIR not in sys.path:
    sys.path.append(UE_DIR)

try:
    import sf_toolbar  # noqa: F401  (import 시점에 register() 실행)
except Exception as e:  # 버튼이 없어도 에디터는 떠야 한다
    import unreal
    unreal.log_warning("SF init_unreal: 툴바 등록 실패 — %s" % e)
