"""SF_Structure 용 온도변화 시퀀스 — 커튼(바람) + 1.1m 온도카펫 + A~D 마커.

표현 설계 ("바람을 통해 온도 변화를 어떻게 표현하나"):
    · 커튼 색 = 그 지점 공기 온도. 시간이 지나면 취출~끝자락 그라디언트가
      통째로 파래진다 (방이 식어 제트가 덜 데워짐) — 바람이 온도 변화를 말한다.
    · 방 공기 자체는 1.1 m 반투명 온도 카펫 — t=0 빨강 → t=900 파랑.
    · A/B/C/D 마커는 그 시각 실측(프로브) 온도색.
    재생 1초 = 실제 30초. 15분 냉각이 30초 루프 (PIE 자동재생).

방식은 sf_sequencer.py 와 동일: 프레임마다 액터(SF_Anim2_NN)를 만들고
시퀀스가 가시성만 토글한다.

    py ue/ue_exec.py -f ue/sf_sequencer2.py
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
FPS = 30
SPEEDUP = 30.0
SEQ_DIR = "/Game/Cinematics"
SEQ_NAME = "SEQ_SF_Flow"
SEQ_PATH = "%s/%s" % (SEQ_DIR, SEQ_NAME)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()


def build_jets(frame):
    """jet_NN.csv -> 커튼 4장 메시 (정점색 = 온도)."""
    path = os.path.join(REPO, "data", "jets", "jet_%02d.csv" % frame)
    sheets = {}
    kmax = smax = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k, st = int(r["k"]), int(r["step"])
            sheets.setdefault(r["dir"], {})[(k, st)] = (
                float(r["x"]) * S, float(r["y"]) * S, float(r["z"]) * S,
                float(r["T"]))
            kmax, smax = max(kmax, k + 1), max(smax, st + 1)
    verts, tris, norms, uvs, cols = [], [], [], [], []
    up = unreal.Vector(0.0, 0.0, 1.0)
    for d, grid in sheets.items():
        base = len(verts)
        for k in range(kmax):
            for st in range(smax):
                x, y, z, T = grid[(k, st)]
                verts.append(unreal.Vector(x, y, min(z, 268.0)))
                norms.append(up)
                uvs.append(unreal.Vector2D(st / (smax - 1.0), k / (kmax - 1.0)))
                cols.append(G.temp_color(T, quantize=0.5))
        for k in range(kmax - 1):
            for st in range(smax - 1):
                a = base + k * smax + st
                b = a + smax
                tris += [a, a + 1, b,   a + 1, b + 1, b]
                tris += [a, b, a + 1,   a + 1, b, b + 1]
    return verts, tris, norms, uvs, cols


def main():
    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    times = {m["frame"]: float(m["time_s"]) for m in man["frames"]}
    series = G.load_probe_series(REPO)
    mat_vc = G.vertex_color_material()
    mat_slice = G.slice_material()
    _t = unreal.ProcMeshTangent()
    _t.set_editor_property("tangent_x", unreal.Vector(1.0, 0.0, 0.0))

    # 단일 프레임용 정적 액터는 겹치니 숨긴다
    for a in eas.get_all_level_actors():
        if a.get_actor_label() in ("SF_Jets", "SF_Probes"):
            a.set_actor_hidden_in_game(True)
            a.set_is_temporarily_hidden_in_editor(True)

    actors = []
    for f in range(15):
        label = "SF_Anim2_%02d" % f
        for a in list(eas.get_all_level_actors()):
            if a.get_actor_label() == label:
                eas.destroy_actor(a)
        actor, pmc = G.get_proc_actor(label, "Anim2Mesh_%02d" % f)
        pmc.clear_all_mesh_sections()
        marks = G.build_markers(G.probe_points_at(series, times[f]),
                                r_sphere=11.0, r_bar=6.5)
        sections = (build_jets(f),
                    G.build_slice(G.load_slice(REPO, f)),
                    marks)
        for idx, data in enumerate(sections):
            verts, tris, normals, uvs, colors = data
            if not verts:
                continue
            pmc.create_mesh_section_linear_color(
                idx, verts, tris, normals, uvs, [], [], [], colors,
                [_t] * len(verts), False)
            # 0=커튼(더 투명) 1=온도카펫(주인공) 2=마커(불투명)
            if idx == 0:
                pmc.set_material(idx, G.curtain_material())
            elif idx == 1:
                pmc.set_material(idx, mat_slice)
            else:
                pmc.set_material(idx, mat_vc)
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        actors.append((f, actor))
        print("SF_SEQ2: %s  정점 %d" % (label, len(sections[0][0])))

    # ── 시퀀스 ─────────────────────────────────────────────
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)
    if not unreal.EditorAssetLibrary.does_directory_exist(SEQ_DIR):
        unreal.EditorAssetLibrary.make_directory(SEQ_DIR)
    seq = at.create_asset(SEQ_NAME, SEQ_DIR, unreal.LevelSequence,
                          unreal.LevelSequenceFactoryNew())
    end_s = max(times.values())
    win = []
    for i, (f, actor) in enumerate(actors):
        t0 = times[f]
        t1 = times[actors[i + 1][0]] if i + 1 < len(actors) \
            else end_s + (end_s - times[actors[i - 1][0]])
        win.append((actor, int(round(t0 / SPEEDUP * FPS)),
                    max(int(round(t1 / SPEEDUP * FPS)),
                        int(round(t0 / SPEEDUP * FPS)) + 1)))
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(win[-1][2])
    for actor, a, b in win:
        binding = seq.add_possessable(actor)
        track = binding.add_track(unreal.MovieSceneVisibilityTrack)
        section = track.add_section()
        section.set_range(a, b)
        for ch in section.get_channels_by_type(
                unreal.MovieSceneScriptingBoolChannel):
            ch.set_default(True)
            ch.add_key(unreal.FrameNumber(a), True)
    unreal.EditorAssetLibrary.save_asset(SEQ_PATH)

    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == "SF_SeqPlayer":
            eas.destroy_actor(a)
    act = eas.spawn_actor_from_class(unreal.LevelSequenceActor,
                                     unreal.Vector(0, 0, 0))
    act.set_actor_label("SF_SeqPlayer")
    act.set_sequence(seq)
    settings = act.get_editor_property("playback_settings")
    loop = unreal.MovieSceneSequenceLoopCount()
    loop.set_editor_property("value", -1)
    settings.set_editor_property("loop_count", loop)
    settings.set_editor_property("auto_play", True)
    act.set_editor_property("playback_settings", settings)

    les.save_current_level()
    print("SF_SEQ2: %s · 15프레임 · 길이 %.1f초 (실제 900초, 30배속) · PIE 자동재생"
          % (SEQ_PATH, win[-1][2] / float(FPS)))


main()
