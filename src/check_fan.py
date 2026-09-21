"""팬이 계산에 제대로 들어갔는지, 그 바람이 어디까지 갔는지 검산한다.

    py -m src.check_fan --run ~/smartfarm-cfd/cases/fan-study/05_F3

두 가지를 본다.

  ① 제대로 나오나 — 셀 영역이 실제로 몇 셀을 잡았고, 그 부피로 나눈 힘 밀도가
     얼마인가. `vectorSemiImplicitSource` 는 `volumeMode absolute` 라 총 추력(N)은
     격자와 무관하게 정확하지만, **그 힘이 퍼지는 부피**는 잡힌 셀 수가 정한다.
     설계 부피(실제 팬 치수)보다 얼마나 희석됐는지 숫자로 남긴다.
     E-001(셀 0개)은 여기서 다시 걸린다.

  ② 온전하게 가나 — 팬 하류와 캐노피 판정면을 지나는 유량(m³/s)이
     팬이 내보낸 풍량과 어떻게 다른가. 하류가 더 크면 주위 공기를 끌고 간 것이고
     (유인), 캐노피 쪽이 작으면 도중에 새고 있다는 뜻이다.

②는 `FOfanflux` 함수오브젝트가 남긴 `postProcessing/` 파일이 있어야 돈다.
없으면 ①만 하고 그 사실을 밝힌다. 계산을 돌리지 않고도 ①은 언제나 할 수 있다.

나가는 값: 검산에 걸린 것이 있으면 1, 없으면 0.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAMS = os.path.join(REPO, "data", "fan_params.json")

# 잡힌 셀 수가 이보다 적으면 팬을 셀 영역으로 대표한다고 보기 어렵다.
# 축마다 최소 두 줄(2x2x2)은 들어와야 방향을 가진 힘으로 읽힌다.
MIN_CELLS = 8


def zone_sizes(log_path):
    """log.topoSet 에서 {셀존 이름: 셀 수}. 마지막에 적힌 값이 최종값이다."""
    out = {}
    if not os.path.exists(log_path):
        return out
    txt = open(log_path, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"cellZoneSet\s+(\S+)\s+now size\s+(\d+)", txt):
        out[m.group(1)] = int(m.group(2))
    return out


def flux_last(run, name):
    """postProcessing/<name>/*/surfaceFieldValue.dat 마지막 줄의 값(m3/s)."""
    pat = os.path.join(run, "postProcessing", name, "*", "surfaceFieldValue.dat")
    files = sorted(glob.glob(pat))
    if not files:
        return None
    last = None
    for line in open(files[-1], encoding="utf-8", errors="replace"):
        if line.startswith("#") or not line.strip():
            continue
        last = line.split()
    if not last or len(last) < 2:
        return None
    try:
        return float(last[-1])
    except ValueError:
        return None


def find_case(params, run):
    """실행 폴더 이름(예 05_F3)으로 케이스를 찾는다."""
    rid = os.path.basename(os.path.normpath(run))
    for c in params["cases"]:
        if c.get("run_id") == rid:
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="케이스 실행 폴더")
    ap.add_argument("--cell", type=float, default=None,
                    help="격자 한 변(m). 생략하면 fan_params.json 의 refine.cell_inside_m")
    ap.add_argument("--params", default=PARAMS)
    ap.add_argument("--tol", type=float, default=0.05,
                    help="유량 대조 허용 오차 비율 (기본 5%%)")
    a = ap.parse_args()

    params = json.load(open(a.params, encoding="utf-8"))
    case = find_case(params, a.run)
    if case is None:
        print("케이스를 찾지 못했다: %s" % a.run)
        return 1

    # 팬은 전부 세분 상자 안에 있으므로 기준 격자는 세분 뒤의 한 변이다.
    ref = params.get("refine") or {}
    cell = a.cell or ref.get("cell_inside_m") or params.get("mesh_cell_m") or 0.10
    zones = case.get("fan_zones") or []
    sizes = zone_sizes(os.path.join(a.run, "log.topoSet"))
    bad = []

    print("케이스 %s (%s) — 격자 %.3f m" % (case["no"], case["run_id"], cell))
    print()

    if not zones:
        print("  팬 영역 없음 — 이 케이스는 팬을 켜지 않는다. ① 검산 대상 없음.")
    else:
        print("  ① 셀 영역과 힘 밀도")
        print("  %-14s %6s %10s %10s %10s %8s" %
              ("팬", "셀", "실부피m3", "설계부피", "N/m3", "희석"))
        cv = cell ** 3
        for z in zones:
            nm = z["id"].lower()
            n = sizes.get(nm)
            fb = z["fan_box_cfd_m"]
            v_design = 1.0
            for i in range(3):
                v_design *= fb["max"][i] - fb["min"][i]
            f = z["thrust_N"]
            if n is None:
                print("  %-14s %6s  log.topoSet 에 기록 없음" % (z["id"], "?"))
                bad.append("%s: 셀존 기록 없음" % z["id"])
                continue
            v_real = n * cv
            dens = (f / v_real) if v_real else 0.0
            ratio = (v_real / v_design) if v_design else 0.0
            flag = ""
            if n == 0:
                flag = "  <- 비었다 (E-001)"
                bad.append("%s: 셀 0개" % z["id"])
            elif n < MIN_CELLS:
                flag = "  <- %d개 미만" % MIN_CELLS
                bad.append("%s: 셀 %d개" % (z["id"], n))
            print("  %-14s %6d %10.5f %10.5f %10.1f %7.1f배%s" %
                  (z["id"], n, v_real, v_design, dens, ratio, flag))

        print()
        print("  총 추력은 volumeMode absolute 라 셀 수와 무관하게 유지된다.")
        print("  희석 배수는 그 추력이 설계보다 몇 배 넓은 부피에 퍼지는지를 뜻한다.")

    # ---- ② 유량 ----
    print()
    print("  ② 유량 — 팬이 내보낸 바람이 캐노피까지 가나")
    any_flux = False
    for z in zones:
        q = z.get("flow_m3s") or 0.0
        got = flux_last(a.run, "fanflux_" + z["id"].lower())
        if got is None:
            continue
        any_flux = True
        d = (got - q) / q if q else 0.0
        print("  %-14s 팬 %6.4f m3/s -> 하류 %7.4f  (%+.0f%%)" %
              (z["id"], q, got, d * 100))
        if got < q * (1 - a.tol):
            bad.append("%s: 하류 유량이 팬 풍량보다 작다" % z["id"])
    for plane in (params.get("judge_planes") or []):
        got = flux_last(a.run, "canopyflux_" + plane.get("name", ""))
        if got is None:
            continue
        any_flux = True
        print("  %-14s 판정면 통과 %7.4f m3/s" % (plane.get("name", "?"), got))
    if not any_flux:
        print("  postProcessing 에 유량 기록이 없다 — 아직 돌리지 않았거나")
        print("  FOfanflux 가 controlDict 에 들어가지 않았다. ② 는 건너뛴다.")

    print()
    if bad:
        print("검산에 걸린 것 %d 건:" % len(bad))
        for b in bad:
            print("  - " + b)
        return 1
    print("검산 통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
