"""fan_params.json 의 케이스를 OpenFOAM 케이스 폴더로 펼친다. (WSL 에서 실행)

    data/fan_params.json
        ↓
    ~/smartfarm-cfd/cases/fan-study/NN_XX/   케이스마다 0.orig·constant·system·Allrun

무엇을 만드는가
    · 재배단 막힘 — topoSet 으로 셀을 덜어내고 그 면을 rackWalls 벽으로 만든다
    · 팬 — 셀존을 잡고 fvOptions 의 vectorSemiImplicitSource 로 추력을 준다
    · 판정면 — 캐노피 중간·윗면 평면에서 magU 를 저장한다
    · 에어컨 — 템플릿(acRoom-vane25)의 취출·리턴 패치를 그대로 쓴다. 끄지 않는다

⚠ 이 스크립트는 케이스를 만들 뿐 해석을 돌리지 않는다. 실행은 run_foam_cases.sh 가 한다.

    python3 src/make_foam_cases.py [--cases 1-10] [--end 180] [--np 12]
                                   [--repo 저장소] [--template 기존케이스] [--out 출력폴더]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil

# 경로는 인자나 환경변수로 바꾼다. 기본값은 이 파일이 있는 저장소와 ~/smartfarm-cfd 다.
REPO_DEFAULT = os.environ.get(
    "SF_REPO", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DEFAULT = os.environ.get(
    "SF_TEMPLATE", os.path.expanduser("~/smartfarm-cfd/cases/acRoom-vane25"))
OUT_DEFAULT = os.environ.get(
    "SF_OUT", os.path.expanduser("~/smartfarm-cfd/cases/fan-study"))
FIELDS = ["U", "T", "p", "p_rgh", "k", "epsilon", "nut", "alphat"]
ROOM_BOX = ((-4.05, -0.05, -0.05), (4.05, 5.75, 2.75))   # CFD 좌표 전체를 덮는 상자


def head(cls, obj):
    return ("FoamFile\n{\n    version     2.0;\n    format      ascii;\n"
            "    class       %s;\n    object      %s;\n}\n\n" % (cls, obj))


def add_rack_patch(field_path):
    """0.orig 각 필드에 walls 블록을 복사해 rackWalls 를 넣는다."""
    txt = open(field_path, encoding="utf-8", errors="replace").read()
    if "rackWalls" in txt:
        return
    m = re.search(r"\n(\s*)walls\s*\n\s*\{(.*?)\n\s*\}", txt, re.S)
    if not m:
        return
    indent, body = m.group(1), m.group(2)
    block = "\n%swalls\n%s{%s\n%s}\n\n%srackWalls\n%s{%s\n%s}" % (
        indent, indent, body, indent, indent, indent, body, indent)
    txt = txt[:m.start()] + block + txt[m.end():]
    open(field_path, "w", encoding="utf-8").write(txt)


def topo_rack(blockage):
    """재배단 셀을 덜어낸 keep 집합 — subsetMesh 입력."""
    acts = ["    {\n        name    keep;\n        type    cellSet;\n"
            "        action  new;\n        source  boxToCell;\n"
            "        box     (%g %g %g) (%g %g %g);\n    }"
            % (ROOM_BOX[0] + ROOM_BOX[1])]
    for b in blockage:
        mn, mx = b["box_cfd_m"]["min"], b["box_cfd_m"]["max"]
        acts.append("    {\n        name    keep;\n        type    cellSet;\n"
                    "        action  subtract;\n        source  boxToCell;\n"
                    "        box     (%g %g %g) (%g %g %g);   // %s\n    }"
                    % (mn[0], mn[1], mn[2], mx[0], mx[1], mx[2], b["name"]))
    return head("dictionary", "topoSetDict") + "actions\n(\n" + "\n".join(acts) + "\n);\n"


def topo_fans(zones):
    """팬 셀존 — fvOptions 가 여기에 힘을 준다."""
    acts = []
    for z in zones:
        mn, mx = z["cellZone_box_cfd_m"]["min"], z["cellZone_box_cfd_m"]["max"]
        nm = z["id"].lower()
        acts.append("    {\n        name    %s;\n        type    cellSet;\n"
                    "        action  new;\n        source  boxToCell;\n"
                    "        box     (%g %g %g) (%g %g %g);\n    }" %
                    (nm, mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]))
        acts.append("    {\n        name    %s;\n        type    cellZoneSet;\n"
                    "        action  new;\n        source  setToCellZone;\n"
                    "        set     %s;\n    }" % (nm, nm))
    if not acts:
        acts.append("    {\n        name    dummy;\n        type    cellSet;\n"
                    "        action  new;\n        source  boxToCell;\n"
                    "        box     (0 0 0) (0.001 0.001 0.001);\n    }")
    return head("dictionary", "topoSetDict") + "actions\n(\n" + "\n".join(acts) + "\n);\n"


def fv_options(zones):
    """온도 제한(템플릿 유지) + 팬 추력."""
    s = head("dictionary", "fvOptions")
    s += ("limitTAir\n{\n    type       limitTemperature;\n    min        280;\n"
          "    max        310;\n    selectionMode all;\n}\n\n")
    for z in zones:
        nm = z["id"].lower()
        d = z["dir_unit"]
        f = z["thrust_N"]
        s += ("%s\n{\n    type            vectorSemiImplicitSource;\n"
              "    selectionMode   cellZone;\n    cellZone        %s;\n"
              "    volumeMode      absolute;   // Su 가 N 단위\n"
              "    sources\n    {\n        U  ((%.5f %.5f %.5f) 0);   // 추력 %.4f N\n"
              "    }\n}\n\n" % (nm, nm, d[0] * f, d[1] * f, d[2] * f, f))
    return s


def control_dict(end_s, write_s, planes):
    surf = []
    for p in planes:
        surf.append("""        %s
        {
            type            plane;
            planeType       pointAndNormal;
            pointAndNormalDict { point (0 %g %g); normal (0 0 1); }
            interpolate     true;
        }""" % (p["name"], (p["y_range_m"][0] + p["y_range_m"][1]) / 2.0, p["z_cfd_m"]))
    return (head("dictionary", "controlDict") +
            """application     buoyantPimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         %g;
