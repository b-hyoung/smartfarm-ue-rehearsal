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

# 레벨이 다 열린 뒤 프레임 액터(SF_Anim2_*)를 다시 숨긴다.
# '에디터 임시 숨김'은 저장이 안 돼서, 안 하면 15장의 반투명 단면이 겹쳐
# z-파이팅으로 색이 반짝거린다 (2026-09-11 버그 제보).
import unreal as _u

_st = {"t": 0.0, "h": None}


def _hide_after_load(dt):
    _st["t"] += dt
    if _st["t"] < 5.0:          # 에디터·레벨 로딩이 끝날 시간을 준다
        return
    try:
        import sf_play
        sf_play.hide_frames()
    except Exception as e:
        _u.log_warning("SF init_unreal: 프레임 숨김 실패 — %s" % e)
    finally:
        if _st["h"] is not None:
            _u.unregister_slate_post_tick_callback(_st["h"])
            _st["h"] = None


_st["h"] = _u.register_slate_post_tick_callback(_hide_after_load)
