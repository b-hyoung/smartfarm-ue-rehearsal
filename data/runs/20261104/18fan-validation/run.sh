#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C OMP_NUM_THREADS=1 OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
ranks=$1
trap 'rc=$?; if ((rc)); then echo "FAILED: line $LINENO (exit $rc)" | tee /out/status.txt; fi' EXIT
status(){ echo "$*" | tee /out/status.txt; }
status "Preparing baseline mesh"
bash /study/case.sh prepare 02_ac_all
cd /work/02_ac_all
(cd constant/polyMesh && sha256sum -c /study/mesh.sha256)
topoSet -dict /study/sideZones > /out/log.sideZones 2>&1
checkMesh -constant > /out/log.checkMesh 2>&1
awk '$1 ~ /^fan_t[01]_(front[1-4]|back[1-3]|left|right)$/ && $2+0>0 {zone[$1]=1}
     /^Mesh OK\./{ok=1} END{if(!ok || length(zone)!=18)exit 1}' /out/log.checkMesh
cp /study/schedule.csv /out/
if ((ranks>1)); then
    foamDictionary system/decomposeParDict -entry numberOfSubdomains -set "$ranks"
    decomposePar > /out/log.decomposePar 2>&1
    solver=(mpirun --bind-to none --use-hwthread-cpus -np "$ranks" buoyantPimpleFoam -parallel)
    time_dir=processor0
else
    solver=(buoyantPimpleFoam)
    time_dir=.
fi
for end in {60..600..60}; do
    begin=$((end-60))
    status "CFD interval $begin-$end s"
    cp "/study/options-$end" system/fvOptions
    foamDictionary system/controlDict -entry startFrom -set latestTime
    foamDictionary system/controlDict -entry endTime -set "$end"
    log="/out/log.$begin-$end"
    "${solver[@]}" > "$log" 2>&1
    grep -qx "Time = $end" "$log"
    grep -qx 'End' "$log"
    test -s "$time_dir/$end/U"
    test -s "$time_dir/$end/T"
done
if ((ranks>1)); then reconstructPar -time '60:600' > /out/log.reconstructPar 2>&1; fi
cp -r postProcessing /out/
for t in {60..600..60}; do
    test -s "/out/postProcessing/canopyMaps/$t/U_lower15cm.raw"
    test -s "/out/postProcessing/canopyMaps/$t/U_upper15cm.raw"
done
status "complete"
