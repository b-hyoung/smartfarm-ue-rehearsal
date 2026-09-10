"""Niagara Fluids 기체 시뮬 실험 — 냉기 연출용 (보기용, 예측 아님).

data/_fluids.json 파라미터:
    {"system": "/NiagaraFluids/.../Grid3D_Gas_Smoke",
     "label": "SF_Fluid_Test", "loc": [400,200,135], "rot": [0,0,0],
     "size": [820,600,280], "res": 96, "emit": [0,0,120]}

    py ue/ue_exec.py -f ue/sf_fluids_spawn.py
"""
import json
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = {}
p = os.path.join(REPO, "data", "_fluids.json")
if os.path.isfile(p):
    cfg = json.load(open(p, encoding="utf-8"))

SYSTEM = cfg.get("system",
                 "/NiagaraFluids/Templates/Gas/3D/Systems/Grid3D_Gas_Smoke")
LABEL = cfg.get("label", "SF_Fluid_Test")
LOC = cfg.get("loc", [400.0, 200.0, 135.0])
ROT = cfg.get("rot", [0.0, 0.0, 0.0])        # (roll, pitch, yaw)
SIZE = cfg.get("size", [820.0, 600.0, 280.0])
RES = int(cfg.get("res", 96))
EMIT = cfg.get("emit", None)                  # User.Emit Position (있는 템플릿만)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 같은 라벨 기존 액터 제거(재실행 대비)
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label() == LABEL:
        eas.destroy_actor(a)

sys_obj = unreal.load_asset(SYSTEM)
if not sys_obj:
    raise SystemExit("SF_FLUIDS: 시스템 로드 실패 %s" % SYSTEM)

loc = unreal.Vector(*[float(v) for v in LOC])
rot = unreal.Rotator(float(ROT[0]), float(ROT[1]), float(ROT[2]))
actor = eas.spawn_actor_from_class(unreal.NiagaraActor, loc, rot)
actor.set_actor_label(LABEL)
comp = actor.get_editor_property("niagara_component")
comp.set_asset(sys_obj)

comp.set_niagara_variable_vec3("User.WorldSpaceSize",
                               unreal.Vector(*[float(v) for v in SIZE]))
comp.set_niagara_variable_int("User.ResolutionMaxAxis", RES)
comp.set_niagara_variable_bool("User.DrawBounds", False)
if EMIT is not None:
    comp.set_niagara_variable_vec3("User.Emit Position",
                                   unreal.Vector(*[float(v) for v in EMIT]))
comp.reset_system()
print("SF_FLUIDS: %s 스폰  sys=%s loc=%s rot=%s size=%s res=%d emit=%s" %
      (LABEL, SYSTEM.split("/")[-1], LOC, ROT, SIZE, RES, EMIT))
