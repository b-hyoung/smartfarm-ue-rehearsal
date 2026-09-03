#!/usr/bin/env pvpython
"""OpenFOAM 케이스 -> UE 프레임 CSV.

목데이터 생성기(`src/generate_frames.py`)와 **완전히 같은 스키마**를 낸다.
UE 쪽 코드는 목/실데이터를 구분하지 않는다 — 폴더만 바꿔 끼우면 된다.

    x,y,z,T,Ux,Uy,Uz,p,source

실행 (ParaView 의 pvbatch 필요, OpenFOAM 환경은 불필요):

    pvbatch cfd/extract_frames.py <case_dir> <out_dir> [--frames 15]

예:
    pvbatch cfd/extract_frames.py ~/smartfarm-cfd/cases/acRoom-transient \\
                                  ~/smartfarm-cfd/out/ue_frames/base_25cmm_289K

산출물: out_dir/frame_00..NN.csv + out_dir/manifest.json
"""

import argparse
import json
import os
import re
import sys

import numpy as np

from paraview import servermanager as sm
from paraview.simple import (
    CellDatatoPointData,
    MergeBlocks,
    OpenFOAMReader,
    UpdatePipeline,
)

try:  # ParaView 6.x
    from vtkmodules.util.numpy_support import vtk_to_numpy
except ImportError:  # ParaView 5.x
    from vtk.util.numpy_support import vtk_to_numpy


# CFD 좌표(x: -4..4)를 UE 좌표(x: 0..8)로 옮기는 값. manifest 에 기록된다.
X_SHIFT_M = 4.0

# 기존 out/ue_frames/*.csv 와 자릿수까지 동일하게 맞춘 포맷.
ROW_FMT = "%.4f,%.4f,%.4f,%.3f,%.4f,%.4f,%.4f,%.2f,simulated"
HEADER = "x,y,z,T,Ux,Uy,Uz,p,source"


# --------------------------------------------------------------------------- #
# 케이스에서 운전 조건 읽기 (스윕한 케이스도 자기 값이 manifest 에 적히도록)
# --------------------------------------------------------------------------- #

def _inlet_blocks(text):
    """boundaryField 안의 inlet* 패치 블록 본문들을 돌려준다."""
    return [m.group(1) for m in re.finditer(r"\binlet\w*\s*\{(.*?)\}", text, re.S)]


def read_case_params(case_dir):
    """0.orig/T, 0.orig/U 에서 토출온도와 풍량을 읽는다."""
    params = {"supply_K": None, "flow_CMM": None, "n_inlets": 0}

    t_path = os.path.join(case_dir, "0.orig", "T")
    if os.path.exists(t_path):
        with open(t_path, encoding="utf-8") as f:
            temps = []
            for body in _inlet_blocks(f.read()):
                m = re.search(r"value\s+uniform\s+([-\d.eE+]+)\s*;", body)
                if m:
                    temps.append(float(m.group(1)))
        if temps:
            params["supply_K"] = temps[0] if len(set(temps)) == 1 else temps
            params["n_inlets"] = len(temps)

    u_path = os.path.join(case_dir, "0.orig", "U")
    if os.path.exists(u_path):
        with open(u_path, encoding="utf-8") as f:
            rates = []
            for body in _inlet_blocks(f.read()):
                m = re.search(
                    r"volumetricFlowRate\s+constant\s+([-\d.eE+]+)\s*;", body
                )
                if m:
                    rates.append(float(m.group(1)))
        if rates:
            # m3/s -> CMM(m3/min), 슬롯 전체 합계
            params["flow_CMM"] = round(sum(rates) * 60.0, 3)
            params["n_inlets"] = params["n_inlets"] or len(rates)

    return params


# --------------------------------------------------------------------------- #
# ParaView 파이프라인
# --------------------------------------------------------------------------- #

def find_foam_file(case_dir):
    """케이스 폴더의 *.foam 을 찾고, 없으면 만든다(빈 파일이면 충분)."""
    for name in sorted(os.listdir(case_dir)):
        if name.endswith(".foam"):
            return os.path.join(case_dir, name)
    path = os.path.join(case_dir, "case.foam")
    open(path, "a").close()
    return path


def time_dir_exists(case_dir, t, decomposed=False):
    """그 시각의 결과 폴더가 실제로 디스크에 있는지 확인."""
    name = f"{t:g}"                       # 0.0 -> "0",  900.0 -> "900"
    root = os.path.join(case_dir, "processor0") if decomposed else case_dir
    return os.path.isdir(os.path.join(root, name))


