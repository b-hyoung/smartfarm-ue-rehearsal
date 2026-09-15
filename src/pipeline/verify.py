"""적대적 검증 — "그럴듯한데 틀린 것"을 찾는다. (목적 O6)

docs/OBJECTIVES.md §3 체크리스트를 자동 실행합니다.
각 항목은 **반증을 시도**하는 방식으로 씁니다. 통과가 목적이 아니라
틀린 곳을 드러내는 게 목적입니다.

    py -m src.pipeline.verify
"""
from __future__ import annotations

import csv
import math
import os
import sys

import numpy as np

# Windows 콘솔이 cp949 라 유니코드 대시 등에서 죽는다 → 출력 인코딩 고정
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRAME_DIR = os.path.join(REPO, "data", "frames")
TRACE_DIR = os.path.join(REPO, "data", "traces")

LX, LY, LZ = 8.0, 5.7, 2.7
CX = LX / 2.0
AC_XY = (4.0, 2.0)          # UE 좌표계 에어컨 중심
N_FRAMES = 15

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}")
    if detail:
        for line in detail.rstrip().split("\n"):
            print(f"       {line}")


def load(i):
    path = os.path.join(FRAME_DIR, "frame_%02d.csv" % i)
    a = np.genfromtxt(path, delimiter=",", names=True,
                      dtype=None, encoding="utf-8",
                      usecols=(0, 1, 2, 3, 4, 5, 6, 7))
    return a


# ─────────────────────────────────────────────────────────────
def v1_coords():
    a = load(14)
    x, y, z = a["x"], a["y"], a["z"]
    bb = (x.min(), x.max(), y.min(), y.max(), z.min(), z.max())
    ok = (abs(bb[0]) < 0.02 and abs(bb[1] - LX) < 0.02
          and abs(bb[2]) < 0.02 and abs(bb[3] - LY) < 0.02
          and abs(bb[4]) < 0.02 and abs(bb[5] - LZ) < 0.02)
    check("V1-a 바운딩박스가 방 치수와 일치",
          ok, "x %.3f~%.3f  y %.3f~%.3f  z %.3f~%.3f  (기대 0~8 / 0~5.7 / 0~2.7)" % bb)

    # 냉기 최저점이 에어컨 바로 아래인가 — 아니면 좌표가 뒤집힌 것
    T = a["T"]
    i = int(np.argmin(T))
    d = math.hypot(x[i] - AC_XY[0], y[i] - AC_XY[1])
    check("V1-b 최저온도 지점이 에어컨 아래",
          d < 0.9,
          "최저 T=%.2f K at (%.2f, %.2f, %.2f) — 에어컨(%.1f,%.1f)에서 %.2f m"
          % (T[i], x[i], y[i], z[i], AC_XY[0], AC_XY[1], d))

    # 좌우 대칭 (에어컨 x=4.0 기준). 높이 1.1m 근처 슬랩에서 비교
    m = np.abs(z - 1.1) < 0.06
    xs, ys, Ts = x[m], y[m], T[m]
    left = Ts[(xs < CX - 3.0)]
    right = Ts[(xs > CX + 3.0)]
    if len(left) > 20 and len(right) > 20:
        diff = abs(left.mean() - right.mean())
        check("V1-c 좌우 대칭",
              diff < 0.25,
              "좌측 평균 %.3f K, 우측 %.3f K, 차 %.3f K" % (left.mean(), right.mean(), diff))
    else:
        check("V1-c 좌우 대칭", False, "표본 부족")


