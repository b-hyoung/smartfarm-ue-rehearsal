# -*- coding: utf-8 -*-
"""판정면 raw -> 미리보기 웹의 데이터(scene.js). 300~450 초 시간평균, 49x17 격자.

web/fan-wind.html 은 이 scene.js 와 web/_wind/app.js 를 한 파일로 합쳐 둔 것이다.
케이스가 늘면

    py -m src.make_wind_page            # scene.js 다시 만들기
    py -m src.make_wind_page --build    # web/fan-wind.html 까지 다시 합치기

본 점수는 베드 전체를 쓴다 — src/judge.py 와 같은 범위라야 docs/FAN-RESULTS.md 와
어긋나지 않는다. 테두리를 뺀 안쪽 값은 tiers[*].inner 에 보조로만 넣는다.
"""
import io, json, math, os, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\Users\ACE\smartfarm-cfd\cases\fan-study"
REPO = r"C:\Users\ACE\Desktop\smartfarm-ue-rehearsal"
WEB  = os.path.join(REPO, "web")
OUT  = os.path.join(WEB, "_wind", "scene.js")
NX, NY = 49, 17
X0, X1, Y0, Y1 = -1.2, 1.2, 1.6, 2.4
MARGIN = 0.10          # 보조 지표: 프레임 자리인 베드 테두리를 잘라 낸 안쪽
TIMES = range(300, 451, 30)


def grid(case, plane):
    """스냅샷마다 격자로 묶고, 격자칸별 시간평균을 낸다."""
    acc, cnt = [[0.0] * NX for _ in range(NY)], [[0] * NX for _ in range(NY)]
    snaps = 0
    for t in TIMES:
        f = "%s/%s/postProcessing/canopy/%d/U_%s.raw" % (ROOT, case, t, plane)
        if not os.path.exists(f):
            continue
        snaps += 1
        for line in open(f, encoding="utf-8", errors="replace"):
            if not line.strip() or line[0] == "#":
                continue
            p = line.split()
            if len(p) < 6:
                continue
            x, y = float(p[0]), float(p[1])
            i = int(round((x - X0) / (X1 - X0) * (NX - 1)))
            j = int(round((y - Y0) / (Y1 - Y0) * (NY - 1)))
            if not (0 <= i < NX and 0 <= j < NY):
                continue
            acc[j][i] += math.sqrt(float(p[3]) ** 2 + float(p[4]) ** 2 + float(p[5]) ** 2)
            cnt[j][i] += 1
    if not snaps:
        return None, 0
    return [[round(acc[j][i] / cnt[j][i], 3) if cnt[j][i] else None
             for i in range(NX)] for j in range(NY)], snaps


def score(g, margin=0.0):
    """분위수·고르기. margin 을 주면 그만큼 베드 테두리를 잘라 낸 안쪽만 본다.

    기본값 0 은 src/judge.py 와 같은 범위다 — 화면 숫자가 docs/FAN-RESULTS.md 와
    어긋나면 안 되므로 본 점수는 반드시 이쪽을 쓴다. 테두리를 뺀 값은 보조로만 쓴다.
    """
    mi = int(round(margin / (X1 - X0) * (NX - 1)))
    mj = int(round(margin / (Y1 - Y0) * (NY - 1)))
    v = sorted(g[j][i] for j in range(mj, NY - mj) for i in range(mi, NX - mi)
               if g[j][i] is not None)
    if not v:
        return None
    n = len(v)
    q = lambda t: v[int((n - 1) * t / 100)]
    mu = sum(v) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in v) / n)
    lo = sum(1 for x in v if x < 0.3)
    hi = sum(1 for x in v if x > 1.0)
    return {"p10": round(q(10), 3), "p50": round(q(50), 3), "p90": round(q(90), 3),
            "mean": round(mu, 3), "cv": round(sd / mu * 100),
            "lo": round(lo / n * 100), "hi": round(hi / n * 100),
            "band": round((n - lo - hi) / n * 100)}


P = json.load(open(os.path.join(REPO, "data", "fan_params.json"), encoding="utf-8"))
meta = {c["run_id"]: c for c in P["cases"]}
BED_W, BED_D = 2.40, 0.80

