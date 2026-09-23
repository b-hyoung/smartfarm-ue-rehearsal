"""G7(에어컨 위치) 케이스의 취출·리턴 faceSet 상자를 격자에 맞춰 고른다.

문제: 템플릿 격자는 안쪽 블록(x ±1.8, y 0~2.9)만 직교 0.1 m 이고 바깥 블록은 반타원을 따라
비스듬하다. 에어컨을 옮기면 천장 면 중심이 상자(폭 0.06 m)에 안 들어가 취출면이 3~5 장,
심하면 0 장이 된다(기준 위치는 6 장, 리턴 36 장). flowRateInletVelocity 라 풍량은 면 수와
무관하게 맞지만 면이 0 장이면 그 슬롯의 급기가 통째로 사라진다.

해결: 슬롯마다 얇은 축 두께를, 리턴은 배율을 여러 개 시험해 topoSet 으로 면 수를 세고
목표(6 / 36)에 가장 가까운 상자를 고른다. 같으면 작은 상자. 고른 상자로 각 케이스의
system/topoSetDict.ac 를 다시 쓴다. 솔버는 돌리지 않는다.

    python3 ac_snap.py                 # WSL cfd 사용자
"""
import json, os, subprocess

REPO = "/mnt/c/Users/jica/source/repos/smartfarm-ue-rehearsal"
PROJECT = os.path.expanduser("~/smartfarm-cfd")
ROOT = os.path.join(PROJECT, "cases", "fan-study")
MESH_CASE = "25_A1"                                  # blockMesh 격자를 빌릴 케이스 (천장은 세분 안 됨)
SLOTS = ("inletXp", "inletXm", "inletYp", "inletYm")
TARGET = {"inletXp": 6, "inletXm": 6, "inletYp": 6, "inletYm": 6, "return": 36}
THICK = (0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18)   # 슬롯 얇은 축 두께 후보
SCALE = (1.0, 1.1, 1.2, 1.3, 1.4, 1.5)               # 리턴 상자 배율 후보 (x·y 둘 다)

spec = json.load(open(os.path.join(REPO, "data", "fan_params.json"), encoding="utf-8"))
cases = [c for c in spec["cases"] if c["group"].startswith("G7")]


def slot_box(b, t):
    mn, mx = list(b["min"]), list(b["max"])
    for i in (0, 1):
        if mx[i] - mn[i] < 0.3:                      # 얇은 축만
            c = 0.5 * (mn[i] + mx[i]); mn[i], mx[i] = c - t / 2, c + t / 2
    return mn, mx


def ret_box(b, s):
    mn, mx = list(b["min"]), list(b["max"])
    for i in (0, 1):
        c = 0.5 * (mn[i] + mx[i]); h = 0.5 * (mx[i] - mn[i]) * s
        mn[i], mx[i] = c - h, c + h
    return mn, mx


def act(name, mn, mx):
    return ("    { name %s; type faceSet; action new; source boxToFace; box (%g %g %g) (%g %g %g); }"
            % (name, mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]))


