# -*- coding: utf-8 -*-
"""CFD 결과에서 판정면 점의 k · ε · 압력을 뽑는다 — 팬 RANS-PINN 의 난류량 데이터.

왜
    RANS-PINN 논문(arXiv:2306.06034)은 속도·압력·k·ε 를 모두 학습에 쓴다.
    data/fan-dataset/fields/ 에는 속도·온도뿐이라 PINN 이 k → 0 자명해에 빠졌다.
    케이스 폴더의 300~450 초 시간 폴더에는 k · ε · p 가 있으므로, 판정면과 같은 점에서 뽑아
    data/fan-dataset/keps/<run_id>.csv 로 둔다.

어디서
    케이스 폴더는 WSL ~/smartfarm-cfd/cases/fan-study-mac/<run_id>/ (맥에서 T7 로 옮겨 온 11~14).
    processor*/ 로 나뉜 채라 reconstructPar 로 300~450 초만 합친 뒤 sample 로 뽑는다.
    OpenFOAM 은 도커 opencfd/openfoam-default:2512 (이 PC 규약: --user 1000:1000, HOME=/tmp).

순서
    1) 이 스크립트(윈도우 파이썬)가 판정점(fields/<run_id>.csv 의 베드 안 점)으로
       케이스의 system/sampleKeps 를 쓴다
    2) 도커에서 reconstructPar -time 300:450 → postProcess -dict system/sampleKeps -time 300:450
    3) 출력 .xy 를 읽어 시각별 CSV 로 편다

실행
    py -m src.extract_keps 11_S3 12_S4 13_S5 14_S6
"""
from __future__ import annotations

import csv
import glob
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = os.path.join(REPO, "data", "fan-dataset", "fields")
OUT = os.path.join(REPO, "data", "fan-dataset", "keps")
WSL_ROOT = "/home/hunvr/smartfarm-cfd/cases/fan-study-mac"
WIN_ROOT = r"\\wsl.localhost\Ubuntu" + WSL_ROOT.replace("/", "\\")
IMAGE = "opencfd/openfoam-default:2512"
VARS = ["k", "epsilon", "p", "p_rgh", "nut", "T", "U"]
TIMES = "300:450"


def plane_points(rid):
    pts = {}
    with io.open(os.path.join(FIELDS, rid + ".csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["in_bed"] == "1":
                pts[(r["x_m"], r["y_m"], r["z_m"])] = r["plane"]
    return pts


def write_dict(rid, pts):
    body = "\n".join("            (%s %s %s)" % k for k in pts)
    d = """FoamFile { version 2.0; format ascii; class dictionary; object sampleKeps; }
    type            sets;
    libs            (sampling);
    interpolationScheme cellPoint;
    setFormat       raw;
    fields          (%s);
    sets
    {
        canopy
        {
            type    cloud;
            axis    xyz;
            points
            (
%s
            );
        }
    }
""" % (" ".join(VARS), body)
    path = os.path.join(WIN_ROOT, rid, "system", "sampleKeps")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(d)


def run_docker(rid):
    cmd = ("source /usr/lib/openfoam/openfoam*/etc/bashrc >/dev/null 2>&1; cd /data/%s && "
           "(ls -d 300 >/dev/null 2>&1 || reconstructPar -time %s > log.reconstructKeps 2>&1) && "
           "postProcess -func sampleKeps -time %s > log.sampleKeps 2>&1; echo rc=$?" % (rid, TIMES, TIMES))
    full = ["wsl", "-e", "docker", "run", "--rm", "--user", "1000:1000", "-e", "HOME=/tmp",
            "-v", "%s:/data" % WSL_ROOT, IMAGE, "bash", "-lc", cmd]
    r = subprocess.run(full, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("  docker", rid, (r.stdout + r.stderr).strip()[-300:])


def collect(rid, pts):
    """postProcessing/sampleKeps/<t>/canopy_<vars>.xy 를 읽어 CSV 로."""
    base = os.path.join(WIN_ROOT, rid, "postProcessing", "sampleKeps")
    rows = []
    for tdir in sorted(glob.glob(os.path.join(base, "*")), key=lambda p: float(os.path.basename(p))):
        t = os.path.basename(tdir)
        cols = {}
        for fp in glob.glob(os.path.join(tdir, "canopy_*.xy")):
            names = os.path.basename(fp)[len("canopy_"):-3].split("_")
            # 스칼라 묶음과 벡터 묶음이 따로 나온다. 이름 순서대로 열이 붙는다.
            with io.open(fp, encoding="utf-8") as f:
                for line in f:
                    v = line.split()
                    if not v:
                        continue
                    key = tuple("%g" % float(x) for x in v[:3])
                    rest, i, out = v[3:], 0, cols.setdefault(key, {})
                    for n in _split_names(names):
                        w = 3 if n == "U" else 1
                        out[n] = rest[i:i + w]
                        i += w
        for (x, y, z), c in cols.items():
            plane = pts.get(_match(x, y, z, pts))
            u = c.get("U", ["nan"] * 3)
            rows.append([rid, plane, t, x, y, z] + [c.get(n, ["nan"])[0] for n in VARS if n != "U"] + u)
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, rid + ".csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "plane", "t_s", "x_m", "y_m", "z_m"] + [n for n in VARS if n != "U"]
                   + ["Ux", "Uy", "Uz"])
        w.writerows(rows)
    print("  %s: %d 행 -> data/fan-dataset/keps/%s.csv" % (rid, len(rows), rid))


def _split_names(names):
    # OpenFOAM 은 필드 이름을 '_' 로 이어 붙인다. p_rgh 처럼 이름 안의 '_' 를 되살린다.
    out, i = [], 0
    while i < len(names):
        if names[i] == "p" and i + 1 < len(names) and names[i + 1] == "rgh":
            out.append("p_rgh"); i += 2
        else:
            out.append(names[i]); i += 1
    return out


_LOOK = {}


def _match(x, y, z, pts):
    if not _LOOK:
        for k in pts:
            _LOOK[tuple("%g" % float(v) for v in k)] = k
    return _LOOK.get((x, y, z))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for rid in sys.argv[1:]:
        _LOOK.clear()
        pts = plane_points(rid)
        print("%s: 판정점 %d" % (rid, len(pts)), flush=True)
        write_dict(rid, pts)
        run_docker(rid)
        collect(rid, pts)


if __name__ == "__main__":
    main()
