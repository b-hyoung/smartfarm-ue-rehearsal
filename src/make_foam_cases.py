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


BOX_ACT = ("    {" + chr(10) + "        name    %s;" + chr(10) +
           "        type    cellSet;" + chr(10) + "        action  new;" + chr(10) +
           "        source  boxToCell;" + chr(10) +
           "        box     (%g %g %g) (%g %g %g);" + chr(10) + "    }")
ZONE_ACT = ("    {" + chr(10) + "        name    %s;" + chr(10) +
            "        type    cellZoneSet;" + chr(10) + "        action  new;" + chr(10) +
            "        source  setToCellZone;" + chr(10) + "        set     %s;" + chr(10) + "    }")


def topo_fans(zones, canopy=()):
    """팬 셀존과 캐노피 다공체 셀존 — fvOptions 가 힘과 저항을 준다.

    refineMesh 뒤에 돌아야 한다. 세분이 셀 번호를 다시 매기기 때문이다.
    """
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
    for z in canopy:
        mn, mx = z["box_cfd_m"]["min"], z["box_cfd_m"]["max"]
        nm = z["id"].lower()
        acts.append(BOX_ACT % (nm, mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]))
        acts.append(ZONE_ACT % (nm, nm))
    if not acts:
        acts.append("    {\n        name    dummy;\n        type    cellSet;\n"
                    "        action  new;\n        source  boxToCell;\n"
                    "        box     (0 0 0) (0.001 0.001 0.001);\n    }")
    return head("dictionary", "topoSetDict") + "actions\n(\n" + "\n".join(acts) + "\n);\n"


def topo_refine(box):
    """세분할 영역 — refineMesh 입력. 전 케이스 같은 좌표다."""
    mn, mx = box["min"], box["max"]
    body = """// 30 케이스 공통. 케이스마다 옮기지 않는다.
actions
(
    {
        name    refine;
        type    cellSet;
        action  new;
        source  boxToCell;
        box     (%g %g %g) (%g %g %g);
    }
);
""" % (mn[0], mn[1], mn[2], mx[0], mx[1], mx[2])
    return head("dictionary", "topoSetDict") + body


def refine_mesh_dict():
    """refine 집합을 한 단계 쪼갠다. 세 방향 모두 — 제트가 퍼지는 모양을 봐야 한다.

    useHexTopology 를 켜면 육면체를 모서리 중점으로 2x2x2 로 나눈다.
    성긴 쪽과 만나는 면에는 매달린 절점이 생기고 그 셀은 다면체가 된다.
    유한체적법에서는 문제가 없지만 비직교성이 그 경계에서 올라가므로
    세분 뒤 checkMesh 로 한 번 확인한다.
    """
    return head("dictionary", "refineMeshDict") + """set             refine;

coordinateSystem global;

globalCoeffs
{
    tan1            (1 0 0);
    tan2            (0 1 0);
}

directions      ( tan1 tan2 normal );

useHexTopology  true;
geometricCut    false;
writeMesh       false;
"""


POROUS = """%s
{
    type            explicitPorositySource;
    selectionMode   cellZone;
    cellZone        %s;

    explicitPorositySourceCoeffs
    {
        type            DarcyForchheimer;
        d               (%g %g %g);   // 점성저항 1/alpha (1/m2)
        f               (%g %g %g);   // 관성저항 C2 (1/m)

        coordinateSystem
        {
            origin  (0 0 0);
            e1      (1 0 0);
            e2      (0 1 0);
        }
    }
}

"""


def fv_options(zones, canopy=()):
    """온도 제한(템플릿 유지) + 팬 추력 + 캐노피 다공체 저항."""
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
    for z in canopy:
        nm = z["id"].lower()
        s += POROUS % (nm, nm, z["d_1_m2"], z["d_1_m2"], z["d_1_m2"],
                       z["f_1_m"], z["f_1_m"], z["f_1_m"])
    return s


TURBULENCE = {
    # 이름: (OpenFOAM RAS 모델, 왜 이 모델인가)
    "standard": ("kEpsilon",
                 "기준선. vane25 에서 쓰던 것을 그대로 물려받았다"),
    "rng": ("RNGkEpsilon",
            "제트 확산과 곡률·회전 흐름에서 표준형보다 낫다고 보고된 변형"),
    "realizable": ("realizableKE",
                   "제트의 퍼짐을 표준형보다 잘 맞춘다고 보고된 변형"),
}


