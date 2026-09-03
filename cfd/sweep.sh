#!/bin/bash
# 운전 조건을 바꿔가며 케이스를 여러 개 돌리고, 각각 UE 프레임 CSV까지 뽑는다.
#
# 원본 케이스는 건드리지 않는다. cfd/case 를 템플릿으로 삼아 조건별 사본을 만들고,
# 사본 안에서만 실행한다.
#
# 사용법:
#     cfd/sweep.sh                 # 아래 VARIANTS 전부 실행
#     cfd/sweep.sh flow30_289K     # 지정한 것만 실행
#     DRYRUN=1 cfd/sweep.sh        # 실제로 안 돌리고 계획만 출력
#
# 환경변수:
#     WORK    케이스 사본이 생길 폴더        (기본: <repo>/cfd/runs)
#     OUT     frame_*.csv 가 나올 폴더       (기본: <repo>/cfd/frames)
#     NP      MPI 프로세스 수                (기본: 8)
#     IMAGE   OpenFOAM 도커 이미지           (기본: opencfd/openfoam-default:2512)
#     NATIVE  1이면 도커 없이 현재 셸의 OpenFOAM 사용
#     PVBATCH pvbatch 실행 파일 경로         (기본: PATH 에서 찾음)

set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
TEMPLATE="$REPO/cfd/case"

WORK="${WORK:-$REPO/cfd/runs}"
OUT="${OUT:-$REPO/cfd/frames}"
NP="${NP:-8}"
IMAGE="${IMAGE:-opencfd/openfoam-default:2512}"
FOAM_BASHRC_IMG="/usr/lib/openfoam/openfoam2512/etc/bashrc"
PVBATCH="${PVBATCH:-pvbatch}"

# --------------------------------------------------------------------------- #
# 돌릴 조건들:  이름  총풍량(CMM)  토출온도(K)
#
# 기준선에서 한 번에 한 변수만 움직인다. 3x3 전조합(9케이스, 24시간+)은 과하다.
# --------------------------------------------------------------------------- #
VARIANTS=(
    "base_25cmm_289K   25   289.5"   # 기준 — 지금 UE 에 들어가 있는 조건
    "flow30_289K       30   289.5"   # 세게: 고르게 퍼지나 / 작물에 바람이 직접 닿나
    "flow20_289K       20   289.5"   # 약하게: 에너지 절감 시나리오
    "temp292_25cmm     25   292.0"   # 덜 차갑게: 급랭 완화 (작물 스트레스)
)

N_INLETS=4          # 4Way 천장 카세트 = 흡입구 4개 (inletXp/Xm/Yp/Ym)
EST_MIN_PER_CASE=163  # 실측 ClockTime 9741s ≈ 2시간 43분 (8코어 기준)

# --------------------------------------------------------------------------- #

if [ -n "${NATIVE:-}" ]; then
    # 현재 셸에 이미 OpenFOAM 환경이 잡혀 있다고 가정
    foam_exec() { ( cd "$1" && shift && eval "$@" ); }
else
    # WORK 를 /data 로 마운트하고 도커 안에서 실행
    foam_exec() {
        local cdir="$1"; shift
        local rel="${cdir#"$WORK"/}"
        docker run --rm -v "$WORK:/data" "$IMAGE" \
            bash -c "source $FOAM_BASHRC_IMG; cd /data/$rel && $*"
    }
fi

# 0.orig/T, 0.orig/U 의 inlet 4개에 값을 써넣는다.
apply_conditions() {
    local cdir="$1" cmm="$2" temp_k="$3"
    # 슬롯당 체적유량 (m3/s) = 총 CMM / 60초 / 슬롯수
    local rate
    rate=$(awk -v c="$cmm" -v n="$N_INLETS" 'BEGIN{printf "%.6f", c/60.0/n}')

    for patch in inletXp inletXm inletYp inletYm; do
        foam_exec "$cdir" \
            "foamDictionary -entry boundaryField/$patch/value \
                            -set 'uniform $temp_k' 0.orig/T > /dev/null"
        foam_exec "$cdir" \
            "foamDictionary -entry boundaryField/$patch/volumetricFlowRate \
                            -set 'constant $rate' 0.orig/U > /dev/null"
    done
    echo "    조건 적용: $cmm CMM (슬롯당 $rate m3/s), 토출 $temp_k K"
}

# --------------------------------------------------------------------------- #

wanted=("$@")
selected=()
for v in "${VARIANTS[@]}"; do
    name=$(echo "$v" | awk '{print $1}')
    if [ ${#wanted[@]} -eq 0 ]; then
        selected+=("$v")
    else
        for w in "${wanted[@]}"; do
            [ "$w" = "$name" ] && selected+=("$v")
        done
    fi
done

if [ ${#selected[@]} -eq 0 ]; then
    echo "해당하는 조건이 없습니다. 사용 가능:" >&2
    for v in "${VARIANTS[@]}"; do echo "  - $(echo "$v" | awk '{print $1}')" >&2; done
    exit 1
fi

total_min=$(( ${#selected[@]} * EST_MIN_PER_CASE ))
echo "==================================================================="
echo " 케이스 ${#selected[@]}개, 예상 소요 약 $((total_min / 60))시간 $((total_min % 60))분 (순차, ${NP}코어)"
echo " 작업 폴더 : $WORK"
echo " 프레임    : $OUT"
echo "==================================================================="

for v in "${selected[@]}"; do
    read -r name cmm temp_k <<< "$v"
    cdir="$WORK/$name"

    echo
    echo "### [$name] $cmm CMM / $temp_k K   $(date '+%H:%M:%S')"

    if [ -n "${DRYRUN:-}" ]; then
        echo "    (DRYRUN) $TEMPLATE -> $cdir, 실행 후 $OUT/$name 에 프레임"
        continue
    fi

    # 1) 템플릿 복사 — 원본은 절대 건드리지 않는다
    rm -rf "$cdir"
    mkdir -p "$cdir"
    cp -r "$TEMPLATE"/. "$cdir"/

    # 2) 조건 주입
    apply_conditions "$cdir" "$cmm" "$temp_k"

    # 3) 솔버 실행 (메시부터 재조립까지)
    foam_exec "$cdir" "NP=$NP ./RUN.sh"

    # 4) UE 프레임 추출 — 도커 밖(호스트)의 ParaView 로
    mkdir -p "$OUT/$name"
    "$PVBATCH" "$REPO/cfd/extract_frames.py" "$cdir" "$OUT/$name"

    echo "### [$name] 완료 $(date '+%H:%M:%S')"
done

echo
echo "전부 완료. UE 에서는 $OUT/<조건이름>/ 폴더를 바꿔 끼우면 됩니다."
