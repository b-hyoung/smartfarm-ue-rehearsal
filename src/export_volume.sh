#!/usr/bin/env bash
# 끝난 케이스에서 볼륨(방 전체 U·T)을 뽑는다. VDB 만들기 전 단계다.
#
#   bash src/export_volume.sh 05_F3               300~600 초 저장본 전부
#   TIMES=450,600 bash src/export_volume.sh 05_F3 고른 시각만
#
# processor*/ 저장본에서 바로 돌기 때문에 reconstructPar 가 필요 없다.
# 케이스당 몇 분. 결과는 <케이스>/postProcessing/volumeGrid/<시각>/{U,T}_zNNN.raw
set -uo pipefail

RID=${1:?케이스 이름을 달라 (예: 05_F3)}
FROM=${FROM:-300}
IMG=${FOAM_IMAGE:-opencfd/openfoam-default:2512}
PROJECT=${FOAM_PROJECT:-$HOME/smartfarm-cfd}
CASE="$PROJECT/cases/fan-study/$RID"
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

[ -d "$CASE/system" ] || { echo "케이스가 없다: $CASE" >&2; exit 1; }
NP=$(ls -d "$CASE"/processor* 2>/dev/null | wc -l)
[ "$NP" -gt 0 ] || { echo "$RID 에 processor* 가 없다 — 이 컴퓨터에서 돌린 케이스만 된다." >&2; exit 1; }

PY=""
for c in py python3 python; do
    if "$c" -c "import sys" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "파이썬을 못 찾았다." >&2; exit 1; }
"$PY" -m src.make_volume_dict --case "$CASE" || exit 1

# 뽑을 시각. 기본은 FROM 이상 전부.
if [ -n "${TIMES:-}" ]; then
    SEL="-time ${TIMES}"
else
    SEL="-time ${FROM}:"
fi

MOUNT="$PROJECT"
EXTRA=(--user "$(id -u):$(id -g)")
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        MOUNT=$(cygpath -w "$PROJECT")
        export MSYS_NO_PATHCONV=1
        EXTRA=(-e OMPI_ALLOW_RUN_AS_ROOT=1 -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1)
        ;;
esac

echo "=== [$RID] 볼륨 추출 · ${NP} 분할 · ${SEL} ==="
docker run --rm "${EXTRA[@]}" \
    -e HOME=/data -e FOAM_WORKDIR="/data/cases/fan-study/$RID" -e NP="$NP" -e SEL="$SEL" \
    -v "$MOUNT:/data" "$IMG" \
    bash -lc 'cd "$FOAM_WORKDIR" || exit 1
              source /usr/lib/openfoam/openfoam*/etc/bashrc
              # 해가 도는 중에도 뽑을 수 있게 --oversubscribe 를 붙인다.
              # postProcess 는 읽고 자르기만 해 코어를 오래 쥐지 않는다.
              mpirun --oversubscribe -np "$NP" postProcess -parallel -func volumeGrid $SEL 2>&1 | tail -20' \
    > "$CASE/log.volumeGrid" 2>&1
rc=$?
tail -6 "$CASE/log.volumeGrid"
if [ $rc -ne 0 ]; then echo "실패 — $CASE/log.volumeGrid 를 봐라" >&2; exit $rc; fi

echo "--- 나온 시각 ---"
ls "$CASE/postProcessing/volumeGrid" 2>/dev/null | tr '\n' ' '; echo
echo "다음: $PY -m src.volume_frames --case $RID"
