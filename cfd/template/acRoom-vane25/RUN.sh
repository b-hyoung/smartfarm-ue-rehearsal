#!/bin/bash
# 케이스 1개를 처음부터 끝까지 돌린다 (메시 -> 분할 -> 솔버 -> 재조립).
#
# ⚠ OpenFOAM bashrc 는 `set -e` 가 켜진 상태에서 source 하면 깨집니다
#   ("pop_var_context: head of shell_variables not a function context")
#   → 먼저 source 하고 그 다음에 set -e 를 켭니다.
#
# ⚠ 시작할 때 이전 결과(processor*, 시간 디렉터리, log.*)를 지웁니다.
#   스윕을 돌릴 때는 반드시 케이스 사본에서 실행하세요 (cfd/sweep.sh 가 그렇게 합니다).
#
# 환경변수:
#   FOAM_BASHRC  OpenFOAM etc/bashrc 경로 (기본: 도커 이미지 경로)
#   NP           MPI 프로세스 수 (기본: 8, system/decomposeParDict 와 맞아야 함)

# 스크립트가 있는 폴더 = 케이스 폴더. 어디서 호출하든 동작한다.
cd "$(dirname "$(readlink -f "$0")")"

FOAM_BASHRC="${FOAM_BASHRC:-/usr/lib/openfoam/openfoam2512/etc/bashrc}"
NP="${NP:-8}"

if [ -z "$WM_PROJECT_DIR" ]; then
    if [ ! -f "$FOAM_BASHRC" ]; then
        echo "OpenFOAM bashrc 를 찾을 수 없습니다: $FOAM_BASHRC" >&2
        echo "FOAM_BASHRC 환경변수로 경로를 지정하세요." >&2
        exit 1
    fi
    source "$FOAM_BASHRC"
fi

set -e

echo "### 케이스: $PWD"
echo "### 정리"
rm -rf processor* postProcessing log.* core.* 2>/dev/null || true
# 0.orig 와 constant/system 을 뺀 시간 디렉터리 제거
for d in [0-9]* ; do
    [ -d "$d" ] && [ "$d" != "0.orig" ] && rm -rf "$d"
done

echo "### 초기장 복원"
cp -r 0.orig 0

echo "### blockMesh"      && blockMesh              > log.blockMesh   2>&1
echo "### topoSet"        && topoSet                > log.topoSet     2>&1
echo "### createPatch"    && createPatch -overwrite > log.createPatch 2>&1
echo "### decomposePar"   && decomposePar           > log.decomposePar 2>&1

echo "### 솔버 시작 (${NP}코어) $(date)"
mpirun -np "$NP" buoyantPimpleFoam -parallel > log.run 2>&1

echo "### reconstructPar $(date)"
reconstructPar > log.reconstructPar 2>&1

touch acRoom.foam
echo "### 완료 $(date)"