def v2_temperature():
    a0 = load(0)
    T0 = a0["T"]
    check("V2-a frame_00 이 균일 (냉방 전)",
          T0.std() < 0.01,
          "평균 %.3f K, 표준편차 %.5f K" % (T0.mean(), T0.std()))

    # source 열이 simulated 인가 — mock 이 섞이면 안 됨
    with open(os.path.join(FRAME_DIR, "frame_07.csv"), encoding="utf-8") as f:
        r = next(csv.DictReader(f))
    check("V2-b source 가 simulated",
          r["source"] == "simulated", "source=%s" % r["source"])

    # 컬러맵 범위(19~27℃) 밖 비율 — 너무 크면 화면이 포화돼 거짓말이 됨
    a14 = load(14)
    tc = a14["T"] - 273.15
    below = float((tc < 19.0).mean()) * 100
    above = float((tc > 27.0).mean()) * 100
    check("V2-c 컬러맵 19~27℃ 가 frame_14 을 담는가",
          below + above < 12.0,
          "19℃ 미만 %.1f%%, 27℃ 초과 %.1f%% (합 %.1f%%)" % (below, above, below + above))


def v3_time():
    means, mins = [], []
    for i in range(N_FRAMES):
        T = load(i)["T"]
        means.append(float(T.mean()))
        mins.append(float(T.min()))
    d = np.diff(means)
    bad = int((d > 1e-6).sum())
    check("V3-a 방 평균 온도가 단조 감소",
          bad == 0,
          "상승한 구간 %d 개 / %d.  %.2f K → %.2f K"
          % (bad, len(d), means[0], means[-1]))
    check("V3-b 최저온도가 취출온도(289.5K) 아래로 안 내려감",
          min(mins) >= 289.4,
          "전 프레임 최저 %.2f K" % min(mins))
    return means


def v4_flow():
    a = load(14)
    x, y, z = a["x"], a["y"], a["z"]
    ux, uy, uz = a["Ux"], a["Uy"], a["Uz"]
    spd = np.sqrt(ux ** 2 + uy ** 2 + uz ** 2)

    i = int(np.argmax(spd))
    d = math.hypot(x[i] - AC_XY[0], y[i] - AC_XY[1])
    check("V4-a 최대 풍속이 취출구 근처",
          d < 1.0 and z[i] > LZ - 0.35,
          "|U|max %.3f m/s at (%.2f, %.2f, %.2f), 에어컨에서 %.2f m"
          % (spd[i], x[i], y[i], z[i], d))

    # 취출 슬롯 링(천장, 반경 0.3~0.6m)에서 아래로 향하는가
    r = np.hypot(x - AC_XY[0], y - AC_XY[1])
    ring = (z > LZ - 0.08) & (r > 0.3) & (r < 0.62)
    if ring.sum() > 10:
        frac_down = float((uz[ring] < 0).mean())
        check("V4-b 취출 슬롯에서 기류가 아래로",
              frac_down > 0.8,
              "슬롯 링 %d 점 중 아래 방향 %.0f%%, 평균 Uz %.3f m/s"
              % (ring.sum(), frac_down * 100, uz[ring].mean()))
    else:
        check("V4-b 취출 슬롯에서 기류가 아래로", False, "슬롯 표본 부족")

    # 궤적이 방 밖으로 안 나갔는가
    tp = os.path.join(TRACE_DIR, "trace_14.csv")
    if os.path.exists(tp):
        t = np.genfromtxt(tp, delimiter=",", names=True, encoding="utf-8")
        e = ((t["x"] - CX) / CX) ** 2 + (t["y"] / LY) ** 2
        out = int(((e > 1.02) | (t["z"] < -0.01) | (t["z"] > LZ + 0.01)).sum())
        check("V4-c 입자 궤적이 방을 벗어나지 않음",
              out == 0, "이탈 표본 %d / %d" % (out, len(t)))
    else:
        check("V4-c 입자 궤적이 방을 벗어나지 않음", False, "trace_14.csv 없음")


