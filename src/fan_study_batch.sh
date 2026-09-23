#!/bin/bash
# fan-study 케이스를 컨테이너 안에서 차례로 돌린다.
#
# 호스트에서 분리(detached) 컨테이너로 띄워 쓴다. 도커 데몬이 관리하므로
# WSL 세션이나 터미널이 끊겨도 완주한다.
#
#   docker run -d --name fanstudy --cpus=12 \
#     --user "$(id -u):$(id -g)" -e HOME=/data -v $HOME/smartfarm-cfd:/data \
#     opencfd/openfoam-default:2512 \
#     bash -lc 'source /usr/lib/openfoam/openfoam*/etc/bashrc; bash /data/scripts/fan_study_batch.sh 1 10'
#
# CPU 상한은 컨테이너 --cpus 로 건다. 16코어에서 12 면 75 % 다.
set -u

LO=${1:-1}; HI=${2:-10}
ROOT=/data/cases/fan-study
CSV="$ROOT/times.csv"
[ -f "$CSV" ] || echo "no,run_id,start,wall_s,status" > "$CSV"

for d in "$ROOT"/*/; do
    rid=$(basename "$d")
    case "$rid" in [0-9][0-9]_*) ;; *) continue ;; esac
    no=$((10#${rid%%_*}))
    [ "$no" -ge "$LO" ] && [ "$no" -le "$HI" ] || continue
    [ -f "$d/DONE" ] && { echo "[$rid] 이미 끝남"; continue; }

    echo "=== [$rid] 시작 $(date '+%F %T') ==="
    t0=$(date +%s)
    ( cd "$d" && ./Allrun ) > "$d/log.allrun" 2>&1
    rc=$?
    dt=$(( $(date +%s) - t0 ))
    if [ $rc -eq 0 ]; then touch "$d/DONE"; st=ok; else st="fail($rc)"; fi
    echo "$no,$rid,$(date -d @$t0 '+%F %T'),$dt,$st" >> "$CSV"
    printf '=== [%s] %s · %d분 %d초 ===\n' "$rid" "$st" $((dt / 60)) $((dt % 60))
    [ $rc -eq 0 ] || tail -20 "$d/log.allrun"
done
echo "=== 배치 끝 $(date '+%F %T') ==="
cat "$CSV"