def run_toposet(acts, tag):
    txt = ("FoamFile { version 2.0; format ascii; class dictionary; object topoSetDict; }\n"
           "actions\n(\n" + "\n".join(acts) + "\n);\n")
    d = os.path.join(ROOT, MESH_CASE)
    open(os.path.join(d, "system", "topoSetDict." + tag), "w", newline="\n").write(txt)
    cmd = ["docker", "run", "--rm", "--user", "%d:%d" % (os.getuid(), os.getgid()), "-e", "HOME=/data",
           "-v", "%s:/data" % PROJECT, "opencfd/openfoam-default:2512", "bash", "-c",
           "cd /data/cases/fan-study/%s && source /usr/lib/openfoam/openfoam*/etc/bashrc && "
           "topoSet -dict system/topoSetDict.%s > log.topoSet.%s 2>&1; echo rc=$?" % (MESH_CASE, tag, tag)]
    print(tag, subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
    sizes = {}
    for line in open(os.path.join(d, "log.topoSet." + tag), encoding="utf-8", errors="replace"):
        if "faceSet" in line and "now size" in line:
            p = line.split(); sizes[p[1]] = int(p[-1])
    return sizes


# 1) 후보 전부 한 번에 센다
acts, cand = [], {}
for c in cases:
    boxes = c["ac"]["topoSet_boxes_cfd_m"]
    for nm in SLOTS:
        for t in THICK:
            key = "s_%s_%s_%02d" % (c["run_id"], nm, round(t * 100))
            mn, mx = slot_box(boxes[nm], t); cand[key] = (mn, mx); acts.append(act(key, mn, mx))
    for s in SCALE:
        key = "s_%s_return_%02d" % (c["run_id"], round(s * 10))
        mn, mx = ret_box(boxes["return"], s); cand[key] = (mn, mx); acts.append(act(key, mn, mx))
sizes = run_toposet(acts, "acsnap")

# 2) 슬롯마다 목표에 가장 가까운(같으면 작은) 상자를 고른다
chosen, report = {}, []
for c in cases:
    rid = c["run_id"]; chosen[rid] = {}; row = {}
    for nm in SLOTS:
        best = None
        for t in THICK:
            key = "s_%s_%s_%02d" % (rid, nm, round(t * 100)); n = sizes.get(key, -1)
            score = (abs(n - TARGET[nm]), t)
            if best is None or score < best[0]:
                best = (score, key, n, "t=%.2f" % t)
        chosen[rid][nm] = {"min": cand[best[1]][0], "max": cand[best[1]][1], "faces": best[2], "pick": best[3]}
        row[nm] = "%d(%s)" % (best[2], best[3])
    best = None
    for s in SCALE:
        key = "s_%s_return_%02d" % (rid, round(s * 10)); n = sizes.get(key, -1)
        score = (abs(n - TARGET["return"]), s)
        if best is None or score < best[0]:
            best = (score, key, n, "x%.1f" % s)
    chosen[rid]["return"] = {"min": cand[best[1]][0], "max": cand[best[1]][1], "faces": best[2], "pick": best[3]}
    row["return"] = "%d(%s)" % (best[2], best[3])
    report.append((rid, tuple(c["ac"]["centre_ue_m"][:2]), row))

# 3) 고른 상자로 케이스의 topoSetDict.ac 를 다시 쓰고, 같은 격자에서 한 번 더 검산한다
HEAD = ("FoamFile\n{\n    version     2.0;\n    format      ascii;\n    class       dictionary;\n"
        "    object      topoSetDict;\n}\n\n")
verify = []
for c in cases:
    rid = c["run_id"]; d = os.path.join(ROOT, rid)
    if not os.path.isdir(d):
        print("케이스 폴더 없음, 건너뜀:", rid); continue
    acts = []
    for nm in SLOTS + ("return",):
        b = chosen[rid][nm]
        acts.append("    {\n        name    %s;\n        type    faceSet;\n        action  new;\n"
                    "        source  boxToFace;\n        box     (%g %g %g) (%g %g %g);   // %s -> %d faces\n    }"
                    % (nm, *b["min"], *b["max"], b["pick"], b["faces"]))
        verify.append(act("v_%s_%s" % (rid, nm), b["min"], b["max"]))
    open(os.path.join(d, "system", "topoSetDict.ac"), "w", newline="\n").write(
        HEAD + "// 격자에 맞춰 고른 상자 (scripts/ac_snap.py). 목표: 취출 6 장, 리턴 36 장.\n"
        "actions\n(\n" + "\n".join(acts) + "\n);\n")
    meta_p = os.path.join(d, "case.json")
    if os.path.isfile(meta_p):
        meta = json.load(open(meta_p, encoding="utf-8"))
        meta["ac_boxes_snapped"] = {nm: chosen[rid][nm] for nm in SLOTS + ("return",)}
        json.dump(meta, open(meta_p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
vs = run_toposet(verify, "acverify")

json.dump(chosen, open(os.path.join(ROOT, "ac_boxes_snapped.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)

print("\n%-7s %-11s %-12s %-12s %-12s %-12s %-12s" % ("case", "ac_ue", *SLOTS, "return"))
for rid, ue, row in report:
    print("%-7s (%.1f,%.1f)   %-12s %-12s %-12s %-12s %-12s" % (rid, ue[0], ue[1], *[row[n] for n in SLOTS + ("return",)]))
print("\n검산(다시 쓴 topoSetDict.ac 로 센 면 수):")
for c in cases:
    rid = c["run_id"]
    print("  %-7s %s" % (rid, " ".join("%s=%d" % (nm, vs.get("v_%s_%s" % (rid, nm), -1)) for nm in SLOTS + ("return",))))
print("\n기준(템플릿 위치): 취출 6 6 6 6, 리턴 36")