def v5_physics():
    """질량 보존: 취출로 들어온 유량 ≈ 리턴으로 나간 유량."""
    a = load(14)
    x, y, z, uz = a["x"], a["y"], a["z"], a["Uz"]
    top = np.abs(z - LZ) < 0.06
    r = np.hypot(x[top] - AC_XY[0], y[top] - AC_XY[1])
    w = uz[top]
    supply = w[(r > 0.3) & (r < 0.62)]        # 슬롯 (아래로, 음수)
    ret = w[r < 0.29]                          # 중앙 리턴 (위로, 양수)
    if len(supply) > 5 and len(ret) > 5:
        s, rr = supply.mean(), ret.mean()
        check("V5-a 취출은 아래(-), 리턴은 위(+)",
              s < 0 < rr,
              "취출 평균 Uz %.3f, 리턴 평균 Uz %.3f m/s" % (s, rr))
    else:
        check("V5-a 취출/리턴 방향", False,
              "표본 부족 (supply %d, return %d)" % (len(supply), len(ret)))



# ─────────────────────────────────────────────────────────────
# 원본 OpenFOAM probes 값 (postProcessing/probes, t=900s, 높이 1.1 m, °C)
# CFD 좌표 → UE 좌표는 x+4.0
PROBE_REF = {
    "A": (4.0, 2.0, 20.53),
    "B": (7.5, 0.8, 22.99),
    "C": (4.0, 4.5, 23.57),
    "D": (0.5, 0.8, 22.99),
}


def v7_against_source():
    """★ 가장 강한 검증 — 내보낸 CSV 가 원본 OpenFOAM 과 같은 값을 주는가.

    좌표 이동·단위 환산·프레임 선택 중 하나라도 틀리면 여기서 깨진다.
    앞의 V1~V5 는 전부 '내부 일관성'만 봤을 뿐, 원본과 맞는지는 안 봤다.
    """
    a = load(14)
    x, y, z, T = a["x"], a["y"], a["z"], a["T"]
    slab = np.abs(z - 1.1) < 0.06
    xs, ys, Ts = x[slab], y[slab], T[slab]

    worst = 0.0
    lines = []
    for name, (px, py, ref) in sorted(PROBE_REF.items()):
        d2 = (xs - px) ** 2 + (ys - py) ** 2
        k = int(np.argmin(d2))
        got = float(Ts[k]) - 273.15
        err = abs(got - ref)
        worst = max(worst, err)
        lines.append("%s (%.1f,%.1f)  원본 %.2f  →  내보낸값 %.2f  (오차 %.2f, %.2f m 이내 점)"
                     % (name, px, py, ref, got, err, math.sqrt(float(d2[k]))))
    check("V7 원본 OpenFOAM probes 와 일치 (종단 검증)",
          worst < 0.35, chr(10).join(lines) + chr(10) + "최대 오차 %.2f K" % worst)


def v5b_flux():
    """수평면 순 유량 ≈ 0 — 준정상 상태면 내려간 만큼 올라와야 한다."""
    a = load(14)
    z, uz = a["z"], a["Uz"]
    lines = []
    ok = True
    for zc in (2.4, 1.5, 0.6):
        m = np.abs(z - zc) < 0.06
        if m.sum() < 100:
            continue
        up = uz[m][uz[m] > 0].sum()
        dn = -uz[m][uz[m] < 0].sum()
        imb = abs(up - dn) / max(up, dn, 1e-9)
        ok &= imb < 0.12
        lines.append("z=%.1f m: 상승 %.1f, 하강 %.1f, 불균형 %.1f%% (%d 점)"
                     % (zc, up, dn, imb * 100, m.sum()))
    check("V5-b 수평면 순 유량 균형 (질량 보존)", ok, chr(10).join(lines))



# ─────────────────────────────────────────────────────────────
# 원본 system/topoSetDict 의 boxToFace 박스 (CFD 좌표, m)
TOPOSET_REF = {
    "inletXp": ([0.397, 1.675, 2.699], [0.457, 2.325, 2.701]),
    "inletXm": ([-0.457, 1.675, 2.699], [-0.397, 2.325, 2.701]),
    "inletYp": ([-0.325, 2.397, 2.699], [0.325, 2.457, 2.701]),
    "inletYm": ([-0.325, 1.543, 2.699], [0.325, 1.603, 2.701]),
    "return": ([-0.285, 1.715, 2.699], [0.285, 2.285, 2.701]),
}


