"""Prepare the 18-fan schedule and launch its single CFD validation run."""
import argparse
import base64
import csv
import hashlib
import io
import json
import lzma
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
IMAGE = "opencfd/openfoam-default@sha256:33fb575aa9980d2bc42fd58c75ae698c489293ba30c991380fe3f899c622f319"
BUNDLE_SHA = "0ba10f02c78a0fade2c537deceeac13b38465cf70583c70e0bcef7f71c7053b5"
COLS = [f"fan{i}_CMM" for i in range(1, 8)] + ["left_CMM", "right_CMM"]


def prepare(folder):
    doc = (HERE.parent / "SmartFarm_CFD_AI_149426_600s.md").read_text(encoding="utf-8-sig")
    payload = re.search(r"(?ms)^```smartfarm-bundle\s*\n(.*?)^```", doc)
    packed = base64.b64decode("".join(payload[1].split()), validate=True)
    if hashlib.sha256(packed).hexdigest() != BUNDLE_SHA:
        raise ValueError("Wrong 4-case baseline package")
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(packed))) as archive:
        archive.extractall(folder)
    case = folder / "02_ac_all"
    setup = json.loads((case / "case.json").read_text(encoding="utf-8"))
    base = (case / "system/fvOptions").read_text(encoding="utf-8")
    header = base[:base.index("fan_t0_front1")]
    canopy = base[base.index("canopy_t0"):]
    mesh = (folder / "common/system/topoSetDict.fans").read_text(encoding="utf-8")
    geom = []
    fan_lists = []
    for tier, z in enumerate((0.7, 1.5)):
        tier_fans = [(f["id"], f["dir_unit"]) for f in setup["fan_zones"] if f["tier"] == tier]
        if [name for name, _ in tier_fans] != [f"fan_t{tier}_{pos}" for pos in
                ("front1","front2","front3","front4","back1","back2","back3")]:
            raise ValueError("Unexpected baseline fan ordering")
        for side, x, sign in (("left", -1.2, 1), ("right", 1.2, -1)):
            name = f"fan_t{tier}_{side}"
            tier_fans.append((name, [sign, 0, 0]))
            # Deposit momentum in the first 25 mm of resolved canopy-side cells.
            geom.append(f"{{ name {name}; type cellSet; action new; source cylinderToCell; "
                        f"p1 ({x} 2 {z}); p2 ({x + .025*sign} 2 {z}); radius .046; }}\n"
                        f"{{ name {name}; type cellZoneSet; action new; source setToCellZone; set {name}; }}")
        fan_lists.append(tier_fans)
    (folder/"sideZones").write_text(mesh[:mesh.index("actions")]+"actions\n(\n"+"\n".join(geom)+"\n);\n",encoding="utf-8")
    with (HERE/"schedule.csv").open(encoding="utf-8-sig",newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 20:
        raise ValueError("Expected two tiers x ten intervals")
    for minute in range(10):
        parts = [header]
        for tier, label in enumerate(("lower","upper")):
            row = rows[minute*2+tier]
            if (int(row["start_s"]),int(row["end_s"]),row["tier"]) != (60*minute,60*(minute+1),label):
                raise ValueError("Unexpected tier or time interval")
            for col,(name,direction) in zip(COLS,fan_lists[tier]):
                q = float(row[col])
                if not 0 <= q <= 2.1:
                    raise ValueError(f"Invalid CMM for {name}")
                force = setup["per_fan_thrust_N"]*(q/setup["per_fan_CMM"])**2
                vector = " ".join(f"{v*force:.10g}" for v in direction)
                parts.append(f"{name}\n{{ type vectorSemiImplicitSource; selectionMode cellZone; "
                             f"cellZone {name}; volumeMode absolute; sources {{ U (({vector}) 0); }} }}\n")
        (folder/f"options-{60*(minute+1)}").write_text("\n".join(parts+[canopy]),encoding="utf-8")
    for name in ("run.sh","schedule.csv"):
        (folder/name).write_bytes((HERE/name).read_bytes().replace(b"\r\n",b"\n"))
    print("Validated 10 intervals, 18 fan commands per interval and baseline checksum.",flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["check","start"])
    parser.add_argument("--ranks",type=int,default=1)
    parser.add_argument("--output",type=Path,default=Path.home()/"SmartFarm18-validation")
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("--ranks must be positive")
    if args.action == "check":
        with tempfile.TemporaryDirectory() as tmp:
            prepare(Path(tmp))
        return
    subprocess.run(["docker","info"],stdout=subprocess.DEVNULL,check=True)
    root = args.output.resolve()
    root.mkdir(parents=True,exist_ok=False)
    study,results=root/"input",root/"results"
    study.mkdir();results.mkdir();prepare(study)
    token=hashlib.sha256(str(root).encode()).hexdigest()[:10]
    name="sf18-"+token
    subprocess.run(["docker","run","-d","--platform","linux/amd64","--name",name,
                    "--mount",f"type=bind,src={study},dst=/study,readonly",
                    "--mount",f"type=bind,src={results},dst=/out",
                    "--mount",f"type=volume,src={name}-work,dst=/work",
                    IMAGE,"bash","/study/run.sh",str(args.ranks)],check=True)
    print(f"docker logs -f {name}\nResults: {results}\nPersistent case volume: {name}-work")

if __name__ == "__main__":
    main()
