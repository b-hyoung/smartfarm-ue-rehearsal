"""SF_Structure: 구조만 있는 새 레벨 — 깨끗한 재시작용.

들어가는 것 (구조):
    조명(SF_Sun/SF_Sky) · D자 바닥(SF_FloorD) · 방 윤곽(SF_Outline)
    에어컨 본체·취출구(sf_make_ac 재사용) · A~D 중립 마커(SF_Probes)
안 들어가는 것 (데이터 표현):
    단면·유선·화살표 — 데이터가 결정되면 그때 같은 스크립트로 얹는다.

    py ue/ue_exec.py -f ue/sf_make_level2.py
"""
import importlib
import os
import sys

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UE_DIR = os.path.join(REPO, "ue")
if UE_DIR not in sys.path:
    sys.path.append(UE_DIR)

import sf_geom as G  # noqa: E402
importlib.reload(G)

LEVEL_PATH = "/Game/Maps/SF_Structure"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
    les.load_level(LEVEL_PATH)
    print("SF_LEVEL2: 기존 %s 열음" % LEVEL_PATH)
else:
    les.new_level(LEVEL_PATH)
    print("SF_LEVEL2: %s 생성" % LEVEL_PATH)

existing = {a.get_actor_label() for a in eas.get_all_level_actors()}


def spawn(cls, loc, rot=None, label=None):
    a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator())
    if a and label:
        a.set_actor_label(label)
    return a


if "SF_Sun" not in existing:
    sun = spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 600),
                unreal.Rotator(0, -55, -30), "SF_Sun")
    sun.light_component.set_intensity(3.0)
if "SF_Sky" not in existing:
    sky = spawn(unreal.SkyLight, unreal.Vector(0, 0, 400), None, "SF_Sky")
    try:
        sky.light_component.set_intensity(1.2)
    except Exception:
        pass

# 방 윤곽 — 바닥 테두리 + 천장 테두리
_, ol = G.get_proc_actor("SF_Outline", "OutlineMesh")
G.set_section(ol, G.build_room_outline())

# A~D 중립 마커 (위치만 — 값은 데이터가 오면)
POS = {"A": (400.0, 200.0), "B": (750.0, 80.0), "C": (400.0, 450.0),
       "D": (50.0, 80.0)}
pts = [(x, y, [(10.0, 0.0), (110.0, 0.0), (170.0, 0.0)])
       for x, y in POS.values()]
_, mk = G.get_proc_actor("SF_Probes", "ProbeMesh")
G.set_section(mk, G.build_markers(pts, r_sphere=9.0, r_bar=5.5, neutral=True))

les.save_current_level()
print("SF_LEVEL2: 구조 저장 완료, actors=%d" %
      len(eas.get_all_level_actors()))
