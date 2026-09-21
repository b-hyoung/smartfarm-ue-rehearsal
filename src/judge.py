"""판정면 표본에서 케이스 성적을 낸다 — 분위수로.

    py -m src.judge --runs ~/smartfarm-cfd/cases/fan-study
    py -m src.judge --runs ... --band 0.25 1.2     다른 작물 기준으로 다시 채점

왜 분위수인가
    지금까지 1 순위 지표는 "적정구간 비율"(0.3~1.0 m/s 인 점의 비율)이었다.
    이 값은 점마다 0 또는 1 로 세므로, 값이 합격선 근처에 몰려 있으면
    격자를 조금만 바꿔도 무더기로 선을 넘나들어 크게 튄다. 평균이 4 % 움직일 때
    비율이 20 %p 움직이는 일이 생긴다. 그러면 격자 수렴(GCI)을 낼 수도 없다 —
    "변화량"이라는 말 자체가 성립하지 않기 때문이다.

    분위수는 개수가 아니라 값이다. 전체가 0.03 밀리면 분위수도 0.03 밀린다.
    부드럽게 변하므로 GCI 를 낼 수 있고, 덤으로 **어디가 나쁜지**를 알려준다.

        P10  밑에서 10 % 자리 — "제일 안 통하는 구석이 얼마인가"
        P50  한가운데       — 평균보다 튀는 값에 덜 휘둘린다
        P90  위에서 10 %    — "너무 센 데는 없는가"

    작물은 평균으로 자라지 않는다. 제일 바람 안 통하는 자리의 상추가 먼저 상한다.
    그래서 1 순위를 P10 으로 둔다. 최솟값을 쓰지 않는 이유는 점 하나짜리라
    벽에 붙은 한 점이나 계산이 튄 한 점에 판단이 휘둘리기 때문이다.

    기존 지표(평균·상대표준편차·층간 차이·적정구간 비율)도 같이 낸다. 비율은
    순위에서 빼되 값은 남겨, 옛 판정과 대조할 수 있게 한다.

무엇을 읽는가
    controlDict 의 `canopy` 함수오브젝트가 남긴
        postProcessing/canopy/<시각>/U_<면이름>.raw   (x y z Ux Uy Uz)
        postProcessing/canopy/<시각>/T_<면이름>.raw   (x y z T)
    가장 늦은 시각을 쓴다. 온도는 순위에 쓰지 않고 표에만 남긴다 — 지금 열원이
    조명 없이 에어컨뿐이라 온도로 판정할 근거가 없다. 조명이 들어오면 그때
    같은 파일로 지표를 붙이면 된다.

    CDF 를 `--cdf` 로 저장해 두면 합격선이 바뀌어도(작물이 바뀌어도) 계산을
    다시 돌리지 않고 다시 채점할 수 있다.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os

import sys

# 윈도우 콘솔이 cp949 라 한글 대시(—) 같은 글자에서 죽는다.
# 배치 스크립트 안에서 돌 때 이것 때문에 통째로 실패한 적이 있다.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAND = (0.3, 1.0)          # 적정 구간 — Kitaya 2003 하한, Zhang & Kacira 2016 상한
STAGNANT = 0.1             # 정체로 보는 선
QS = (10, 50, 90)          # 뽑을 분위수


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


def read_raw(path, ncol):
    """raw 표본 파일 -> 값 목록. 앞 세 칸은 좌표다."""
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.split()
        if len(f) < 3 + ncol:
            continue
        try:
            out.append([float(v) for v in f[3:3 + ncol]])
        except ValueError:
            continue
    return out


def latest_dir(run):
    """postProcessing/canopy 아래 가장 늦은 시각 폴더."""
    base = os.path.join(run, "postProcessing", "canopy")
    if not os.path.isdir(base):
        return None
    ts = []
    for d in os.listdir(base):
        try:
            ts.append((float(d), os.path.join(base, d)))
        except ValueError:
            continue
    return max(ts)[1] if ts else None


def plane_stats(d, name, band, want_cdf=False):
    """면 하나의 성적. 없으면 None."""
    up = os.path.join(d, "U_%s.raw" % name)
    if not os.path.exists(up):
        return None
    mags = sorted(math.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2) for u in read_raw(up, 3))
    if not mags:
        return None
    n = len(mags)
    mean = sum(mags) / n
    var = sum((v - mean) ** 2 for v in mags) / n
    sd = math.sqrt(var)
    lo, hi = band

    s = {
        "n": n,
        "P10": round(quantile(mags, 10), 4),
        "P50": round(quantile(mags, 50), 4),
        "P90": round(quantile(mags, 90), 4),
        "mean": round(mean, 4),
        "cov": round(sd / mean, 4) if mean else float("nan"),
        # 옛 지표 — 순위에는 쓰지 않고 대조용으로만 남긴다
        "band_ratio": round(sum(1 for v in mags if lo <= v <= hi) / n, 4),
        "stagnant_ratio": round(sum(1 for v in mags if v < STAGNANT) / n, 4),
    }
    s["spread"] = round(s["P90"] / s["P10"], 3) if s["P10"] > 1e-9 else float("inf")

    tp = os.path.join(d, "T_%s.raw" % name)
    if os.path.exists(tp):
        ts = [v[0] for v in read_raw(tp, 1)]
        if ts:
            tm = sum(ts) / len(ts)
            s["T_mean_C"] = round(tm - 273.15, 2)
            s["T_sd"] = round(math.sqrt(sum((v - tm) ** 2 for v in ts) / len(ts)), 3)

    if want_cdf:
        # 합격선을 나중에 바꿔도 다시 채점할 수 있게 100 점으로 남긴다
        s["cdf"] = [[round(quantile(mags, q), 4), q] for q in range(0, 101)]
    return s


def judge_run(run, band, want_cdf=False):
    d = latest_dir(run)
    if d is None:
        return None
    names = sorted({os.path.basename(f)[2:-4]
                    for f in glob.glob(os.path.join(d, "U_*.raw"))})
    planes = {}
    for nm in names:
        st = plane_stats(d, nm, band, want_cdf)
        if st:
            planes[nm] = st
    if not planes:
        return None

    worst = min(p["P10"] for p in planes.values())
    hottest = max(p["P90"] for p in planes.values())
    means = [p["mean"] for p in planes.values()]
    return {
        "run_id": os.path.basename(os.path.normpath(run)),
        "time_s": float(os.path.basename(d)),
        "planes": planes,
        # 케이스 성적 — 네 면 가운데 가장 나쁜 쪽으로 대표한다
        "P10_worst": round(worst, 4),
        "P90_max": round(hottest, 4),
        "tier_gap": round(max(means) - min(means), 4),
        "pass_low": worst >= band[0],
        "pass_high": hottest <= band[1],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="케이스 폴더들이 든 상위 폴더")
    ap.add_argument("--band", nargs=2, type=float, default=list(BAND),
                    metavar=("LO", "HI"), help="적정 구간 (m/s). 작물이 바뀌면 여기만 바꾼다")
    ap.add_argument("--cdf", action="store_true", help="CDF 까지 JSON 에 남긴다")
    ap.add_argument("--out", default=None, help="JSON 저장 경로")
    a = ap.parse_args()
    band = (a.band[0], a.band[1])

    runs = sorted(d for d in glob.glob(os.path.join(a.runs, "*"))
                  if os.path.isdir(d))
    rows = [r for r in (judge_run(d, band, a.cdf) for d in runs) if r]
    if not rows:
        print("판정면 표본을 찾지 못했다. 아직 돌리지 않았거나 canopy 함수오브젝트가 "
              "controlDict 에 없다.")
        print("  찾은 폴더 %d 개: %s" % (len(runs), a.runs))
        return 1

    # 1 순위 P10(높을수록), 2 순위 층간 차이(작을수록)
    rows.sort(key=lambda r: (-r["P10_worst"], r["tier_gap"]))

    print("적정 구간 %.2f ~ %.2f m/s · 케이스 %d 개 · 1 순위 P10(가장 나쁜 면)"
          % (band[0], band[1], len(rows)))
    print()
    print("  %-14s %7s %7s %7s %7s %8s %7s  %s"
          % ("케이스", "P10", "P50", "P90", "층간차", "옛비율", "온도℃", "판정"))
    for r in rows:
        p = list(r["planes"].values())
        p50 = sum(x["P50"] for x in p) / len(p)
        ratio = sum(x["band_ratio"] for x in p) / len(p)
        temps = [x["T_mean_C"] for x in p if "T_mean_C" in x]
        tstr = "%7.1f" % (sum(temps) / len(temps)) if temps else "      -"
        mark = "통과" if (r["pass_low"] and r["pass_high"]) else (
            "하한미달" if not r["pass_low"] else "상한초과")
        print("  %-14s %7.3f %7.3f %7.3f %7.3f %7.1f%% %s  %s"
              % (r["run_id"], r["P10_worst"], p50, r["P90_max"],
                 r["tier_gap"], ratio * 100, tstr, mark))

    print()
    print("  P10 = 밑에서 10 % 자리. 밭의 90 % 가 이 값 이상이다.")
    print("  옛비율 = 적정구간 비율. 순위에는 쓰지 않는다 — 합격선 근처에서 크게 튄다.")
    print("  온도는 순위에 쓰지 않는다. 지금 열원이 에어컨뿐이라 근거가 없다.")

    out = a.out or os.path.join(REPO, "data", "judge.json")
    json.dump({"band_m_s": list(band), "stagnant_m_s": STAGNANT, "cases": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n  -> %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