deltaT          0.002;
writeControl    adjustableRunTime;
writeInterval   %g;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;
adjustTimeStep  yes;
maxCo           1.0;
maxDeltaT       0.5;

functions
{
    canopy
    {
        type            surfaces;
        libs            (sampling);
        writeControl    adjustableRunTime;
        writeInterval   %g;
        surfaceFormat   raw;
        fields          (U T);
        surfaces
        {
%s
        }
    }
}
""" % (end_s, write_s, write_s, "\n".join(surf)))


def allrun(np_, with_rack):
    rack = """
runApp topoSet -dict system/topoSetDict.rack
runApp subsetMesh keep -patch rackWalls -overwrite
""" if with_rack else "\n"
    return """#!/bin/bash
# 케이스 하나를 끝까지 돌린다. 컨테이너 안에서 실행된다.
cd "${0%%/*}" || exit 1
set -e
runApp(){ echo "--- $* ---"; "$@" > log."$1" 2>&1 || { tail -20 log."$1"; exit 1; }; }

runApp blockMesh
runApp topoSet -dict system/topoSetDict.ac
runApp createPatch -overwrite
%s
runApp topoSet -dict system/topoSetDict.fans
rm -rf 0 && cp -r 0.orig 0
runApp decomposePar -force
mpirun --use-hwthread-cpus -np %d buoyantPimpleFoam -parallel > log.run 2>&1
runApp reconstructPar -latestTime
echo DONE
""" % (rack, np_)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="1-10")
    ap.add_argument("--end", type=float, default=180.0, help="물리 시간 (초)")
    ap.add_argument("--write", type=float, default=30.0)
    ap.add_argument("--np", type=int, default=12)
    ap.add_argument("--repo", default=REPO_DEFAULT, help="fan_params.json 이 있는 저장소")
    ap.add_argument("--template", default=TEMPLATE_DEFAULT, help="복사해 올 기존 OpenFOAM 케이스")
    ap.add_argument("--out", default=OUT_DEFAULT, help="케이스를 펼칠 폴더")
    a = ap.parse_args()
    for label, path in (("저장소", a.repo), ("템플릿 케이스", a.template)):
        if not os.path.isdir(path):
            raise SystemExit("%s 를 찾을 수 없다: %s" % (label, path))
    for f in ("0.orig", "system/blockMeshDict", "system/topoSetDict", "system/createPatchDict",
              "constant/thermophysicalProperties"):
        if not os.path.exists(os.path.join(a.template, f)):
            raise SystemExit("템플릿에 %s 가 없다: %s" % (f, a.template))
    lo, hi = (int(x) for x in a.cases.split("-"))

    spec = json.load(open(os.path.join(a.repo, "data", "fan_params.json"), encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    made = []
    for c in spec["cases"]:
        if not (lo <= c["no"] <= hi):
            continue
        d = os.path.join(a.out, c["run_id"])
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(os.path.join(d, "system"))
        # 템플릿 복사
        shutil.copytree(os.path.join(a.template, "0.orig"), os.path.join(d, "0.orig"))
        os.makedirs(os.path.join(d, "constant"))
        for f in ("g", "thermophysicalProperties", "turbulenceProperties"):
            shutil.copy2(os.path.join(a.template, "constant", f), os.path.join(d, "constant", f))
        for f in ("fvSchemes", "fvSolution", "blockMeshDict", "createPatchDict"):
            shutil.copy2(os.path.join(a.template, "system", f), os.path.join(d, "system", f))
        shutil.copy2(os.path.join(a.template, "system", "topoSetDict"),
                     os.path.join(d, "system", "topoSetDict.ac"))

        with_rack = bool(c["rack"])
        if with_rack:
            for f in FIELDS:
                p = os.path.join(d, "0.orig", f)
                if os.path.isfile(p):
                    add_rack_patch(p)
            open(os.path.join(d, "system", "topoSetDict.rack"), "w", encoding="utf-8").write(
                topo_rack(spec["rack_blockage"]))

        zones = c.get("fan_zones", [])
        open(os.path.join(d, "system", "topoSetDict.fans"), "w", encoding="utf-8").write(
            topo_fans(zones))
        open(os.path.join(d, "system", "fvOptions"), "w", encoding="utf-8").write(
            fv_options(zones))
        open(os.path.join(d, "system", "controlDict"), "w", encoding="utf-8").write(
            control_dict(a.end, a.write, spec["judge_planes"]))
        open(os.path.join(d, "system", "decomposeParDict"), "w", encoding="utf-8").write(
            head("dictionary", "decomposeParDict") +
            "numberOfSubdomains  %d;\nmethod          hierarchical;\n"
            "coeffs\n{\n    n           (%d 2 1);\n}\n" % (a.np, a.np // 2))
        ar = os.path.join(d, "Allrun")
        open(ar, "w", encoding="utf-8").write(allrun(a.np, with_rack))
        os.chmod(ar, 0o755)

        meta = {"no": c["no"], "case": c["case"], "group": c["group"],
                "purpose": c["purpose"], "per_fan_CMM": c["per_fan_CMM"],
                "fans_on": c.get("fans_on", 0), "fans_off": c.get("fans_off", []),
                "rack": with_rack, "endTime_s": a.end, "np": a.np}
        json.dump(meta, open(os.path.join(d, "case.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        made.append((c["no"], c["run_id"], len(zones), with_rack))

    for no, rid, nz, rk in made:
        print("  %2d  %-8s 팬존 %2d  재배단 %s" % (no, rid, nz, "있음" if rk else "없음"))
    print("케이스 %d개 -> %s (물리 %gs, %d분할)" % (len(made), a.out, a.end, a.np))


if __name__ == "__main__":
    main()
