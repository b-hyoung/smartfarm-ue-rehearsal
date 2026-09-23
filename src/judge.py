"""판정면 표본에서 케이스 성적을 낸다 — 시간평균한 장에서 분위수로.

    py -m src.judge --runs ~/smartfarm-cfd/cases/fan-study
    py -m src.judge --runs ... --average-from 450    평균 구간을 바꾼다
    py -m src.judge --runs ... --last-only           옛 방식(마지막 한 장)
    py -m src.judge --runs ... --band 0.25 1.2       다른 작물 기준으로 다시 채점

왜 시간평균인가
    마지막 시각 한 장으로 판정하면 안 된다. 부력이 섞인 실내 흐름은 자리를 잡은
    뒤에도 계속 출렁이므로, 어느 한 순간을 찍으면 그때 우연히 죽어 있던 자리가
    잡힌다. 우리 5 번 케이스에서 재 보니 마지막 한 장과 300~600 초 평균의
    P10 차이가 4.7 ~ 12.6 % 였다. 같은 구간에서 물리 시간을 300 초에서 600 초로
    늘렸을 때의 차이는 0.4 % 다. 곧 스냅샷 잡음이 물리 시간 부족보다 25 배 크다.
    더 오래 돌려도 답이 안 나오고, 평균을 내면 해결된다.

    P50 / P90 / 평균은 0.1 ~ 0.5 % 밖에 안 움직이는데 P10 만 10 % 넘게 움직인다.
    밑바닥 자리가 잠깐씩 죽었다 살아나기 때문이다. 하필 P10 이 1 순위 지표다.

    문헌이 이 방식을 명시한다. Blocken(2015) Building and Environment 91:219-245
    5.6 절 - "solutions at different stages ... should be stored and averaged to
    yield the final averaged solution". Ramponi & Blocken(2012) 53:34-48 은 PIV
    실측과 대조해 "accurate results could only be obtained by averaging the CFD
    results over at least a period of oscillatory behavior" 라고 적었다.
    농업 시설에서는 Janke 외(2020) Comput. Electron. Agric. 175:105546 이 발달
    구간과 평균 구간을 따로 유도하고 구간을 옮겨 재평균해 검증했다. 그 처방을
    우리 캐노피 판정면에 넣으면 평균 구간 284 초가 나온다 - 기본값 300 초는
    거기서 왔다. docs/FAN-CFD-TRANSIENT-REFERENCES.md 참고.

    평균은 점마다 |U| 를 시각에 걸쳐 평균한 장을 만들고 그 장의 분위수를 낸다
    (필드를 먼저 평균하고 통계를 낸다). 모든 시각의 점을 한 데 모아 분위수를 내는
    것은 "어느 자리가 얼마나 자주 정체하는가"라는 다른 질문이므로 섞지 않는다.

    30 초 간격 표본이라 참 시간평균은 아니다. 다음 재실행부터는 OpenFOAM 의
    fieldAverage 로 UMean 을 만들어 찍는 것이 낫다.

왜 분위수인가
    "적정구간 비율"(0.3~1.0 m/s 인 점의 비율)은 점마다 0 또는 1 로 세므로,
    값이 합격선 근처에 몰리면 격자를 조금만 바꿔도 무더기로 선을 넘나들어 크게
    튄다. 그러면 격자 수렴(GCI)도 낼 수 없다. 분위수는 개수가 아니라 값이라
    부드럽게 변하고, 덤으로 어디가 나쁜지를 알려준다.

        P10  밑에서 10 % 자리 - "제일 안 통하는 구석이 얼마인가"
        P50  한가운데
        P90  위에서 10 %    - "너무 센 데는 없는가"

    작물은 평균으로 자라지 않는다. 제일 바람 안 통하는 자리부터 상한다.
    그래서 1 순위를 P10 으로 둔다. 최솟값을 쓰지 않는 이유는 점 하나짜리라
    벽에 붙은 한 점이나 계산이 튄 한 점에 판단이 휘둘리기 때문이다.

사후 검증
    평균 구간의 뒷절반만으로 다시 평균해 P10 이 얼마나 움직이는지 같이 낸다.
    Janke 외(2020)가 [1,6] 대 [2,7] 로 한 검증이고 비용은 0 이다. 이 값이 크면
    평균 구간이 아직 모자란 것이다.

무엇을 읽는가
    controlDict 의 canopy 함수오브젝트가 남긴
        postProcessing/canopy/<시각>/U_<면이름>.raw   (x y z Ux Uy Uz)
        postProcessing/canopy/<시각>/T_<면이름>.raw   (x y z T)
    온도는 순위에 쓰지 않고 표에만 남긴다 - 지금 열원이 조명 없이 에어컨뿐이라
    온도로 판정할 근거가 없다. 조명이 들어오면 같은 파일로 지표를 붙이면 된다.

    CDF 를 --cdf 로 저장해 두면 합격선이 바뀌어도(작물이 바뀌어도) 계산을
    다시 돌리지 않고 다시 채점할 수 있다.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

# 윈도우 콘솔이 cp949 라 한글 대시 같은 글자에서 죽는다.
# 배치 스크립트 안에서 돌 때 이것 때문에 통째로 실패한 적이 있다.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAND = (0.3, 1.0)          # 적정 구간 - Kitaya 2003 하한, Zhang & Kacira 2016 상한
STAGNANT = 0.1             # 정체로 보는 선
AVG_FROM = 300.0           # 이 시각부터 평균한다 (Janke 외 2020 환산 284 초)


def quantile(sorted_vals, pct):
    """정렬된 값에서 pct 분위수. 선형 보간."""
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * pct / 100.0
    lo = int(math.floor(k))
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def read_points(path, ncol, crop=None):
    """raw 표본 -> {(x,y,z): 값}. 좌표로 묶어야 시각끼리 점을 맞출 수 있다.

    crop = (x0, x1, y0, y1) 이면 그 사각형 밖의 점을 버린다.

    이게 왜 필요한가. controlDict 의 `surfaces` 는 평면 하나를 정의할 뿐이라
    OpenFOAM 이 그 평면이 격자를 가르는 **전체**를 찍는다. 곧 재배 베드 위만이
    아니라 방 전체 단면(x -4~4, y 0~5.7)이 들어온다. 실제로 5,124 점 가운데
    베드 안은 855 점, **16.7 %** 뿐이었다. 거르지 않으면 P10 이 상추가 없는
    방 구석을 읽는다. 05 번에서 방 전체 P10 은 0.071 인데 베드만 보면 0.330 이다.

    데이터 자체는 그대로 둔다. 방 전체를 찍어두면 바람이 어디로 새는지 나중에
    볼 수 있고 용량도 작다. 좁히는 것은 채점할 때 한다.
    """
    out = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.split()
        if len(f) < 3 + ncol:
            continue
        try:
            x, y, z = float(f[0]), float(f[1]), float(f[2])
            vals = [float(v) for v in f[3:3 + ncol]]
        except ValueError:
            continue
        if crop and not (crop[0] <= x <= crop[1] and crop[2] <= y <= crop[3]):
            continue
        out[(round(x, 4), round(y, 4), round(z, 4))] = (
            math.sqrt(sum(v * v for v in vals)) if ncol == 3 else vals[0])
    return out


def judge_crops(params_path):
    """fan_params.json 의 judge_planes -> {면 이름: (x0, x1, y0, y1)}."""
    try:
        spec = json.load(open(params_path, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for pl in spec.get("judge_planes") or []:
        xr, yr = pl.get("x_range_cfd_m"), pl.get("y_range_m")
        if xr and yr:
            out[pl["name"]] = (xr[0], xr[1], yr[0], yr[1])
    return out


def snapshot_times(run):
    """postProcessing/canopy 아래 시각 목록 (오름차순)."""
    base = os.path.join(run, "postProcessing", "canopy")
    if not os.path.isdir(base):
        return []
    ts = []
    for d in os.listdir(base):
        try:
            ts.append((float(d), os.path.join(base, d)))
        except ValueError:
            continue
    return sorted(ts)


def mean_field(dirs, fname, ncol, crop=None):
    """여러 시각의 같은 면을 점마다 평균한 장. 모든 시각에 있는 점만 쓴다."""
    fields = []
    for _, d in dirs:
        p = os.path.join(d, fname)
        if os.path.exists(p):
            f = read_points(p, ncol, crop)
            if f:
                fields.append(f)
    if not fields:
        return None
    keys = set(fields[0])
    for f in fields[1:]:
        keys &= set(f)
    if not keys:
        return None
    n = len(fields)
    return [sum(f[k] for f in fields) / n for k in sorted(keys)], n


def plane_stats(dirs, name, band, crop=None, want_cdf=False):
    """면 하나의 성적. 없으면 None."""
    got = mean_field(dirs, "U_%s.raw" % name, 3, crop)
    if got is None:
        return None
    mags, nsnap = got
    mags = sorted(mags)
    n = len(mags)
    mean = sum(mags) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in mags) / n)
    lo, hi = band

    s = {
        "n": n,
        "snapshots": nsnap,
        "P10": round(quantile(mags, 10), 4),
        "P50": round(quantile(mags, 50), 4),
        "P90": round(quantile(mags, 90), 4),
        "mean": round(mean, 4),
        "cov": round(sd / mean, 4) if mean else float("nan"),
        # 옛 지표 - 순위에는 쓰지 않고 대조용으로만 남긴다
        "band_ratio": round(sum(1 for v in mags if lo <= v <= hi) / n, 4),
        "stagnant_ratio": round(sum(1 for v in mags if v < STAGNANT) / n, 4),
    }
    s["spread"] = round(s["P90"] / s["P10"], 3) if s["P10"] > 1e-9 else float("inf")

    # 사후 검증 - 평균 구간의 뒷절반으로 다시 평균해 P10 이 얼마나 움직이나
    if len(dirs) >= 4:
        half = mean_field(dirs[len(dirs) // 2:], "U_%s.raw" % name, 3, crop)
        if half and s["P10"] > 1e-9:
            p10h = quantile(sorted(half[0]), 10)
            s["P10_recheck"] = round(p10h, 4)
            s["P10_drift_pct"] = round((p10h - s["P10"]) / s["P10"] * 100, 1)

    got_t = mean_field(dirs, "T_%s.raw" % name, 1, crop)
    if got_t:
        ts = got_t[0]
        tm = sum(ts) / len(ts)
        s["T_mean_C"] = round(tm - 273.15, 2)
        s["T_sd"] = round(math.sqrt(sum((v - tm) ** 2 for v in ts) / len(ts)), 3)

    if want_cdf:
        # 합격선을 나중에 바꿔도 다시 채점할 수 있게 100 점으로 남긴다
        s["cdf"] = [[round(quantile(mags, q), 4), q] for q in range(0, 101)]
    return s


def judge_run(run, band, avg_from, last_only, crops=None, want_cdf=False):
    ts = snapshot_times(run)
    if not ts:
        return None
    dirs = ts[-1:] if last_only else ([x for x in ts if x[0] >= avg_from] or ts[-1:])

    names = sorted({os.path.basename(f)[2:-4]
                    for f in glob.glob(os.path.join(dirs[-1][1], "U_*.raw"))})
    planes = {}
    for nm in names:
        st = plane_stats(dirs, nm, band, (crops or {}).get(nm), want_cdf)
        if st:
            planes[nm] = st
    if not planes:
        return None

    worst = min(p["P10"] for p in planes.values())
    hottest = max(p["P90"] for p in planes.values())
    means = [p["mean"] for p in planes.values()]
    drifts = [abs(p["P10_drift_pct"]) for p in planes.values() if "P10_drift_pct" in p]
    return {
        "run_id": os.path.basename(os.path.normpath(run)),
        "window_s": [dirs[0][0], dirs[-1][0]],
        "snapshots": len(dirs),
        "mode": "last" if last_only else "time-average",
        "planes": planes,
        # 케이스 성적 - 네 면 가운데 가장 나쁜 쪽으로 대표한다
        "P10_worst": round(worst, 4),
        "P90_max": round(hottest, 4),
        "tier_gap": round(max(means) - min(means), 4),
        "P10_drift_max_pct": max(drifts) if drifts else None,
        "pass_low": worst >= band[0],
        "pass_high": hottest <= band[1],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="케이스 폴더들이 든 상위 폴더")
    ap.add_argument("--band", nargs=2, type=float, default=list(BAND),
                    metavar=("LO", "HI"), help="적정 구간 (m/s). 작물이 바뀌면 여기만 바꾼다")
    ap.add_argument("--average-from", type=float, default=AVG_FROM,
                    help="이 시각(s)부터 시간평균한다. 기본 %d" % AVG_FROM)
    ap.add_argument("--last-only", action="store_true",
                    help="옛 방식 - 마지막 한 장만 읽는다. 대조용")
    ap.add_argument("--params", default=os.path.join(REPO, "data", "fan_params.json"),
                    help="judge_planes 범위를 읽을 파일")
    ap.add_argument("--no-crop", action="store_true",
                    help="베드 범위로 자르지 않고 방 전체 단면을 채점한다. 대조용")
    ap.add_argument("--cdf", action="store_true", help="CDF 까지 JSON 에 남긴다")
    ap.add_argument("--out", default=None, help="JSON 저장 경로")
    a = ap.parse_args()
    band = (a.band[0], a.band[1])

    runs = sorted(d for d in glob.glob(os.path.join(a.runs, "*")) if os.path.isdir(d))
    crops = {} if a.no_crop else judge_crops(a.params)
    rows = [r for r in (judge_run(d, band, a.average_from, a.last_only, crops, a.cdf)
                        for d in runs) if r]
    if not rows:
        print("판정면 표본을 찾지 못했다. 아직 돌리지 않았거나 canopy 함수오브젝트가 "
              "controlDict 에 없다.")
        print("  찾은 폴더 %d 개: %s" % (len(runs), a.runs))
        return 1

    # 1 순위 P10(높을수록), 2 순위 층간 차이(작을수록)
    rows.sort(key=lambda r: (-r["P10_worst"], r["tier_gap"]))

    head = ("마지막 한 장 (옛 방식)" if a.last_only
            else "시간평균 %.0f 초부터" % a.average_from)
    head += " · " + ("방 전체 단면" if a.no_crop else "재배 베드 위만")
    print("적정 구간 %.2f ~ %.2f m/s · 케이스 %d 개 · %s · 1 순위 P10"
          % (band[0], band[1], len(rows), head))
    print()
    print("  %-14s %7s %7s %7s %7s %8s %7s %6s  %s"
          % ("케이스", "P10", "P50", "P90", "층간차", "옛비율", "온도C", "표류%", "판정"))
    for r in rows:
        p = list(r["planes"].values())
        p50 = sum(x["P50"] for x in p) / len(p)
        ratio = sum(x["band_ratio"] for x in p) / len(p)
        temps = [x["T_mean_C"] for x in p if "T_mean_C" in x]
        tstr = "%7.1f" % (sum(temps) / len(temps)) if temps else "      -"
        dr = r.get("P10_drift_max_pct")
        dstr = "%6.1f" % dr if dr is not None else "     -"
        mark = "통과" if (r["pass_low"] and r["pass_high"]) else (
            "하한미달" if not r["pass_low"] else "상한초과")
        print("  %-14s %7.3f %7.3f %7.3f %7.3f %7.1f%% %s %s  %s"
              % (r["run_id"], r["P10_worst"], p50, r["P90_max"],
                 r["tier_gap"], ratio * 100, tstr, dstr, mark))

    w = rows[0]
    print()
    print("  구간 %.0f~%.0f 초, 스냅샷 %d 장을 점마다 평균한 장에서 분위수를 냈다."
          % (w["window_s"][0], w["window_s"][1], w["snapshots"]))
    print("  P10 = 밑에서 10 % 자리. 밭의 90 % 가 이 값 이상이다.")
    print("  표류% = 평균 구간 뒷절반으로 다시 평균했을 때 P10 이 움직인 폭.")
    print("          크면 평균 구간이 모자란 것이다 (Janke 외 2020 의 사후 검증).")
    print("  옛비율 = 적정구간 비율. 순위에는 쓰지 않는다 - 합격선 근처에서 크게 튄다.")
    print("  온도는 순위에 쓰지 않는다. 지금 열원이 에어컨뿐이라 근거가 없다.")

    out = a.out or os.path.join(REPO, "data", "judge.json")
    json.dump({"band_m_s": list(band), "stagnant_m_s": STAGNANT,
               "mode": "last" if a.last_only else "time-average",
               "average_from_s": None if a.last_only else a.average_from,
               "cases": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n  -> %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
