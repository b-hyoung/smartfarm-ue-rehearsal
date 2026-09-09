#!/bin/sh
# 사용: sh ue/nia.sh <frame> "<spawnX,spawnY,spawnZ>" <intensity>
cd "$(dirname "$0")/.."
python - "$1" "$2" "$3" <<'PY'
import json, sys
json.dump({"frame": int(sys.argv[1]),
           "spawn": [float(t) for t in sys.argv[2].split(",")],
           "intensity": float(sys.argv[3])},
          open("data/_nia.json", "w", encoding="utf-8"))
PY
py ue/ue_exec.py -f ue/sf_niagara.py 2>&1 | grep -aiE "SF_NIA|Error" | head -4
