"""4방향 취출 리본 커튼을 레벨에 세운다 — SF_Jets (ProceduralMesh).

    data/jets/jet_NN.csv (src/make_jets.py) -> 시트 4장, 정점색 = 온도

프레임 선택: data/_jets.json {"frame": N}  (없으면 5 = t=320s)

    py ue/ue_exec.py -f ue/sf_jets.py
"""
import csv
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
importlib.reload(G)

S = 100.0
frame = 5
cfg_p = os.path.join(REPO, "data", "_jets.json")
if os.path.isfile(cfg_p):
    frame = int(json.load(open(cfg_p, encoding="utf-8")).get("frame", 5))

path = os.path.join(REPO, "data", "jets", "jet_%02d.csv" % frame)
sheets = {}          # dir -> {(k, step): (x,y,z,T)}
kmax = smax = 0
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        d = r["dir"]
        k, st = int(r["k"]), int(r["step"])
        sheets.setdefault(d, {})[(k, st)] = (
            float(r["x"]) * S, float(r["y"]) * S, float(r["z"]) * S,
            float(r["T"]))
        kmax = max(kmax, k + 1)
        smax = max(smax, st + 1)

verts, tris, norms, uvs, cols = [], [], [], [], []
up = unreal.Vector(0.0, 0.0, 1.0)
for d, grid in sheets.items():
    base = len(verts)
    for k in range(kmax):
        for st in range(smax):
            x, y, z, T = grid[(k, st)]
            # 천장 z-파이팅 방지로 2 cm 내림
            verts.append(unreal.Vector(x, y, min(z, 268.0)))
            norms.append(up)
            uvs.append(unreal.Vector2D(st / (smax - 1.0), k / (kmax - 1.0)))
            cols.append(G.temp_color(T, quantize=0.5))
    for k in range(kmax - 1):
        for st in range(smax - 1):
            a = base + k * smax + st
            b = a + smax
            # 양면 (언릿 단면 대비 두 방향 다)
            tris += [a, a + 1, b,   a + 1, b + 1, b]
            tris += [a, b, a + 1,   a + 1, b, b + 1]

actor, pmc = G.get_proc_actor("SF_Jets", "JetMesh")
G.set_section(pmc, (verts, tris, norms, uvs, cols))

# ── 커튼은 SF_AC_Root 를 따라간다 ────────────────────────────
# 정점은 원본 방 좌표(에어컨 = 400,200,270cm) 기준이므로, 루트가 어디로
# 옮겨졌든 그 차이만큼 액터를 이동시키면 취출구에 정확히 붙는다.
AC_HOME = unreal.Vector(400.0, 200.0, 270.0)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SF_AC_Root":
        d = a.get_actor_location() - AC_HOME
        actor.set_actor_location(d, False, False)
        print("SF_JETS: SF_AC_Root 따라 이동 delta=(%.0f,%.0f,%.0f)" %
              (d.x, d.y, d.z))
        break

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("SF_JETS: frame %d  시트 %d장  정점 %d  삼각형 %d" %
      (frame, len(sheets), len(verts), len(tris) // 3))
