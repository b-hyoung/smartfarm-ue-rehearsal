"""[SF 갱신] — 에어컨을 옮긴 자리 기준으로 예상 온도·기류를 다시 만들어 재생.

    SF_AC_Root 위치 읽기 → data/_ac.json
      → (외부 py) src.predict_mock: 단면·커튼·프로브 재생성 (수식, 수 초)
      → sf_sequencer2: 30배속·10배속 시퀀스 재빌드
      → 재생

지금 예측기는 수식 모델(임시)이다. 나중에 케이스 라이브러리/대리모델이 오면
predict_mock 자리만 바뀌고 이 버튼·화면은 그대로다.

    py ue/ue_exec.py -c "import sf_refresh; sf_refresh.run()"   (또는 툴바 버튼)
"""
import json
import os
import subprocess
import sys

import unreal

UE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(UE_DIR)
if UE_DIR not in sys.path:
    sys.path.append(UE_DIR)


def _exec_script(name, seq_cfg):
    with open(os.path.join(REPO, "data", "_seq.json"), "w",
              encoding="utf-8") as fh:
        json.dump(seq_cfg, fh)
    path = os.path.join(UE_DIR, name)
    src = open(path, encoding="utf-8").read()
    g = {"__name__": "__main__", "__file__": path}
    exec(compile(src, path, "exec"), g)


def run():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    root = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SF_AC_Root":
            root = a
            break
    if root is None:
        unreal.log_warning("SF_REFRESH: SF_AC_Root 가 없습니다")
        return
    loc = root.get_actor_location()
    ac = [round(loc.x / 100.0, 3), round(loc.y / 100.0, 3)]
    with open(os.path.join(REPO, "data", "_ac.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"ac": ac}, fh)
    unreal.log("SF_REFRESH: AC=(%.2f, %.2f)m — 예측 생성 중..." % (ac[0], ac[1]))

    r = subprocess.run(["py", "-m", "src.predict_mock"], cwd=REPO,
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        unreal.log_warning("SF_REFRESH: 예측기 실패\n%s" % (r.stderr or "")[-800:])
        return
    unreal.log("SF_REFRESH: %s" % (r.stdout or "").strip().splitlines()[-1])

    # 시퀀스 재빌드 (30배속은 액터 재생성, 10배속은 재사용)
    _exec_script("sf_sequencer2.py",
                 {"speedup": 30, "fps": 30, "rebuild_actors": True})
    _exec_script("sf_sequencer2.py",
                 {"speedup": 10, "fps": 10, "rebuild_actors": False})

    import importlib
    import sf_play
    importlib.reload(sf_play)
    sf_play.go(30)
    unreal.log("SF_REFRESH: 완료 — 새 위치 기준으로 재생 중")


if __name__ == "__main__":
    run()
