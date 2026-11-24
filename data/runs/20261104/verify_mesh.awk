# Read checkMesh, boundary, U, T, faces and points, in that order.
# Store boundary polygons and their referenced points only.
function fail(message) { print message > "/dev/stderr"; bad=1 }
function near(actual, target, label) {
    if ((actual-target)^2 > (1e-7 + 1e-6*(target<0?-target:target))^2)
        fail(label ": " actual " versus " target)
}
function clean(line) { gsub(/[();]/," ",line); sub(/^[[:space:]]+/,"",line); return line }
function inlet(name) { return name ~ /^inlet[XY][pm]$/ }
FILENAME ~ /log.checkMesh$/ {
    if (/^Mesh OK[.]/) ok=1
    if ($1=="cells:") cells=$2
    if ($1 ~ /^fan_t[01]_(front|back)[0-9]+$/) {
        if ($2<=0) fail("Empty fan zone " $1)
        fanCount++
    }
    if ($1 ~ /^canopy_t[01]$/) {
        split(clean($0), zone, /[[:space:]]+/)
        base=(zone[1]=="canopy_t0" ? 0.55 : 1.35)
        near(zone[7],base,zone[1] " base")
        near(zone[10],base+0.18,zone[1] " top")
        canopy[zone[1]]=sprintf("%.3f..%.3f m",zone[7],zone[10])
    }
    next
}
FILENAME ~ /\/boundary$/ {
    if (NF==1 && (inlet($1) || $1=="rackWalls")) patch=$1
    if (patch!="" && $1=="nFaces") count[patch]=$2+0
    if (patch!="" && $1=="startFace") start[$2+0]=patch
    if ($1=="}") patch=""
    next
}
FILENAME ~ /^0\/[UT]$/ {
    if (NF==1 && (inlet($1) || $1=="rackWalls" || $1=="walls")) patch=$1
    if (FILENAME=="0/T" && patch=="walls" && $1=="type") {
        if ($2!="zeroGradient;") fail("0/T walls type: " $2)
        wallTemperatureChecked=1
    }
    if (patch=="rackWalls" && $1=="type") {
        expected=FILENAME=="0/U" ? "noSlip;" : "zeroGradient;"
        if ($2!=expected) fail(FILENAME " rackWalls type: " $2)
        rackField[FILENAME]=1
    }
    if (inlet(patch) && $1=="value") {
        split(clean($0),field,/[[:space:]]+/)
        if (FILENAME=="0/U") {
            ux[patch]=field[3]+0; uy[patch]=field[4]+0; uz[patch]=field[5]+0
            near(sqrt(ux[patch]^2+uy[patch]^2+uz[patch]^2),3.5,patch " speed")
            near(uz[patch],-1.75,patch " vertical speed")
        } else near(field[3],291.15,patch " temperature")
    }
    if ($1=="}") patch=""
    next
}
FILENAME ~ /\/faces$/ {
    if ($0 ~ /^[0-9]+\(/) {
        if (faceNumber in start) {
            patch=start[faceNumber]
            stop=faceNumber+count[patch]
        }
        if (faceNumber < stop) {
            n=split(clean($0),row,/[[:space:]]+/)
            facePatch[faceNumber]=patch
            polygon[faceNumber]=$0
            for (i=2;i<=row[1]+1;i++) wanted[row[i]+0]=1
        }
        faceNumber++
    }
    next
}
FILENAME ~ /\/points$/ && /^\([-+.0-9]/ {
    if (pointNumber+0 in wanted) {
        split(clean($0),coord,/[[:space:]]+/)
        x[pointNumber+0]=coord[1]; y[pointNumber+0]=coord[2]; z[pointNumber+0]=coord[3]
    }
    pointNumber++
}
END {
    if (cells!=403210) fail("Expected 403210 cells; found " cells)
    if (!ok || !wallTemperatureChecked || fanCount!=14 || length(canopy)!=2 || length(rackField)!=2)
        fail("checkMesh, fan zones or canopy zones incomplete")
    for (f in polygon) {
        split(clean(polygon[f]),row,/[[:space:]]+/)
        n=row[1]+0; sx=sy=sz=0; bottom=top=1
        for (i=0;i<n;i++) {
            a=row[2+i]+0; b=row[2+(i+1)%n]+0
            if (!(a in z)) { fail("Missing mesh point " a); break }
            sx+=(y[a]-y[b])*(z[a]+z[b])/2
            sy+=(z[a]-z[b])*(x[a]+x[b])/2
            sz+=(x[a]-x[b])*(y[a]+y[b])/2
            if ((z[a]-1.75)^2>1e-14) bottom=0
            if ((z[a]-1.785)^2>1e-14) top=0
        }
        patch=facePatch[f]
        if (inlet(patch)) {
            area[patch]+=sqrt(sx*sx+sy*sy+sz*sz)
            flow[patch]+=-60*(ux[patch]*sx+uy[patch]*sy+uz[patch]*sz)
        } else {
            if (bottom) bottomArea+=(sz<0?-sz:sz)
            if (top) topArea+=(sz<0?-sz:sz)
        }
    }
    print "cells:",cells,"fan zones:",fanCount
    print "canopy_t0:",canopy["canopy_t0"],"canopy_t1:",canopy["canopy_t1"]
    if (length(flow)!=4) fail("Missing supply patches")
    for (patch in flow) {
        near(flow[patch],6.25,patch " CMM")
        printf "%s: %.8f m2, %.5f m3/min\n",patch,area[patch],flow[patch]
        total+=flow[patch]
    }
    near(total,25,"total CMM")
    near(bottomArea,1.92,"closed plate bottom")
    near(topArea,1.92,"closed plate top")
    printf "total supply: %.5f m3/min\nplate area at 1.750 / 1.785 m: %.5f / %.5f m2\n",total,bottomArea,topArea
    exit bad ? 1 : 0
}