def turbulence(name):
    """난류 모델 파일. 기본은 기준선(kEpsilon) 이다.

    표준 k-epsilon 은 제트가 퍼지는 모양과 부력 효과를 실제보다 부드럽게
    만드는 경향이 있다고 알려져 있다. 하필 우리가 보려는 것이 그 둘이다.
    그렇다고 30 케이스를 모두 다른 모델로 다시 돌릴 수는 없으므로,
    기준선은 그대로 두고 대표·극단 케이스 몇 개만 바꿔 돌려
    **케이스 사이의 순위가 유지되는지**만 확인한다.

    kOmegaSST 는 넣지 않았다. 벽 근처 격자를 따로 짜야 공정한 비교가 되는데
    지금 격자로 그대로 돌리면 모델을 비교한 것이 아니라 격자를 비교한 것이 된다.
    """
    model, why = TURBULENCE[name]
    return (head("dictionary", "turbulenceProperties") +
            "// %s — %s\n\nsimulationType  RAS;\n\n"
            "RAS\n{\n    model           %s;\n    turbulence      on;\n"
            "    printCoeffs     on;\n}\n" % (name, why, model))


def fan_flux(zones, planes, write_s, probe_m=0.30, halfw=0.35):
    """유량 검산용 함수오브젝트. 팬 하류와 캐노피 판정면을 지나는 유량(m3/s).

    팬이 내보낸 풍량과 견주면 바람이 어디까지 갔는지 알 수 있다. 하류가 더 크면
    주위 공기를 끌고 간 것(유인)이고, 캐노피 쪽이 작으면 도중에 새는 것이다.

    `areaNormalIntegrate` 는 면을 지나는 U 의 법선 성분을 면적분한다. 곧 m3/s 다.
    팬 하류면은 축에서 halfw 만큼만 잘라 제트만 본다. 방 전체를 재면 되돌아오는
    순환류가 섞여 의미가 없어진다.
    """
    out = []
    for z in zones:
        c, d = z["centre_cfd_m"], z["dir_unit"]
        p = [c[i] + d[i] * probe_m for i in range(3)]
        out.append("""    fanflux_%s
    {
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    adjustableRunTime;
        writeInterval   %g;
        writeFields     false;
        regionType      sampledSurface;
        sampledSurfaceDict
        {
            type        plane;
            planeType   pointAndNormal;
            pointAndNormalDict { point (%.4f %.4f %.4f); normal (%.4f %.4f %.4f); }
            interpolate true;
            bounds      (%.4f %.4f %.4f) (%.4f %.4f %.4f);
        }
        operation       areaNormalIntegrate;
        fields          (U);
    }""" % (z["id"].lower(), write_s, p[0], p[1], p[2], d[0], d[1], d[2],
            p[0] - halfw, p[1] - halfw, p[2] - halfw,
            p[0] + halfw, p[1] + halfw, p[2] + halfw))

    for pl in planes:
        y0, y1 = pl["y_range_m"]
        out.append("""    canopyflux_%s
    {
        type            surfaceFieldValue;
        libs            (fieldFunctionObjects);
        writeControl    adjustableRunTime;
        writeInterval   %g;
        writeFields     false;
        regionType      sampledSurface;
        sampledSurfaceDict
        {
            type        plane;
            planeType   pointAndNormal;
            pointAndNormalDict { point (0 %g %g); normal (0 0 1); }
            interpolate true;
        }
        operation       areaNormalIntegrate;
        fields          (U);
    }""" % (pl["name"], write_s, (y0 + y1) / 2.0, pl["z_cfd_m"]))
    return "\n".join(out)


def control_dict(end_s, write_s, planes, zones=()):
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
startFrom       latestTime;   // 중단돼도 마지막 저장 시점부터 이어간다
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

%s
}
""" % (end_s, write_s, write_s, "\n".join(surf), fan_flux(zones, planes, write_s)))


def allrun(np_, with_rack):
    rack = """
runApp topoSet -dict system/topoSetDict.rack
runApp subsetMesh keep -patch rackWalls -overwrite
""" if with_rack else "\n"
    return """#!/bin/bash
# 케이스 하나를 끝까지 돌린다. 컨테이너 안에서 실행된다.
# 이미 돌던 케이스면 격자·분할을 건너뛰고 마지막 저장 시점부터 이어간다.
cd "${0%%/*}" || exit 1
set -e
runApp(){ echo "--- $* ---"; "$@" > log."$1" 2>&1 || { tail -20 log."$1"; exit 1; }; }

resume=no
if [ -d processor0 ] && [ -n "$(ls -d processor0/[1-9]* 2>/dev/null | head -1)" ]; then
    resume=yes
    echo "--- 이어서 시작 (마지막 저장 시점부터) ---"
