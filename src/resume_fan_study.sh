#!/usr/bin/env bash
# 배치가 끊긴 뒤(정전·재부팅·강제 종료) 다시 이어서 돌린다. WSL 에서 실행한다.
#
#   bash src/resume_fan_study.sh 1 10
#
# 하는 일은 세 가지다.
#   1. 끊긴 흔적(Allrun.new)이 있으면 이어받기용 Allrun 으로 바꿔 넣는다.
#   2. 죽은 컨테이너 껍데기를 치운다.
#   3. 같은 배치를 다시 띄운다. 끝난 케이스(DONE)는 건너뛰고,
#      돌던 케이스는 마지막 저장 시점(30초 간격)부터 이어간다.
set -uo pipefail

LO=${1:-1}; HI=${2:-10}
IMG=${FOAM_IMAGE:-opencfd/openfoam-default:2512}
PROJECT=${FOAM_PROJECT:-$HOME/smartfarm-cfd}
ROOT="$PROJECT/cases/fan-study"

for d in "$ROOT"/*/; do
    [ -f "$d/Allrun.new" ] || continue
    mv "$d/Allrun.new" "$d/Allrun"; chmod +x "$d/Allrun"
    echo "[$(basename "$d")] 이어받기용 Allrun 으로 교체"
done

docker rm -f fanstudy >/dev/null 2>&1 && echo "죽은 컨테이너 정리"

docker run -d --name fanstudy --cpus=12 \
    --user "$(id -u):$(id -g)" -e HOME=/data -v "$PROJECT:/data" "$IMG" \
    bash -lc "source /usr/lib/openfoam/openfoam*/etc/bashrc; bash /data/scripts/fan_study_batch.sh $LO $HI"

echo "다시 띄웠다. 진행은 docker logs -f fanstudy 로 본다."
