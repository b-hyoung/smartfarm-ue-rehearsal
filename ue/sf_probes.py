"""A/B/C/D 측정점을 레벨에 세운다 — 숫자 없이 **색으로만** 읽히게.

실측 온도계를 놓을 지점이다. 화면에는 숫자를 안 띄운다.
숫자가 붙으면 눈이 거기로 쏠려서 방 전체 분포를 안 본다.
정확한 값이 필요하면 data/probes.csv 를 보면 된다.

    A  UE(4.0, 2.0)   에어컨 바로 아래
    B  UE(7.5, 0.8)   평벽 쪽 오른쪽
    C  UE(4.0, 4.5)   반원 안쪽 (정체 구역)
    D  UE(0.5, 0.8)   평벽 쪽 왼쪽 (B 와 대칭)

    높이 0.1 / 1.1 / 1.7 m. 라벨은 1.1 m(서 있을 때 몸통 높이) 값을 쓴다.

값의 출처는 **OpenFOAM probes 원본**(data/probes.csv)이다.
화면의 유선·화살표 색은 셀 평균을 거친 값이지만 probes 는 솔버가 그 좌표에서
직접 뽑은 값이라 중간 가공이 없다. 실측 비교는 이쪽을 기준으로 해야 한다.

    py ue/ue_exec.py -f ue/sf_probes.py      # data/_nia.json 의 frame 사용
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
HEIGHTS = (0.1, 1.1, 1.7)
LABEL_H = 1.1                 # 라벨에 쓸 기준 높이

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def load_probes():
    """probes.csv -> {지점: {"xy": (x,y), 높이: [(t, T), ...]}}"""
    out = {}
    path = os.path.join(REPO, "data", "probes.csv")
    if not os.path.isfile(path):
        raise RuntimeError("probes.csv 없음 — py -m src.pipeline.make_probes 먼저")
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = out.setdefault(r["point"], {"xy": (float(r["ue_x"]),
                                                   float(r["ue_y"])), "z": {}})
            p["z"].setdefault(round(float(r["z"]), 2), []).append(
                (float(r["t_s"]), float(r["T_C"])))
    return out


def at_time(series, t):
    """가장 가까운 시각의 값. probes 는 1.15초 간격이라 보간이 필요 없다."""
    return min(series, key=lambda kv: abs(kv[0] - t))[1]


def text_actor(label, loc, text, color):
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == label:
            eas.destroy_actor(a)
    # TextRender 는 단면(뒤에서 보면 안 보인다). 기본이 +X 를 향하므로
    # yaw -90 으로 -Y 쪽(주 카메라가 있는 방향)을 보게 한다.
    act = eas.spawn_actor_from_class(unreal.TextRenderActor, loc,
                                     unreal.Rotator(0, 0, -90))
    act.set_actor_label(label)
    c = act.get_editor_property("text_render")
    c.set_editor_property("text", unreal.Text(text))
    c.set_editor_property("world_size", 42.0)
    c.set_editor_property("text_render_color", color)
    c.set_editor_property("horizontal_alignment",
                          unreal.HorizTextAligment.EHTA_CENTER)
    c.set_editor_property("vertical_alignment",
                          unreal.VerticalTextAligment.EVRTA_TEXT_BOTTOM)
    return act


def main():
    frame = 14
    cfg = os.path.join(REPO, "data", "_nia.json")
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8") as f:
            frame = int(json.load(f).get("frame", 14))
    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    t_s = next(m["time_s"] for m in man["frames"] if m["frame"] == frame)

    pr = load_probes()
    pts, lines = [], []
    for name in ("A", "B", "C", "D"):
        p = pr[name]
        x, y = p["xy"][0] * S, p["xy"][1] * S
        stack = [(z * S, at_time(p["z"][round(z, 2)], t_s)) for z in HEIGHTS]
        pts.append((x, y, stack))
        t11 = at_time(p["z"][round(LABEL_H, 2)], t_s)
        # ⚠ 숫자는 안 띄운다. 온도는 **색**으로 읽고, 글자는 어느 지점인지만 알린다.
        #   숫자가 붙으면 눈이 색 대신 숫자를 읽어서 전체 분포가 안 보인다.
        text_actor("SF_Probe_%s" % name,
                   unreal.Vector(x, y, 196.0), name,
                   unreal.Color(235, 238, 245, 255))
        lines.append("%s (%.1f, %.1f)  0.1m %.2f / 1.1m %.2f / 1.7m %.2f C"
                     % (name, p["xy"][0], p["xy"][1],
                        stack[0][1], stack[1][1], stack[2][1]))

    _, pmc = G.get_proc_actor("SF_Probes", "ProbeMesh")
    G.set_section(pmc, G.build_markers(pts, r_sphere=11.0, r_bar=6.5))

    les.save_current_level()
    msg = "SF_PROBE: frame %d (t=%.0f초)\n        " % (frame, t_s) + \
          "\n        ".join(lines)
    unreal.log(msg)
    print(msg)


main()
