#!/usr/bin/env bash
# fan-study 케이스를 차례로 돌린다. (WSL 에서 실행)
#
#   bash src/run_foam_cases.sh 1 10          1~10번 케이스
#   CPUS=19 bash src/run_foam_cases.sh 1 10      (기본은 코어의 80 %)
#
# CPU 상한은 --cpus 로 건다. 16코어 머신에서 12 면 75 % 다.
# 케이스마다 벽시계 시간을 times.csv 에 적는다.
set -uo pipefail

LO=${1:-1}; HI=${2:-10}
# 코어는 기계에 맞춘다 - 기본 80 %. 나머지는 사람이 쓸 몫으로 남긴다.
# 맥에는 nproc 이 없다. sysctl 로 받는다.
CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 8)
CPUS=${CPUS:-$(( CORES * 8 / 10 ))}

IMG=${FOAM_IMAGE:-opencfd/openfoam-default:2512}
PROJECT=${FOAM_PROJECT:-$HOME/smartfarm-cfd}
ROOT="$PROJECT/cases/fan-study"
CSV="$ROOT/times.csv"

# 파이썬을 찾는다. 윈도우의 python3 은 마이크로소프트 스토어 더미인 경우가 있다 -
# command -v 로는 잡히는데 실행하면 "Python" 한 줄만 찍고 끝난다. 실제로 돌려 본다.
PY=""
for c in py python3 python; do
    if "$c" -c "import sys" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || echo "경고: 파이썬을 못 찾았다. 케이스별 검산을 건너뛴다." >&2

# 윈도우(Git Bash)에서는 도커가 POSIX 경로를 못 받는다. 윈도우 경로로 바꾸고
# MSYS 의 경로 변환을 끈다. 바인드 마운트에 uid 매핑이 없어 --user 도 못 쓰는데,
# 그러면 컨테이너가 root 로 돌아 mpirun 이 거부한다. 환경변수로 풀어 준다.
MOUNT="$PROJECT"
EXTRA=(--user "$(id -u):$(id -g)")
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        MOUNT=$(cygpath -w "$PROJECT")
        export MSYS_NO_PATHCONV=1
        EXTRA=(-e OMPI_ALLOW_RUN_AS_ROOT=1 -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1)
        ;;
    Darwin)
        # opencfd 이미지는 linux/arm64 도 낸다. 애플 실리콘에서 네이티브로 돈다.
        # --platform 을 강제하면 오히려 에뮬레이션으로 끌려가므로 붙이지 않는다.
        ;;
esac

[ -f "$CSV" ] || echo "no,run_id,start,wall_s,status" > "$CSV"

for d in "$ROOT"/*/; do
    rid=$(basename "$d")
    no=${rid%%_*}; no=$((10#$no))
    [ "$no" -ge "$LO" ] && [ "$no" -le "$HI" ] || continue
    if [ -f "$d/DONE" ]; then echo "[$rid] 이미 끝남, 건너뜀"; continue; fi

    echo "=== [$rid] 시작 $(date '+%H:%M:%S') · CPU 상한 ${CPUS}/${CORES} ==="
    t0=$(date +%s)
    docker run --rm "${EXTRA[@]}" --cpus="$CPUS" \
        -e HOME=/data -e FOAM_WORKDIR="/data/cases/fan-study/$rid" \
        -v "$MOUNT:/data" "$IMG" \
        bash -lc 'cd "$FOAM_WORKDIR" || exit 1; source /usr/lib/openfoam/openfoam*/etc/bashrc; ./Allrun' \
        > "$d/log.allrun" 2>&1
    rc=$?
    t1=$(date +%s); dt=$((t1 - t0))
    if [ $rc -eq 0 ]; then touch "$d/DONE"; st=ok; else st="fail($rc)"; fi

    # 팬이 제대로 들어갔는지, 그 바람이 캐노피까지 갔는지 검산한다.
    # 계산이 정상 종료해도 팬이 빠진 채 돌 수 있다(E-001). 케이스마다 남긴다.
    if [ -n "$PY" ]; then
        (cd "${SF_REPO:-$PWD}" && "$PY" -m src.check_fan --run "$d") \
            > "$d/check_fan.txt" 2>&1 || st="$st+검산실패"
        sed -n '1,40p' "$d/check_fan.txt"
    fi
    echo "$no,$rid,$(date -r $t0 '+%F %T' 2>/dev/null || date -d @$t0 '+%F %T'),$dt,$st" >> "$CSV"
    printf '=== [%s] %s · %d분 %d초 ===\n' "$rid" "$st" $((dt / 60)) $((dt % 60))
    [ $rc -eq 0 ] || { echo "--- 실패 꼬리 ---"; tail -25 "$d/log.allrun"; }
done

echo "--- 요약 ---"; column -s, -t "$CSV" 2>/dev/null || cat "$CSV"
