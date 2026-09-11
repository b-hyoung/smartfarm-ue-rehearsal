"""재생 배속 클릭 전환 헬퍼 — 툴바 버튼(sf_toolbar.py)이 부른다.

go(30) → SEQ_SF_Flow      (30fps · 재생 1초 = 실제 30초 · 32초)
go(10) → SEQ_SF_Flow_10x  (10fps · 재생 1초 = 실제 10초 · 90초)
stop() → 일시정지
"""
import unreal

SEQ_DIR = "/Game/Cinematics"


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