def open_case(case_dir, decomposed=False):
    reader = OpenFOAMReader(registrationName="case", FileName=find_foam_file(case_dir))
    reader.MeshRegions = ["internalMesh"]
    reader.CellArrays = ["T", "U", "p"]
    reader.CaseType = "Decomposed Case" if decomposed else "Reconstructed Case"

    # t=0(초기장)도 프레임에 포함한다.
    #   SkipZeroTime 만으로는 부족하다 — 이 리더는 폴더를 훑을 때 0 을 빼고 센다.
    #   controlDict 기준으로 시각을 나열하면 0 이 들어온다. 대신 controlDict 에만
    #   있고 실제로 안 써진 시각이 섞일 수 있어, 아래에서 디스크와 대조해 걸러낸다.
    reader.SkipZeroTime = 0
    reader.ListtimestepsaccordingtocontrolDict = 1

    # ⚠ 리더 자체의 셀->점 보간은 끈다.
    #   켜면 경계 패치 값을 점에 그대로 얹는데, walls 가 fixedValue 302K(29도)라
    #   방 외피 전체(약 10,800점)가 302K 로 칠해져 내부 기류가 안 보인다.
    #   대신 아래 CellDatatoPointData 로 "인접 셀 평균"만 쓴다 = 공기 온도장.
    reader.Createcelltopointfiltereddata = 0
    reader.UpdatePipelineInformation()

    times = [float(t) for t in reader.TimestepValues]
    times = [t for t in times if time_dir_exists(case_dir, t, decomposed)]
    if not times:
        sys.exit(f"[!] 시간 디렉터리가 없습니다: {case_dir}\n"
                 f"    솔버를 먼저 돌리고 reconstructPar 까지 마쳤는지 확인하세요.")

    merged = MergeBlocks(registrationName="merged", Input=reader)
    c2p = CellDatatoPointData(registrationName="c2p", Input=merged)
    c2p.ProcessAllArrays = 1
    return c2p, times


def pick_frame_times(times, n_frames):
    """0 ~ endTime 을 균등분할하고, 각 지점에서 가장 가까운 저장시각으로 스냅."""
    arr = np.asarray(times, dtype=float)
    picked = []
    for target in np.linspace(arr[0], arr[-1], n_frames):
        picked.append(float(arr[int(np.argmin(np.abs(arr - target)))]))
    return picked


def fetch_frame(merged, time_s):
    """한 시각의 점 좌표와 필드를 numpy 로 가져온다."""
    UpdatePipeline(time=time_s, proxy=merged)
    data = sm.Fetch(merged)

    pts = vtk_to_numpy(data.GetPoints().GetData())
    pd = data.GetPointData()

    missing = [n for n in ("T", "U", "p") if pd.GetArray(n) is None]
    if missing:
        sys.exit(f"[!] {time_s}s 에 필드가 없습니다: {', '.join(missing)}")

    T = vtk_to_numpy(pd.GetArray("T")).reshape(-1)
    U = vtk_to_numpy(pd.GetArray("U")).reshape(-1, 3)
    p = vtk_to_numpy(pd.GetArray("p")).reshape(-1)

    rows = np.empty((pts.shape[0], 8), dtype=float)
    rows[:, 0] = pts[:, 0] + X_SHIFT_M     # CFD x(-4..4) -> UE x(0..8)
    rows[:, 1] = pts[:, 1]
    rows[:, 2] = pts[:, 2]
    rows[:, 3] = T
    rows[:, 4:7] = U
    rows[:, 7] = p
    return rows


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description="OpenFOAM 케이스 -> UE 프레임 CSV")
    ap.add_argument("case_dir", help="OpenFOAM 케이스 폴더")
    ap.add_argument("out_dir", help="frame_*.csv 를 쓸 폴더")
    ap.add_argument("--frames", type=int, default=15, help="뽑을 프레임 수 (기본 15)")
    ap.add_argument("--decomposed", action="store_true",
                    help="reconstructPar 를 안 돌렸을 때 processor* 를 직접 읽는다")
    args = ap.parse_args()

    case_dir = os.path.abspath(os.path.expanduser(args.case_dir))
    out_dir = os.path.abspath(os.path.expanduser(args.out_dir))
    os.makedirs(out_dir, exist_ok=True)

    merged, times = open_case(case_dir, decomposed=args.decomposed)
    picked = pick_frame_times(times, args.frames)
    print(f"[i] 저장시각 {len(times)}개 중 {len(picked)}개 선택 "
          f"({picked[0]:g}s ~ {picked[-1]:g}s)")

    entries = []
    for i, t in enumerate(picked):
        rows = fetch_frame(merged, t)
        name = f"frame_{i:02d}.csv"
        np.savetxt(os.path.join(out_dir, name), rows,
                   fmt=ROW_FMT, header=HEADER, comments="")
        entries.append({"frame": i, "time_s": t,
                        "points": int(rows.shape[0]), "file": name})
        print(f"    {name}  t={t:7.1f}s  {rows.shape[0]}점  "
              f"T {rows[:, 3].min():.2f}~{rows[:, 3].max():.2f}K")

    params = read_case_params(case_dir)
    manifest = {
        "source": "simulated",
        "case": os.path.basename(case_dir),
        "solver": "buoyantPimpleFoam (OpenFOAM v2512)",
        "room_m": {"Lx": 8.0, "Ly": 5.7, "Lz": 2.7, "shape": "D (semi-ellipse)"},
        "coord_note": f"CFD x(-4..4) shifted by +{X_SHIFT_M} to UE x(0..8)",
        "ac": {
            "type": "4Way ceiling cassette",
            "flow_CMM": params["flow_CMM"],
            "supply_K": params["supply_K"],
            "centre_ue_m": [4.0, 2.0, 2.7],
        },
        "frames": entries,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[+] 완료 -> {out_dir}")


if __name__ == "__main__":
    main()