def v8_ac_roundtrip():
    """UE 의 에어컨 액터 → 경계조건 재생성이 원본과 같은가.

    '에어컨을 옮기면 바람이 달라진다'를 하려면 이 변환이 정확해야 합니다.
    기본 위치에서 원본 topoSetDict 와 한 자리라도 다르면, 옮겼을 때
    엉뚱한 곳에 취출구가 생깁니다.
    """
    fp = os.path.join(REPO, "data", "ac_params.json")
    if not os.path.exists(fp):
        check("V8 에어컨 경계조건 왕복 일치", False,
              "ac_params.json 없음 — ue/sf_ac_params.py 를 먼저 실행")
        return
    import json
    d = json.load(open(fp, encoding="utf-8"))

    c = d["cfd_centre_m"]
    if abs(c[0]) > 1e-6 or abs(c[1] - 2.0) > 1e-6:
        check("V8 에어컨 경계조건 왕복 일치", False,
              "에어컨이 기본 위치가 아님 CFD(%.3f, %.3f) — 비교 불가" % (c[0], c[1]))
        return

    worst, lines = 0.0, []
    for name, (rmin, rmax) in sorted(TOPOSET_REF.items()):
        got = d["topoSet_boxes"].get(name)
        if got is None:
            lines.append("%s: 누락" % name)
            worst = 9.9
            continue
        e = max(max(abs(a - b) for a, b in zip(got["min"], rmin)),
                max(abs(a - b) for a, b in zip(got["max"], rmax)))
        worst = max(worst, e)
        lines.append("%-8s 최대 오차 %.4f m" % (name, e))
    check("V8 에어컨 경계조건 왕복 일치 (topoSetDict 대조)",
          worst < 1e-3, chr(10).join(lines) + chr(10) + "전체 최대 %.4f m" % worst)


def v9_power_model():
    """전력 모델이 명판 3점을 재현하는가."""
    fp = os.path.join(REPO, "data", "ac_params.json")
    if not os.path.exists(fp):
        check("V9 전력 모델", False, "ac_params.json 없음")
        return
    import json
    d = json.load(open(fp, encoding="utf-8"))
    spec = d["spec"]
    curve = d["power"]["curve_W"]
    lines, ok = [], True
    for k in ("min", "mid", "rated"):
        ref = spec["power_W"][k]
        got = curve[k]
        ok &= abs(got - ref) < 1.0
        cop = spec["cooling_W"][k] / ref
        lines.append("%-6s 냉방 %5d W → 전력 %6.1f W (명판 %d, COP %.2f)"
                     % (k, spec["cooling_W"][k], got, ref, cop))
    check("V9 전력 모델이 명판 3점을 재현", ok, chr(10).join(lines))


def v6_limits():
    """한계 명시 — 통과/실패가 아니라 '기록되었는가'를 본다."""
    doc = os.path.join(REPO, "docs", "OBJECTIVES.md")
    txt = open(doc, encoding="utf-8").read() if os.path.exists(doc) else ""
    for key, label in [("재배단이 CFD 에 없다", "V6-a 재배단 미반영 명시"),
                       ("벽 온도 29", "V6-b 벽 온도 가정 명시"),
                       ("수직 아래", "V6-c 취출 방향 오류 명시")]:
        check(label, key in txt, "OBJECTIVES.md 에 기록됨" if key in txt else "미기록")


def main():
    print("=" * 62)
    print(" 적대적 검증 — CFD → UE 파이프라인")
    print("=" * 62)
    v1_coords()
    v2_temperature()
    v3_time()
    v4_flow()
    v5_physics()
    v5b_flux()
    v7_against_source()
    v8_ac_roundtrip()
    v9_power_model()
    v6_limits()

    n = len(RESULTS)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    print("=" * 62)
    print(f" 결과: {p}/{n} 통과")
    fails = [r for r in RESULTS if not r[1]]
    if fails:
        print(" 실패 항목:")
        for name, _, detail in fails:
            print(f"   · {name} — {detail.splitlines()[0] if detail else ''}")
    print("=" * 62)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
