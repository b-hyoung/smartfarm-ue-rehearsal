"""재생 배속 클릭 전환 헬퍼 — 툴바 버튼(sf_toolbar.py)이 부른다.

go(30) → SEQ_SF_Flow      (30fps · 재생 1초 = 실제 30초 · 32초)
go(10) → SEQ_SF_Flow_10x  (10fps · 재생 1초 = 실제 10초 · 90초)
stop() → 일시정지
"""
import unreal

import os as _os, sys as _sys
_sys.path.append(_os.path.dirname(_os.path.abspath(__file__)))
import sf_config as _CFG
SEQ_DIR = _CFG.SEQ_DIR


def _seq_path(speed):
    name = "SEQ_SF_Flow" if int(speed) == 30 else "SEQ_SF_Flow_%dx" % int(speed)
    return "%s/%s" % (SEQ_DIR, name)


def go(speed):
    seq = unreal.load_asset(_seq_path(speed))
    if seq is None:
        unreal.log_warning("SF_PLAY: %s 없음 — sf_sequencer2.py 로 먼저 만드세요"
                           % _seq_path(speed))
        return
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SF_SeqPlayer":
            a.set_sequence(seq)          # PIE 자동재생도 이 배속을 따라간다
            break
    lib = unreal.LevelSequenceEditorBlueprintLibrary
    lib.open_level_sequence(seq)
    lib.play()
    unreal.log("SF_PLAY: %s 재생 (1초 = 실제 %d초)" % (seq.get_name(), int(speed)))


def stop():
    lib = unreal.LevelSequenceEditorBlueprintLibrary
    lib.pause()
    unreal.log("SF_PLAY: 일시정지")


def hide_frames():
    """프레임 액터(SF_Anim2_*) 전부 숨김.

    ⚠ '에디터 임시 숨김'은 레벨에 저장되지 않는다 — 에디터를 새로 켜면
    15장의 반투명 단면이 전부 겹쳐 보여서 z-파이팅으로 색이 반짝거린다
    (사용자 버그 제보). 그래서 에디터 시작 시(init_unreal) 이걸 다시 돌린다.
    시퀀서가 재생할 때는 가시성 트랙이 알아서 켠다.
    """
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in eas.get_all_level_actors():
        if a.get_actor_label().startswith(("SF_Anim2_", "SF_Anim_")):
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            n += 1
    unreal.log("SF_PLAY: 프레임 액터 %d개 숨김" % n)
    return n
