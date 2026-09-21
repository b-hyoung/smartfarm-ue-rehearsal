#!/usr/bin/env bash
# fan-study 케이스를 차례로 돌린다. (WSL 에서 실행)
#
#   bash src/run_foam_cases.sh 1 10          1~10번 케이스
#   NP=12 CPUS=12 bash src/run_foam_cases.sh 1 2
#
# CPU 상한은 --cpus 로 건다. 16코어 머신에서 12 면 75 % 다.
# 케이스마다 벽시계 시간을 times.csv 에 적는다.
set -uo pipefail

LO=${1:-1}; HI=${2:-10}
NP=${NP:-12}
CPUS=${CPUS:-12}
IMG=${FOAM_IMAGE:-opencfd/openfoam-default:2512}
PROJECT=${FOAM_PROJECT:-$HOME/smartfarm-cfd}
ROOT="$PROJECT/cases/fan-study"
CSV="$ROOT/times.csv"

[ -f "$CSV" ] || echo "no,run_id,start,wall_s,status" > "$CSV"

for d in "$ROOT"/*/; do
    rid=$(basename "$d")
    no=${rid%%_*}; no=$((10#$no))
    [ "$no" -ge "$LO" ] && [ "$no" -le "$HI" ] || continue
    if [ -f "$d/DONE" ]; then echo "[$rid] 이미 끝남, 건너뜀"; continue; fi

    echo "=== [$rid] 시작 $(date '+%H:%M:%S') · ${NP}분할 · CPU 상한 ${CPUS} ==="
    t0=$(date +%s)
    docker run --rm --user "$(id -u):$(id -g)" --cpus="$CPUS" \
        -e HOME=/data -e FOAM_WORKDIR="/data/cases/fan-study/$rid" \
        -v "$PROJECT:/data" -w "/data/cases/fan-study/$rid" "$IMG" \
        bash -lc 'cd "$FOAM_WORKDIR" || exit 1; source /usr/lib/openfoam/openfoam*/etc/bashrc; ./Allrun' \
        > "$d/log.allrun" 2>&1
    rc=$?
    t1=$(date +%s); dt=$((t1 - t0))
    if [ $rc -eq 0 ]; then touch "$d/DONE"; st=ok; else st="fail($rc)"; fi
    echo "$no,$rid,$(date -d @$t0 '+%F %T'),$dt,$st" >> "$CSV"
    printf '=== [%s] %s · %d분 %d초 ===\n' "$rid" "$st" $((dt / 60)) $((dt % 60))
    [ $rc -eq 0 ] || { echo "--- 실패 꼬리 ---"; tail -25 "$d/log.allrun"; }
done

echo "--- 요약 ---"; column -s, -t "$CSV"