out = {}
for case in sorted(d for d in os.listdir(ROOT) if d[0].isdigit()):
    m = meta.get(case, {})
    tiers, snaps = {}, 0
    for tk, tag in (("t0", "tier0"), ("t1", "tier1")):
        g, s = grid(case, tag + "_canopy_mid")
        if g is None:
            break
        snaps = max(snaps, s)
        full, inner = score(g) or {}, score(g, MARGIN) or {}
        tiers[tk] = dict(full, nx=NX, ny=NY, x=[X0, X1], y=[Y0, Y1], g=g,
                         inner={k: inner[k] for k in ("p10", "p50", "p90", "band", "cv")},
                         margin=MARGIN)
    if len(tiers) < 2:
        print("건너뜀", case)
        continue
    n = m.get("n_per_side") or 0
    layout = m.get("layout", "none")
    if layout == "top":
        k = max(2, n * 2)
        fans = [{"x": round(-BED_W / 2 + BED_W * (i + 0.5) / k, 3), "y": 2.0,
                 "dz": 0.55, "dir": [0, 0, -1]} for i in range(k)]
    elif layout == "none" or not m.get("per_fan_CMM"):
        fans = []
    else:
        h = m.get("fan_height_above_bed_m", 0.18)
        tl = math.radians(m.get("tilt_deg", 0.0))
        ys = [round(2.0 + BED_D * ((i + 0.5) / n - 0.5), 3) for i in range(n)]
        fans = [{"x": sx * (BED_W / 2 + 0.10), "y": fy, "dz": h,
                 "dir": [round(-sx * math.cos(tl), 3), 0, round(-math.sin(tl), 3)]}
                for fy in ys for sx in (-1, 1)]
    out[case] = {
        "label": (m.get("purpose") or "").strip() or "기준선",
        "group": m.get("group", ""),
        "cmm": m.get("per_fan_CMM", 0) or 0,
        "n": n, "tilt": m.get("tilt_deg", 0.0),
        "h": m.get("fan_height_above_bed_m", 0.18),
        "layout": layout, "fans": fans, "snaps": snaps,
        "ac": (m.get("ac") or {}).get("centre_cfd_m", [0.0, 2.0])[:2],
        "tiers": tiers,
    }
    print("%-8s 장 %d  P10 %.3f  P90 %.3f  고르기 %d%%"
          % (case, snaps, tiers["t0"]["p10"], tiers["t0"]["p90"], tiers["t0"]["cv"]))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("const SCENE = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("\n->", OUT, os.path.getsize(OUT) // 1024, "KB,", len(out), "케이스")


def build_single_file():
    """web/_wind 의 세 파일을 web/fan-wind.html 한 장으로 합친다.

    받는 사람이 클론만 하고 바로 열 수 있어야 해서 한 파일로 둔다.
    three.js 만 CDN 에서 받아 온다 (web/3d.html 과 같은 규약). 못 받으면
    3D 만 접히고 지도·고르기·표는 그대로 보인다 — app.js 의 HAS3D.
    """
    src = os.path.join(WEB, "_wind")
    rd = lambda n: io.open(os.path.join(src, n), encoding="utf-8").read()
    html, scene_js, app_js = rd("index.html"), rd("scene.js"), rd("app.js")
    head = ('<!doctype html>' + chr(10) + '<html lang="ko">' + chr(10) + '<head>' + chr(10) +
            '<meta charset="utf-8">' + chr(10) +
            '<meta name="viewport" content="width=device-width, initial-scale=1">' + chr(10))
    i, j = html.index("<title>"), html.index("</style>") + len("</style>")
    body = head + html[i:j] + chr(10) + "</head>" + chr(10) + "<body>" + chr(10) + html[j:]
    body = body.replace('<script src="./scene.js"></script>',
                        "<script>" + chr(10) + scene_js + "</script>")
    body = body.replace('<script src="./app.js"></script>',
                        "<script>" + chr(10) + app_js + "</script>")
    dst = os.path.join(WEB, "fan-wind.html")
    with io.open(dst, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write(body.rstrip() + chr(10) + "</body>" + chr(10) + "</html>" + chr(10))
    print("->", dst, os.path.getsize(dst) // 1024, "KB")


if "--build" in sys.argv:
    build_single_file()
