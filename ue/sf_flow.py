"""SF_Rehearsal: CFD 속도장을 따라 이류시킨 입자 궤적을 그린다. (목적 O5-A)

data/traces/trace_XX.csv 를 읽어 입자 경로를 폴리라인으로 그립니다.
색 = 속력 (파랑 느림 → 노랑 빠름).

궤적 계산은 src/pipeline/make_traces.py 에서 이미 끝냈습니다 — UE 는 그리기만 합니다.
(UE 파이썬엔 numpy 가 없고 8만 점 적분은 에디터를 멈춥니다.)

환경변수
    SF_FRAME    프레임 번호 (기본 14)
    SF_TAIL     꼬리 길이(스텝). 0 이면 전체 경로 (기본 0)
    SF_HEAD     꼬리 끝 스텝. SF_TAIL 과 함께 쓰면 애니메이션 구간
    SF_NPART    그릴 입자 수 (기본 160)

    py ue/ue_exec.py -c "import os;os.environ['SF_FRAME']='14';exec(open(r'...\\sf_flow.py',encoding='utf-8').read())"
"""
import csv
import os
import unreal

REPO = r"C:\Users\hunvr\Desktop\bobs_projects\smartfarm-ue-rehearsal"
TRACE_DIR = os.path.join(REPO, "data", "traces")

S = 100.0                 # m -> cm
DUR = 1.0e6
SPD_MIN, SPD_MAX = 0.0, 1.6      # ★ 전 프레임 고정 색범위
THICK = 1.4


def speed_color(v):
    """속력 -> 색. 어두운 파랑 → 청록 → 노랑 (viridis 근사)."""
    f = (v - SPD_MIN) / (SPD_MAX - SPD_MIN)
    f = 0.0 if f < 0.0 else (1.0 if f > 1.0 else f)
    stops = [(0.27, 0.00, 0.33), (0.19, 0.41, 0.56),
             (0.13, 0.66, 0.51), (0.99, 0.91, 0.14)]
    seg = f * (len(stops) - 1)
    i = min(int(seg), len(stops) - 2)
    t = seg - i
    a, b = stops[i], stops[i + 1]
    return unreal.LinearColor(a[0] + (b[0] - a[0]) * t,
                              a[1] + (b[1] - a[1]) * t,
                              a[2] + (b[2] - a[2]) * t, 1.0)


def main():
    frame = int(os.environ.get("SF_FRAME", "14"))
    tail = int(os.environ.get("SF_TAIL", "0"))
    head = os.environ.get("SF_HEAD")
    npart = int(os.environ.get("SF_NPART", "160"))

    path = os.path.join(TRACE_DIR, "trace_%02d.csv" % frame)
    if not os.path.exists(path):
        print("SF_FLOW: no trace for frame %d" % frame)
        return

    tracks = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pid = int(r["pid"])
            tracks.setdefault(pid, []).append(
                (int(r["step"]), float(r["x"]), float(r["y"]),
                 float(r["z"]), float(r["speed"])))
    if not tracks:
        print("SF_FLOW: frame %d has no motion (냉방 시작 전)" % frame)
        return

    pids = sorted(tracks)
    stride = max(1, len(pids) // npart)
    pids = pids[::stride]

    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.flush_persistent_debug_lines(w)

    hi = int(head) if head is not None else None
    segs = 0
    for pid in pids:
        pts = sorted(tracks[pid])
        if hi is not None:
            lo = max(0, hi - tail) if tail > 0 else 0
            pts = [p for p in pts if lo <= p[0] <= hi]
        elif tail > 0:
            pts = pts[-tail:]
        for j in range(len(pts) - 1):
            _, x0, y0, z0, s0 = pts[j]
            _, x1, y1, z1, _ = pts[j + 1]
            unreal.SystemLibrary.draw_debug_line(
                w, unreal.Vector(x0 * S, y0 * S, z0 * S),
                unreal.Vector(x1 * S, y1 * S, z1 * S),
                speed_color(s0), DUR, THICK)
            segs += 1

    try:
        unreal.get_editor_subsystem(
            unreal.LevelEditorSubsystem).editor_invalidate_viewports()
    except Exception:
        pass

    msg = ("SF_FLOW: frame_%02d  %d particles, %d segments (stride=%d)"
           % (frame, len(pids), segs, stride))
    unreal.log(msg)
    print(msg)


main()
