#!/bin/bash
set -euo pipefail
export LC_ALL=C
shopt -s nullglob
cd /work/04_ac_upper
solver=$1
cpu_stat=/sys/fs/cgroup/cpu.stat
usage() { awk '$1=="usage_usec" {print $2}' "$cpu_stat"; }
last_sim() {
    tail -1000 log.run | awk '/^Time = /{t=$3} /^ExecutionTime = /&&t!=""{done=t} END{print (done==""?0:done)}'
}
write_canopy() {
    local tables=(postProcessing/{lowerMeanT15cm,upperMeanT15cm}/*/surfaceFieldValue.dat)
    ((${#tables[@]})) || return 0
    awk 'BEGIN{print "simulation_s,lower_15cm_C,upper_15cm_C"}
        NF==2 && $1~/^[0-9.+eE-]+$/ && $2~/^[0-9.+eE-]+$/ {
            t=int($1+0.5)
            if (($1-t)^2>1e-12 || t<300 || t>600 || t%30) next
            if(FILENAME~/lowerMeanT15cm/) lower[t]=$2; else upper[t]=$2
        }
        END{for(t=300;t<=600;t+=30) if(t in lower && t in upper)
            printf "%d,%.4f,%.4f\n",t,lower[t]-273.15,upper[t]-273.15
        }' "${tables[@]}" > canopy_300-600s.csv
    if ! cmp -s canopy_300-600s.csv /out/canopy_300-600s.csv; then
        cp canopy_300-600s.csv /out/.canopy.tmp && mv -f /out/.canopy.tmp /out/canopy_300-600s.csv || echo "Refresh deferred for canopy CSV" >&2
    fi
}
package_sensor=
for dev in /sys/class/hwmon/hwmon*; do
    [[ -r $dev/name ]] || continue
    [[ $(cat "$dev/name") == k10temp ]] || continue
    for label in "$dev"/temp*_label; do
        if [[ $(cat "$label") == Tctl && -r ${label%_label}_input ]]; then package_sensor=${label%_label}_input; fi
    done
done
last_at=$(date +%s)
last_use=$(usage)
last_t=0
printf '%s\n' 'utc_time,simulation_s,cpu_percent_one_thread_100,container_memory_MiB,oom_kills,cpu_package_C,progress' > /out/cpu_health.csv
health() {
    local now elapsed use percent sim mem oom temp='' progress=advancing
    now=$(date +%s); elapsed=$((now-last_at))
    (( elapsed > 0 )) || return 0
    use=$(usage)
    percent=$(awk -v u="$((use-last_use))" -v s="$elapsed" 'BEGIN{printf "%.1f",u/(10000*s)}')
    sim=$(last_sim)
    if [[ $sim == "$last_t" ]]; then progress=no_new_step; fi
    mem=$(awk '{printf "%.1f",$1/1048576}' /sys/fs/cgroup/memory.current)
    oom=$(awk '$1=="oom_kill"{print $2}' /sys/fs/cgroup/memory.events)
    if [[ -n $package_sensor ]]; then temp=$(awk '{printf "%.1f",$1/1000}' "$package_sensor"); fi
    printf '%s,%s,%s,%s,%s,%s,%s\n' "$(date -u +%FT%TZ)" "$sim" "$percent" "$mem" "$oom" "$temp" "$progress" >> /out/cpu_health.csv
    last_at=$now; last_use=$use; last_t=$sim
}
write_canopy
sleep 15
health
while kill -0 "$solver" 2>/dev/null; do
    write_canopy
    if (( $(date +%s)-last_at >= 300 )); then health; fi
    sleep 30
done
health
write_canopy
