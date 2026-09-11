"""재배단 실제 광원 — 단마다 RectLight(식물등 핑크)가 선반을 비춘다.

배광(IES)이 확보되면 이 라이트의 IES Texture 슬롯에 꽂으면 그대로
실측 배광이 된다. 그 전까지는 사각 면광원 근사.

조명 상태는 data/_light.json {"pct": 0~100} 과 연동:
    pct > 0  → 라이트 켜짐 (밝기 = pct 비례)
    pct == 0 → 꺼짐
[SF 갱신]이 이 파일을 읽어 온도(광열)와 빛을 같이 맞춘다.

    py ue/ue_exec.py -f ue/sf_make_lights.py
"""
import json
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 100.0
RACK_X, RACK_Y = 4.0, 2.0
LED_Z = [1.28, 1.60]            # sf_make_racks 의 LED 바 높이
BED_W, BED_D = 2.40, 0.80
INTENSITY_LM = 9000.0           # 단당 광속 가정 (240 W 식물등급) — IES 오면 교체
COLOR = unreal.LinearColor(1.0, 0.35, 0.75, 1.0)   # 식물등 핑크

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 재배단이 옮겨져 있으면 그 위치에 등을 단다 (bed0 앵커)
for _a in eas.get_all_level_actors():
    if _a.get_actor_label() == "SF_Rack_bed0":
        _l = _a.get_actor_location()
        RACK_X, RACK_Y = _l.x / 100.0, _l.y / 100.0
        break

pct = 100.0
p = os.path.join(REPO, "data", "_light.json")
if os.path.isfile(p):
    pct = float(json.load(open(p, encoding="utf-8")).get("pct", 100))

for a in list(eas.get_all_level_actors()):
    if a.get_actor_label().startswith("SF_GrowLight"):
        eas.destroy_actor(a)

made = 0
for t, z in enumerate(LED_Z):
    a = eas.spawn_actor_from_class(
        unreal.RectLight,
        unreal.Vector(RACK_X * S, RACK_Y * S, (z - 0.03) * S),
        unreal.Rotator(0.0, -90.0, 0.0))        # 아래를 향해
    a.set_actor_label("SF_GrowLight_%d" % t)
    a.set_folder_path("SF/Rack")
    c = a.get_editor_property("light_component")
    c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    c.set_intensity(INTENSITY_LM * max(pct, 1.0) / 100.0)
    c.set_light_color(COLOR)
    c.set_editor_property("source_width", BED_W * 0.9 * S)
    c.set_editor_property("source_height", BED_D * 0.8 * S)
    c.set_editor_property("attenuation_radius", 320.0)
    c.set_editor_property("cast_shadows", True)
    a.set_actor_hidden_in_game(pct <= 0)
    c.set_visibility(pct > 0)
    made += 1

# 배경 태양이 너무 세면 식물등이 안 보인다 — 무드 조절
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SF_Sun":
        a.light_component.set_intensity(1.2)

# 재배단 + 등을 한 그룹으로 — 아무거나 잡고 끌면 같이 움직인다
try:
    unreal.ActorGroupingUtils.set_grouping_active(True)
    agu = unreal.get_default_object(unreal.ActorGroupingUtils)
    grp = [a for a in eas.get_all_level_actors()
           if a.get_actor_label().startswith(("SF_Rack", "SF_GrowLight"))]
    agu.group_actors(grp)
except Exception as e:
    unreal.log_warning("SF_LIGHTS: 그룹핑 실패 %s" % e)

les.save_current_level()
print("SF_LIGHTS: RectLight %d개 (단당 %.0f lm, 점등률 %.0f%%). "
      "IES 확보 시 IES Texture 슬롯에 장착" % (made, INTENSITY_LM, pct))
