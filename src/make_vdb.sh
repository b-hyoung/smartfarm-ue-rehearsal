#!/usr/bin/env bash
# 프레임 CSV -> VDB. 윈도우·맥 파이썬엔 openvdb 가 없어 데비안 컨테이너로 돈다.
#
#   bash src/make_vdb.sh 05_F3
#
# 앞 단계
#   bash src/export_volume.sh 05_F3     (processor*/ -> 수평면 raw)
#   py -m src.volume_frames --case 05_F3 (raw -> out/frames/05_F3/*.csv)
set -uo pipefail

RID=${1:?케이스 이름을 달라 (예: 05_F3)}
shift || true
# 조명 발열을 뺀 계산이라 방이 차다. 색척도를 케이스에 맞게 좁혀 둔다.
SCALE=${VDB_SCALE:---tmin 17 --tmax 27}
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
IMG=${VDB_IMAGE:-debian:bookworm-slim}

[ -d "$REPO/out/frames/$RID" ] || {
    echo "out/frames/$RID 가 없다. 먼저: py -m src.volume_frames --case $RID" >&2; exit 1; }

MOUNT="$REPO"
EXTRA=(--user "$(id -u):$(id -g)")
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        MOUNT=$(cygpath -w "$REPO")
        export MSYS_NO_PATHCONV=1
        EXTRA=()
        ;;
esac

# 패키지 설치가 매번 일어나지 않게 한 번 구운 이미지를 재사용한다.
if ! docker image inspect sf-openvdb:1 >/dev/null 2>&1; then
    echo "=== openvdb 이미지를 한 번 굽는다 (처음 한 번만, 2~3 분) ==="
    docker build -t sf-openvdb:1 - <<'DOCKER'
FROM debian:bookworm-slim
RUN apt-get -qq update \
 && apt-get -qq install -y --no-install-recommends python3-openvdb python3-numpy \
 && rm -rf /var/lib/apt/lists/*
DOCKER
fi

docker run --rm "${EXTRA[@]}" -v "$MOUNT:/work" -w /work sf-openvdb:1 \
    python3 -m src.make_vdb --case "$RID" $SCALE "$@"
