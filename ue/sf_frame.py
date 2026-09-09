"""레벨에 특정 프레임 하나를 올린다 — 에디터에서 눈으로 넘겨보기용.

`sf_bake_anim.py` 는 15프레임을 돌면서 PNG 로 굽는다(결과물용).
이건 반대로 **에디터 뷰포트에 한 프레임만 세워두는** 용도다. 각도를 돌려보거나
특정 시각의 기류를 뜯어볼 때 쓴다.

    sh ue/frame.sh 7        # 450초 상태를 레벨에 올림
    sh ue/frame.sh 14       # 900초

액터(SF_Streamlines, SF_Arrows)는 재사용하고 메시 섹션만 갈아 끼운다.
"""
import importlib
import json
import os
import sys

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE_DIR = os.path.join(REPO, "ue")
if UE_DIR not in sys.path:
    sys.path.append(UE_DIR)

import sf_geom as G  # noqa: E402

# ⚠ UE 파이썬 세션은 한 번 import 한 모듈을 계속 들고 있다.
#   sf_geom 을 고쳐도 reload 하지 않으면 **옛 코드가 그대로 돈다**
#   (색 범위를 바꿨는데 예전 값으로 구워지는 사고가 실제로 났다).
importlib.reload(G)

frame = 14
cfg = os.path.join(REPO, "data", "_nia.json")
if os.path.isfile(cfg):
    with open(cfg, encoding="utf-8") as f:
        frame = int(json.load(f).get("frame", 14))

man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                     encoding="utf-8"))
t_s = next((m["time_s"] for m in man["frames"] if m["frame"] == frame), None)

lines = G.load_ribbon(REPO, frame)
rows = G.load_arrows(REPO, frame)

_, ol = G.get_proc_actor("SF_Outline", "OutlineMesh")
G.set_section(ol, G.build_room_outline())

_, sl = G.get_proc_actor("SF_Slice", "SliceMesh")
G.set_section(sl, G.build_slice(G.load_slice(REPO, frame)), translucent=True)

_, vs = G.get_proc_actor("SF_VSlice", "VSliceMesh")
G.set_section(vs, G.build_vslice(G.load_vslice(REPO, frame)), translucent=True)

_, tube = G.get_proc_actor("SF_Streamlines", "FlowMesh")
_, arrow = G.get_proc_actor("SF_Arrows", "ArrowMesh")
G.set_section(tube, G.build_tubes(lines), animated=True)
G.set_section(arrow, G.build_arrows(rows), animated="arrow")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
msg = ("SF_FRAME: frame %d (t=%s초)  유선 %d · 화살표 %d  색범위 %.1f~%.1f C"
       % (frame, "%.0f" % t_s if t_s is not None else "?",
          len(lines), len(rows), G.TMIN, G.TMAX))
unreal.log(msg)
print(msg)
