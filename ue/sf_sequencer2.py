"""SF_Structure 용 온도변화 시퀀스 - 커튼(바람) + 1.1m 온도카펫 + A~D 마커.

표현 설계 ("바람을 통해 온도 변화를 어떻게 표현하나"):
    * 커튼 색 = 그 지점 공기 온도. 시간이 지나면 취출~끝자락 그라디언트가
      통째로 파래진다 (방이 식어 제트가 덜 데워짐) - 바람이 온도 변화를 말한다.
    * 방 공기 자체는 1.1 m 반투명 온도 카펫 - t=0 빨강 → t=900 파랑.
    * A/B/C/D 마커는 그 시각 실측(프로브) 온도색.
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

import sf_config as CFG  # noqa: E402
import sf_geom as G  # noqa: E402
importlib.reload(G)

S = 100.0
# 배속*fps 는 data/_seq.json 으로 바꿀 수 있다: {"speedup": 10, "fps": 10}
#   ★ fps == speedup 이면 "표시 프레임 번호 = 실제 경과 초" 가 유지된다
#     (30x/30fps → 32초, 10x/10fps → 90초)
_cfg = {}
_cfg_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "_seq.json")
if os.path.isfile(_cfg_p):
    _cfg = json.load(open(_cfg_p, encoding="utf-8"))
FPS = int(_cfg.get("fps", 30))
SPEEDUP = float(_cfg.get("speedup", 30.0))
REBUILD_ACTORS = bool(_cfg.get("rebuild_actors", True))
# mesh=False 면 CSV 기반 표시(커튼*카펫*마커)를 시퀀스에서 빼고 VDB 볼륨만 몬다
SHOW_MESH = bool(_cfg.get("mesh", True))
SEQ_DIR = CFG.SEQ_DIR
SEQ_NAME = "SEQ_SF_Flow" if int(SPEEDUP) == 30 else "SEQ_SF_Flow_%dx" % int(SPEEDUP)
SEQ_PATH = "%s/%s" % (SEQ_DIR, SEQ_NAME)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
at = unreal.AssetToolsHelpers.get_asset_tools()


def load_jet_grid(frame):
    path = os.path.join(REPO, "data", "jets", "jet_%02d.csv" % frame)
    sheets = {}
    kmax = smax = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k, st = int(r["k"]), int(r["step"])
            sheets.setdefault(r["dir"], {})[(k, st)] = (
                float(r["x"]) * S, float(r["y"]) * S,
                min(float(r["z"]) * S, 268.0), float(r["T"]))
            kmax, smax = max(kmax, k + 1), max(smax, st + 1)
    return sheets, kmax, smax


def build_jets(frame, frame_next):
    """커튼 4장 - 정점색=현재 온도, UV1/UV2=다음 프레임 색, UV2.y/UV3=위치 델타.

    "이미지가 바뀐다" 지적의 해법: 다음 프레임 데이터를 정점에 같이 실어서
    머티리얼이 BlendU(시퀀서 구동)로 색은 번지고 형태는 모핑하게 한다.
    """
    cur, kmax, smax = load_jet_grid(frame)
    nxt, _, _ = load_jet_grid(frame_next)
    verts, tris, norms = [], [], []
    uv0, uv1, uv2, uv3, cols = [], [], [], [], []
    up = unreal.Vector(0.0, 0.0, 1.0)
    for d in sorted(cur):
        base = len(verts)
        for k in range(kmax):
            for st in range(smax):
                x, y, z, T = cur[d][(k, st)]
                xn, yn, zn, Tn = nxt[d][(k, st)]
                verts.append(unreal.Vector(x, y, z))
                norms.append(up)
                # 커튼은 연속 그라디언트 - 곡면 위 0.5K 띠는 주름처럼 보인다
                c = G.temp_color(T)
                cn = G.temp_color(Tn)
                cols.append(c)
                uv0.append(unreal.Vector2D(st / (smax - 1.0), k / (kmax - 1.0)))
                uv1.append(unreal.Vector2D(cn.r, cn.g))
                uv2.append(unreal.Vector2D(cn.b, xn - x))
                uv3.append(unreal.Vector2D(yn - y, zn - z))
        for k in range(kmax - 1):
            for st in range(smax - 1):
                a = base + k * smax + st
                b = a + smax
                tris += [a, a + 1, b,   a + 1, b + 1, b]
                tris += [a, b, a + 1,   a + 1, b, b + 1]
    return verts, tris, norms, uv0, uv1, uv2, uv3, cols


def build_slice_blend(frame, frame_next):
    """온도 카펫 - 현재 프레임 메시에 다음 프레임 색을 UV1/UV2 로 싣는다.

    카펫 격자는 프레임과 무관하게 동일하므로 정점 순서가 1:1 대응한다.
    """
    v, t, n, u, c = G.build_slice(G.load_slice(REPO, frame))
    _, _, _, _, cn = G.build_slice(G.load_slice(REPO, frame_next))
    uv1 = [unreal.Vector2D(x.r, x.g) for x in cn]
    uv2 = [unreal.Vector2D(x.b, 0.0) for x in cn]
    return v, t, n, u, uv1, uv2, c


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

    # 액터 15개가 이미 있으면(다른 배속 시퀀스만 추가할 때) 재빌드 생략 가능
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors()
                if a.get_actor_label().startswith("SF_Anim2_")}
    if not REBUILD_ACTORS and len(existing) == 15:
        txts = {a.get_actor_label(): a for a in eas.get_all_level_actors()
                if a.get_actor_label().startswith("SF_PwrTxt_")}
        actors = [(f, existing["SF_Anim2_%02d" % f],
                   txts.get("SF_PwrTxt_%02d" % f)) for f in range(15)]
        print("SF_SEQ2: 기존 액터 15개 재사용")
        build_sequence_only(actors, times)
        return

    power = {}
    pw_p = os.path.join(REPO, "data", "power.json")
    if os.path.isfile(pw_p):
        power = json.load(open(pw_p, encoding="utf-8"))

    actors = []
    for f in range(15):
        fn = min(f + 1, 14)
        label = "SF_Anim2_%02d" % f
        for a in list(eas.get_all_level_actors()):
            if a.get_actor_label() == label:
                eas.destroy_actor(a)
        actor, pmc = G.get_proc_actor(label, "Anim2Mesh_%02d" % f)
        pmc.clear_all_mesh_sections()

        # 0=커튼: 색+형태를 다음 프레임으로 보간(모핑) + 흐름 파도
        jv, jt, jn, ju0, ju1, ju2, ju3, jc = build_jets(f, fn)
        pmc.create_mesh_section_linear_color(
            0, jv, jt, jn, ju0, ju1, ju2, ju3, jc, [_t] * len(jv), False)
        pmc.set_material(0, G.curtain_flow_blend_material())

        # 1=온도카펫: 색을 다음 프레임으로 보간
        sv, st_, sn, su0, su1, su2, sc = build_slice_blend(f, fn)
        pmc.create_mesh_section_linear_color(
            1, sv, st_, sn, su0, su1, su2, [], sc, [_t] * len(sv), False)
        pmc.set_material(1, G.slice_blend_material())

        # 2=마커 (작아서 보간 없이 교체)
        mv, mt, mn, mu, mc = G.build_markers(
            G.probe_points_at(series, times[f]), r_sphere=11.0, r_bar=6.5)
        if mv:
            pmc.create_mesh_section_linear_color(
                2, mv, mt, mn, mu, [], [], [], mc, [_t] * len(mv), False)
            pmc.set_material(2, mat_vc)

        actor.set_actor_hidden_in_game(True)
        actor.set_is_temporarily_hidden_in_editor(True)

        # 프레임별 전력 텍스트 - 재생 중 실시간 변화 (시퀀서가 가시성 토글)
        txt = None
        if power.get("t"):
            cool = power["cool_W"][f] / 1000.0
            led = power.get("light_W", 0.0) / 1000.0
            tl = "SF_PwrTxt_%02d" % f
            for a in list(eas.get_all_level_actors()):
                if a.get_actor_label() == tl:
                    eas.destroy_actor(a)
            # 평벽(-y) 바깥 위 - 방 안 어디서도 가려지지 않는 자리
            txt = eas.spawn_actor_from_class(
                unreal.TextRenderActor, unreal.Vector(400, -40, 300),
                unreal.Rotator(0, 0, -90))
            txt.set_actor_label(tl)
            txt.set_folder_path("SF/Power")
            tc = txt.get_editor_property("text_render")
            tc.set_editor_property("world_size", 34.0)
            tc.set_editor_property("horizontal_alignment",
                                   unreal.HorizTextAligment.EHTA_CENTER)
            tc.set_text("t=%ds   AC %.2f kW  LED %.2f kW   TOTAL %.2f kW"
                        % (int(times[f]), cool, led, cool + led))
            txt.set_actor_hidden_in_game(True)
            txt.set_is_temporarily_hidden_in_editor(True)

        actors.append((f, actor, txt))
        print("SF_SEQ2: %s  커튼정점 %d" % (label, len(jv)))

    if power.get("t"):
        _ensure_power_text_light()
    build_sequence_only(actors, times)


def _ensure_power_text_light():
    """전력 텍스트 조명 - 기본 텍스트 머티리얼은 lit 이라 어두운 씬에선 안 보인다.

    (재배등 감쇠반경 320 밖은 완전 암흑 → 흰 글자가 검정 위 검정으로 렌더.
     SceneCapture 검증으로 확인.) 텍스트 전용 포인트라이트를 앞에 하나 둔다.
    """
    label = "SF_PwrTxtLight"
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            return
    l = eas.spawn_actor_from_class(unreal.PointLight,
                                   unreal.Vector(400, -200, 300),
                                   unreal.Rotator())
    l.set_actor_label(label)
    l.set_folder_path("SF/Power")
    c = l.get_editor_property("point_light_component")
    c.set_intensity(5000.0)
    c.set_editor_property("attenuation_radius", 400.0)
    c.set_editor_property("cast_shadows", False)


def build_sequence_only(actors, times):
    # ── 시퀀스 ─────────────────────────────────────────────
    if unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH):
        unreal.EditorAssetLibrary.delete_asset(SEQ_PATH)
    if not unreal.EditorAssetLibrary.does_directory_exist(SEQ_DIR):
        unreal.EditorAssetLibrary.make_directory(SEQ_DIR)
    seq = at.create_asset(SEQ_NAME, SEQ_DIR, unreal.LevelSequence,
                          unreal.LevelSequenceFactoryNew())
    end_s = max(times.values())
    win = []
    for i, entry in enumerate(actors):
        f, actor = entry[0], entry[1]
        txt = entry[2] if len(entry) > 2 else None
        t0 = times[f]
        t1 = times[actors[i + 1][0]] if i + 1 < len(actors) \
            else end_s + (end_s - times[actors[i - 1][0]])
        a_ = int(round(t0 / SPEEDUP * FPS))
        b_ = max(int(round(t1 / SPEEDUP * FPS)), a_ + 1)
        win.append((actor, a_, b_))
        if txt is not None:                 # 전력 텍스트도 같은 창으로 토글
            win.append((txt, a_, b_))
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(win[-1][2])
    if SHOW_MESH:
        for actor, a, b in win:
            binding = seq.add_possessable(actor)
            track = binding.add_track(unreal.MovieSceneVisibilityTrack)
            section = track.add_section()
            section.set_range(a, b)
            for ch in section.get_channels_by_type(
                    unreal.MovieSceneScriptingBoolChannel):
                ch.set_default(True)
                ch.add_key(unreal.FrameNumber(a), True)
    else:
        print("SF_SEQ2: mesh=False - CSV 표시(커튼*카펫) 제외, 볼륨만")

    # ── VDB 볼륨(SF_Volume) Frame 트랙 - 시퀀서가 볼륨 프레임을 직접 몬다 ──
    #    (컴포넌트 자체 재생은 시퀀서*스크럽과 안 맞아서 "안 움직인다" 문제의 원인)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "SF_Volume":
            comp = a.get_components_by_class(unreal.HeterogeneousVolumeComponent)
            if comp:
                comp = comp[0]
                try:
                    comp.set_editor_property("playing", False)
                except Exception:
                    pass
                vb = seq.add_possessable(comp)
                vt = vb.add_track(unreal.MovieSceneFloatTrack)
                vt.set_property_name_and_path("Frame", "Frame")
                vs_ = vt.add_section()
                vs_.set_range(0, win[-1][2])
                for ch in vs_.get_channels_by_type(
                        unreal.MovieSceneScriptingFloatChannel):
                    for i, (_a2, a2, _b2) in enumerate(win):
                        ch.add_key(unreal.FrameNumber(a2), float(i))
                print("SF_SEQ2: SF_Volume Frame 트랙 추가 (0~14)")
            break

    # BlendU 톱니파 - 각 표시창에서 0→1 로 올라가며 다음 프레임으로 보간/모핑
    # ⚠ add_scalar_parameter_key 의 FrameNumber 는 표시 프레임이 아니라
    #   **틱 해상도**(기본 24000/s) 단위다. 표시 프레임 그대로 넣으면 키가
    #   재생 0.005초 안에 몰려서 BlendU 가 항상 1 - "보간이 안 된다" 사고.
    if not SHOW_MESH:
        unreal.EditorAssetLibrary.save_asset(SEQ_PATH)
        _place_player(seq)
        les.save_current_level()
        print("SF_SEQ2: %s * %dfps * 볼륨 전용 * PIE 자동재생" % (SEQ_PATH, FPS))
        return
    tick = seq.get_tick_resolution()
    scale = int(round(tick.numerator / float(tick.denominator) / FPS))
    mpc = G.blend_mpc()
    mtrack = seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack)
    mtrack.set_editor_property("mpc", mpc)
    msec = mtrack.add_section()
    msec.set_range(0, win[-1][2])
    for _actor, a, b in win:
        msec.add_scalar_parameter_key("BlendU", unreal.FrameNumber(a * scale), 0.0)
        msec.add_scalar_parameter_key("BlendU",
                                      unreal.FrameNumber((b - 1) * scale), 1.0)
    unreal.EditorAssetLibrary.save_asset(SEQ_PATH)
    _place_player(seq)
    les.save_current_level()
    print("SF_SEQ2: %s * %dfps * 길이 %.1f초 (실제 900초, %.0f배속) * PIE 자동재생"
          % (SEQ_PATH, FPS, win[-1][2] / float(FPS), SPEEDUP))


def _place_player(seq):
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


main()
