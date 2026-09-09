#!/bin/sh
# 사용: sh ue/cap.sh "x,y,z,pitch,yaw" 출력이름 [fov]
cd "$(dirname "$0")/.."
python - "$1" "$2" "${3:-60}" <<'PY'
import json, os, sys
cam = [float(t) for t in sys.argv[1].split(",")]
out = r"C:\Users\hunvr\Desktop\smartfarm-cfd\out\ue_shots" + "\\" + sys.argv[2] + ".png"
json.dump({"cam": cam, "out": out, "fov": float(sys.argv[3])},
          open("data/_cap.json", "w", encoding="utf-8"))
PY
py ue/ue_exec.py -f ue/sf_capture.py 2>&1 | grep -aiE "SF_CAP|Error" | head -5
