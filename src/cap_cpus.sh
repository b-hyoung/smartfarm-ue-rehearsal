#!/usr/bin/env bash
# 돌고 있는 fan-study 컨테이너의 CPU 상한을 실시간으로 바꾼다 (재시작 없음).
# 케이스가 바뀌어 새 컨테이너가 떠도 같은 값으로 잡는다. 배치가 끝나면 스스로 종료.
#
#   bash src/cap_cpus.sh 6 "11 20" &     11~20 배치를 6 코어로
#
# 맥이 뜨거울 때 쓴다. 6 이면 8 대비 약 25 % 느려진다.
CAP=${1:-6}; RANGE=${2:-}
while pgrep -f "run_foam_cases.sh ${RANGE}" >/dev/null; do
    for c in $(docker ps -q); do docker update --cpus "$CAP" "$c" >/dev/null 2>&1; done
    sleep 20
done
