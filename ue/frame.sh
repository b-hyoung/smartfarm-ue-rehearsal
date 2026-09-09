#!/bin/sh
# 레벨에 프레임 하나 올리기.   sh ue/frame.sh 7
cd "$(dirname "$0")/.."
python -c "import json,sys; json.dump({'frame':int(sys.argv[1])}, open('data/_nia.json','w'))" "${1:-14}"
py ue/ue_exec.py -f ue/sf_frame.py 2>&1 | grep -aiE "SF_FRAME|Error" | head -3