fi

if [ "$resume" = no ]; then
    runApp blockMesh
    runApp topoSet -dict system/topoSetDict.ac
    runApp createPatch -overwrite
%s
    runApp topoSet -dict system/topoSetDict.refine
    runApp refineMesh -dict system/refineMeshDict -overwrite
    runApp checkMesh -constant
    runApp topoSet -dict system/topoSetDict.fans
    # 비었을 때만이 아니라 줄어들었을 때도 잡는다. 세분이 셀 번호를 다시 매기므로
    # 순서가 어긋나면 셀존이 조용히 작아진다 — 그래도 계산은 끝까지 돈다.
    small=$(awk '/cellZoneSet .* now size/ { if ($NF < 8) print $2" "$NF }' log.topoSet)
    if [ -n "$small" ]; then
        echo '팬 셀 영역이 너무 작다 (8셀 미만):'
        echo "$small"
        echo 'refineMesh 가 topoSet.fans 앞에서 돌았는지, zone_box 가 세분 격자 기준인지 볼 것.'
        exit 1
    fi
    rm -rf 0 && cp -r 0.orig 0
    runApp decomposePar -force
fi

mpirun --use-hwthread-cpus -np %d buoyantPimpleFoam -parallel >> log.run 2>&1
runApp reconstructPar -latestTime
echo DONE
""" % (rack, np_)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="1-10")
    ap.add_argument("--end", type=float, default=600.0, help="물리 시간 (초)")
    ap.add_argument("--write", type=float, default=30.0)
    ap.add_argument("--np", type=int, default=12)
    ap.add_argument("--repo", default=REPO_DEFAULT, help="fan_params.json 이 있는 저장소")
    ap.add_argument("--template", default=TEMPLATE_DEFAULT, help="복사해 올 기존 OpenFOAM 케이스")
    ap.add_argument("--out", default=OUT_DEFAULT, help="케이스를 펼칠 폴더")
    ap.add_argument("--canopy", default="on", choices=("on", "off"),
                    help="작물층을 다공체로 둘지. off 는 빈 공간 — 순위 비교용")
    ap.add_argument("--turbulence", default="standard", choices=sorted(TURBULENCE),
                    help="난류 모델. 기본은 기준선(kEpsilon). 민감도 확인용으로만 바꾼다")
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
        rid = (c["run_id"]
               + ("" if a.turbulence == "standard" else "_" + a.turbulence)
               + ("" if a.canopy == "on" else "_nocanopy"))
        d = os.path.join(a.out, rid)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(os.path.join(d, "system"))
        # 템플릿 복사
        shutil.copytree(os.path.join(a.template, "0.orig"), os.path.join(d, "0.orig"))
        os.makedirs(os.path.join(d, "constant"))
        for f in ("g", "thermophysicalProperties"):
            shutil.copy2(os.path.join(a.template, "constant", f), os.path.join(d, "constant", f))
        open(os.path.join(d, "constant", "turbulenceProperties"), "w",
             encoding="utf-8").write(turbulence(a.turbulence))
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
        canopy = (spec["canopy"]["zones"] if a.canopy == "on" else [])
        open(os.path.join(d, "system", "topoSetDict.refine"), "w", encoding="utf-8").write(
            topo_refine(spec["refine"]))
        open(os.path.join(d, "system", "refineMeshDict"), "w", encoding="utf-8").write(
            refine_mesh_dict())
        open(os.path.join(d, "system", "topoSetDict.fans"), "w", encoding="utf-8").write(
            topo_fans(zones, canopy))
        open(os.path.join(d, "system", "fvOptions"), "w", encoding="utf-8").write(
            fv_options(zones, canopy))
        open(os.path.join(d, "system", "controlDict"), "w", encoding="utf-8").write(
            control_dict(a.end, a.write, spec["judge_planes"], zones))
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
                "rack": with_rack, "endTime_s": a.end, "np": a.np,
                "run_id": rid,
                "canopy_porous": a.canopy == "on",
                "turbulence": TURBULENCE[a.turbulence][0],
                "turbulence_why": TURBULENCE[a.turbulence][1]}
        json.dump(meta, open(os.path.join(d, "case.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        made.append((c["no"], rid, len(zones), with_rack))

    for no, rid, nz, rk in made:
        print("  %2d  %-8s 팬존 %2d  재배단 %s" % (no, rid, nz, "있음" if rk else "없음"))
    print("케이스 %d개 -> %s (물리 %gs, %d분할)" % (len(made), a.out, a.end, a.np))


if __name__ == "__main__":
    main()
