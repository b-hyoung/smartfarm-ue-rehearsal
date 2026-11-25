#!/bin/bash
set -euo pipefail
export LC_ALL=C
cd /work
mkdir 04_ac_upper
cd 04_ac_upper
cp -a /input/04_ac_upper/{0,constant,system,mesh-check.txt} .
grep -q 'cells: 149426' mesh-check.txt
test "$(foamDictionary system/decomposeParDict -entry numberOfSubdomains -value)" = 12
test "$(foamDictionary 0/T -entry boundaryField/walls/type -value)" = zeroGradient
test "$(foamDictionary 0/T -entry boundaryField/rackWalls/type -value)" = zeroGradient
test "$(foamDictionary system/controlDict -entry startFrom -value)" = startTime
test "$(foamDictionary system/controlDict -entry startTime -value)" = 0
foamDictionary system/controlDict -entry endTime -set 600
foamDictionary system/controlDict -entry writeInterval -set 60
foamDictionary system/controlDict -entry functions/canopyMaps/writeInterval -set 60
test "$(foamDictionary system/controlDict -entry functions/lowerMeanT15cm/writeInterval -value)" = 1
test "$(foamDictionary system/controlDict -entry functions/upperMeanT15cm/writeInterval -value)" = 1
export OMP_NUM_THREADS=1 OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
on_exit() {
    rc=$?
    if [[ $rc != 0 ]]; then printf 'failed (exit %d)\n' "$rc" > /out/status.txt; fi
}
trap on_exit EXIT
printf '%s\n' preparing > /out/status.txt
decomposePar > log.decomposePar 2>&1
printf '%s\n' running > /out/status.txt
mpirun --bind-to none --use-hwthread-cpus -np 12 buoyantPimpleFoam -parallel > log.run 2>&1 &
solver=$!
bash /out/observe.sh "$solver" > log.observer 2>&1 &
observer=$!
wait "$solver"
wait "$observer"
grep -q '^End$' log.run
for n in $(seq 0 11); do test -s "processor$n/600/U"; test -s "processor$n/600/T"; done
printf '%s\n' postprocessing > /out/status.txt
reconstructPar -time '60:600' > log.reconstructPar 2>&1
postProcess -dict system/postProbesDict -fields '(U T)' -time '300,600' > log.probes 2>&1
cp -a postProcessing /out/
cp log.run log.observer log.reconstructPar log.probes /out/
test "$(wc -l < /out/canopy_300-600s.csv)" -eq 12
printf '%s\n' complete > /out/status.txt
