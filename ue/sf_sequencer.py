"""언리얼 안에서 **재생 가능한** 애니메이션을 만든다 — 레벨 시퀀스

지금까지의 애니메이션은 PNG 로 구워서 GIF/MP4 로 묶은 것이라 UE 밖에서만 볼 수 있었다.
이건 시퀀서에서 재생 · 스크럽 · 구간반복이 되고, PIE 에서도 나오고,
Movie Render Queue 로 고화질 출력도 된다.

방식
    프레임마다 액터를 하나씩 만들어 두고(SF_Anim_00 ~ 14), 시퀀스가 **가시성만**
    켰다 껐다 한다. 매 프레임 메시를 다시 만들면 재생이 불가능하게 느리다
    (한 프레임 굽는 데 수 초). 가시성 토글은 공짜다.

    메모리는 15 x 약 37,000 정점 = 55만 정점. ProceduralMesh 로 충분히 감당된다.

    py ue/ue_exec.py -f ue/sf_sequencer.py
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
#   reload 하지 않으면 sf_geom 을 고쳐도 옛 코드가 그대로 돈다.
importlib.reload(G)

SEQ_DIR = "/Game/Cinematics"
SEQ_NAME = "SEQ_SF_Flow"
SEQ_PATH = "%s/%s" % (SEQ_DIR, SEQ_NAME)

# 시간 축 매핑: **재생 1초 = 실제 30초** (15분 → 30초로 압축)
# 30 fps 에서 이 배율이면 "표시 프레임 번호 = 실제 경과 초" 가 정확히 맞아떨어진다.
#   실제 900초 → 900 표시프레임 → 30 fps → 30초 재생
# ⚠ CFD 프레임 간격이 60~70초로 균일하지 않다. 프레임마다 같은 길이를 주면
#   시간이 고르게 흐르지 않는다 → manifest 의 time_s 를 그대로 쓴다.
FPS = 30
SPEEDUP = 30.0      # 실제 몇 초를 재생 1초에 담을지

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()


def build_frame_actors(frames, man):
    """프레임마다 액터 하나. 유선 0, 화살표 1, A/B/C/D 마커 2."""
    series = G.load_probe_series(REPO)
    times = {m["frame"]: float(m["time_s"]) for m in man["frames"]}
    actors = []
    for f in frames:
        label = "SF_Anim_%02d" % f
        for a in list(eas.get_all_level_actors()):
            if a.get_actor_label() == label:
                eas.destroy_actor(a)

        actor, pmc = G.get_proc_actor(label, "AnimMesh_%02d" % f)
        lines = G.load_ribbon(REPO, f)
        rows = G.load_arrows(REPO, f)
        mat_arrow = G.vertex_color_material()
        mat_flow = G.flow_anim_material()      # 유선만 흐름 무늬
        pmc.clear_all_mesh_sections()

        _t = unreal.ProcMeshTangent()
        _t.set_editor_property("tangent_x", unreal.Vector(1.0, 0.0, 0.0))
        marks = G.build_markers(G.probe_points_at(series, times[f]),
                                r_sphere=11.0, r_bar=6.5)
        slice_mesh = G.build_slice(G.load_slice(REPO, f))
        for idx, data in enumerate((G.build_tubes(lines), G.build_arrows(rows),
                                    marks, slice_mesh)):
            verts, tris, normals, uvs, colors = data
            if not verts:
                continue
            pmc.create_mesh_section_linear_color(
                idx, verts, tris, normals, uvs, [], [], [], colors,
                [_t] * len(verts), False)
            if idx == 0:
                pmc.set_material(idx, mat_flow)             # 유선 — 흐름 무늬
            elif idx == 1:
                pmc.set_material(idx, G.arrow_anim_material())  # 화살표 — 마루 이동
            elif idx == 3:
                pmc.set_material(idx, G.slice_material())  # 온도 단면 — 반투명
            else:
                pmc.set_material(idx, mat_arrow)

        # 시퀀스가 켜 주기 전까지는 전부 꺼둔다.
        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)
        actors.append((f, actor))
        print("SF_SEQ: %s  유선 %d · 화살표 %d · 마커 %d"
              % (label, len(lines), len(rows), len(marks[0])))
    return actors


def frame_windows(actors, man):
    """액터마다 (시작, 끝) 표시프레임. manifest 의 실제 시각에 비례한다."""
    times = {m["frame"]: float(m["time_s"]) for m in man["frames"]}
    end_s = max(times.values())
    win = []
    for i, (f, actor) in enumerate(actors):
        t0 = times[f]
        t1 = times[actors[i + 1][0]] if i + 1 < len(actors) else end_s
        if i + 1 == len(actors):          # 마지막 프레임도 한 칸은 보여준다
            t1 = end_s + (end_s - times[actors[i - 1][0]])
        a = int(round(t0 / SPEEDUP * FPS))
        b = int(round(t1 / SPEEDUP * FPS))
        win.append((actor, a, max(b, a + 1)))
    return win


def build_sequence(actors, man):
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)
    if not unreal.EditorAssetLibrary.does_directory_exist(SEQ_DIR):
        unreal.EditorAssetLibrary.make_directory(SEQ_DIR)

    seq = at.create_asset(SEQ_NAME, SEQ_DIR, unreal.LevelSequence,
                          unreal.LevelSequenceFactoryNew())
    win = frame_windows(actors, man)
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(win[-1][2])

    for actor, a, b in win:
        binding = seq.add_possessable(actor)
        track = binding.add_track(unreal.MovieSceneVisibilityTrack)
        section = track.add_section()
        section.set_range(a, b)
        # 가시성 트랙의 bool 채널. UE 버전에 따라 True 의 의미가 뒤집히는 일이
        # 있어서, 만들고 나서 실제로 스크럽해 눈으로 확인해야 한다.
        # 5.8 의 이름은 find_channels_by_type 이 아니라 get_channels_by_type 이다
        for ch in section.get_channels_by_type(
                unreal.MovieSceneScriptingBoolChannel):
            ch.set_default(True)
            ch.add_key(unreal.FrameNumber(a), True)
    unreal.EditorAssetLibrary.save_asset(SEQ_PATH)
    return seq


def place_sequence_actor(seq):
    """레벨에 LevelSequenceActor 를 놓고 자동재생+반복을 켠다.

    시퀀서 창에서 재생하는 것과 별개로, **에디터에서 Play(PIE) 를 눌러도**
    돌아가게 하려면 레벨에 이 액터가 있어야 한다.
    """
    for a in list(eas.get_all_level_actors()):
        if a.get_actor_label() == "SF_SeqPlayer":
            eas.destroy_actor(a)
    act = eas.spawn_actor_from_class(unreal.LevelSequenceActor,
                                     unreal.Vector(0, 0, 0))
    act.set_actor_label("SF_SeqPlayer")
    act.set_sequence(seq)
    # auto_play / loop_count 는 액터가 아니라 playback_settings 구조체에 있다.
    settings = act.get_editor_property("playback_settings")
    loop = unreal.MovieSceneSequenceLoopCount()
    loop.set_editor_property("value", -1)          # -1 = 무한 반복
    settings.set_editor_property("loop_count", loop)
    settings.set_editor_property("auto_play", True)
    act.set_editor_property("playback_settings", settings)
    return act


def main():
    frames = list(range(15))

    # 단일 프레임용 액터는 겹쳐 보이니 꺼둔다 (frame.sh 로 다시 켜서 쓰면 된다)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() in ("SF_Streamlines", "SF_Arrows",
                                   "SF_Probes", "SF_Slice"):
            a.set_actor_hidden_in_game(True)
            a.set_is_temporarily_hidden_in_editor(True)

    man = json.load(open(os.path.join(REPO, "data", "frames", "manifest.json"),
                         encoding="utf-8"))
    actors = build_frame_actors(frames, man)
    seq = build_sequence(actors, man)
    place_sequence_actor(seq)
    les.save_current_level()

    dur = seq.get_playback_end() / float(FPS)
    msg = ("SF_SEQ: %s · %d프레임 · %d fps · 길이 %.1f초 "
           "(실제 %.0f초를 %.0f배속으로)"
           % (SEQ_PATH, len(actors), FPS, dur,
              man["frames"][-1]["time_s"], SPEEDUP))
    unreal.log(msg)
    print(msg)


main()
