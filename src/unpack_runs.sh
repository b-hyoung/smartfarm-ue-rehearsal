#!/usr/bin/env bash
# data/runs/*/<case>/postProcessing.tar.gz 를 한 폴더에 풀어 미리보기 생성기의 원본으로 쓴다.
#   sh src/unpack_runs.sh [출력폴더]     기본 ~/smartfarm-cfd/cases/fan-study-all
# 같은 케이스가 여러 폴더에 있으면 나중 날짜(정렬상 뒤) 것이 덮는다.
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$HOME/smartfarm-cfd/cases/fan-study-all}
for tgz in $(ls "$REPO"/data/runs/*/*/postProcessing.tar.gz | sort); do
    c=$(basename "$(dirname "$tgz")")
    mkdir -p "$OUT/$c"
    rm -rf "$OUT/$c/postProcessing"
    tar xzf "$tgz" -C "$OUT/$c"
    printf '%-8s %s 장\n' "$c" "$(ls "$OUT/$c/postProcessing/canopy" | wc -l | tr -d ' ')"
done
echo "-> $OUT   (SF_WIND_ROOT=$OUT py -m src.make_wind_page --build)"
