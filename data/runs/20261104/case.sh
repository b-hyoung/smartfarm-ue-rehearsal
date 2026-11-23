#!/bin/bash
# Run in the OpenFOAM 2512 image with the study at /study and persistent /work.
set -euo pipefail
mode=${1:-}
name=${2:-}
case "$name" in
    01_ac_only|02_ac_all|03_ac_lower|04_ac_upper) ;;
    *) echo 'Choose 01_ac_only, 02_ac_all, 03_ac_lower or 04_ac_upper.' >&2; exit 2 ;;
esac
case "$mode" in prepare|run) ;; *) echo 'Usage: bash /study/case.sh prepare|run CASE' >&2; exit 2 ;; esac
cd /work
stage() {
    local log=$1
    shift
    "$@" > "$log" 2>&1 || { tail -40 "$log" >&2; return 1; }
}
if [[ "$mode" == prepare ]]; then
    if [[ -e "$name" ]]; then echo "$name already exists in this volume." >&2; exit 1; fi
    temp=$(mktemp -d "/work/.prepare-$name-XXXXXX")
    trap 'rm -rf -- "$temp"' EXIT
    cd "$temp"
    cp -r /study/common/system /study/common/constant .
    cp "/study/$name/system/fvOptions" system/fvOptions
    stage log.blockMesh blockMesh
    stage log.selectRefine topoSet -dict system/topoSetDict.canopyRefine
    stage log.refineMesh refineMesh -dict system/refineMeshDict -overwrite
    stage log.selectAC topoSet -dict system/topoSetDict.ac
    stage log.createPatch createPatch -overwrite
    stage log.selectRack topoSet -dict system/topoSetDict.rack
    stage log.subsetMesh subsetMesh keep -patch rackWalls -overwrite
    stage log.wallType foamDictionary constant/polyMesh/boundary -entry entry0/rackWalls/type -set wall
    stage log.wallGroup foamDictionary constant/polyMesh/boundary -entry entry0/rackWalls/inGroups -set '1(wall)'
    stage log.zones topoSet -dict system/topoSetDict.fans
    stage log.checkMesh checkMesh -constant
    mkdir -p 0
    cp -r /study/common/0.orig/. 0/
    awk -f /study/verify_mesh.awk log.checkMesh constant/polyMesh/boundary 0/U 0/T constant/polyMesh/faces constant/polyMesh/points | tee mesh-check.txt
    cd /work
    mv -T -- "$temp" "$name"
    trap - EXIT
    exit
fi
cd "$name"
if [[ ! -s mesh-check.txt || -e processor0 || -e log.run ]]; then
    echo 'Use a prepared case with no earlier solver run.' >&2
    exit 1
fi
export OMP_NUM_THREADS=1 OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
stage log.decomposePar decomposePar
stage log.run mpirun --bind-to none -np 4 buoyantPimpleFoam -parallel
stage log.reconstructPar reconstructPar -newTimes
stage log.probes postProcess -dict system/postProbesDict -fields '(U T)' -time '300,600,900'
