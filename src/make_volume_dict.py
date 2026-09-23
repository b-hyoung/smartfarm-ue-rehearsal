# -*- coding: utf-8 -*-
"""케이스에 볼륨 추출용 function object(`system/volumeGrid`)를 써 넣는다.

방 전체를 0.1 m 간격 수평면 27 장으로 잘라 U·T 를 뽑는다. 이 높이 간격이
VDB 복셀 한 변(0.1 m)과 같아서, 면 하나가 복셀 한 층에 그대로 대응한다.

왜 셀 중심을 그대로 안 쓰고 면으로 자르나
--------------------------------------
전체 셀 값을 받으려면 `reconstructPar` 로 분할본을 다시 합쳐야 한다(케이스당
수십 분, 1 GB). 반면 `postProcess -parallel -func volumeGrid` 는 `processor*/`
저장본에서 바로 돌아 몇 분이면 끝난다. 0.1 m 격자에서 수평면 하나를 자르면
그 층의 셀을 한 번씩 지나므로, 0.1 m 복셀로 담을 때 정보 손실이 없다.

⚠ 재배단·팬 상자만 0.05 m 로 세분돼 있다. 그 구간은 한 복셀에 세분 셀이
  여러 개 들어가 평균된다 — VDB 해상도가 0.1 m 이므로 의도된 결과다.

실행  py -m src.make_volume_dict --case 05_F3
"""
from __future__ import annotations

import argparse
import os

DZ = 0.10            # 면 간격 = VDB 복셀 한 변
NZ = 27              # 0.05 ~ 2.65 m, 방 높이 2.7 m
ROOM_Z = 2.7

HEAD = """/*--------------------------------*- C++ -*----------------------------------*\\
| 볼륨 추출 — src/make_volume_dict.py 가 만든다. 직접 고치지 말 것.          |
\\*---------------------------------------------------------------------------*/
volumeGrid
{
    type            surfaces;
    libs            (sampling);
    writeControl    writeTime;
    surfaceFormat   raw;
    fields          (U T);
    interpolate     false;
    surfaces
    {
"""

PLANE = """        z%03d
        {
            type            plane;
            planeType       pointAndNormal;
            pointAndNormalDict { point (0 2 %.3f); normal (0 0 1); }
            interpolate     false;
        }
"""

TAIL = """    }
}
"""


def dict_text():
    out = [HEAD]
    for k in range(NZ):
        z = round(DZ / 2.0 + k * DZ, 3)
        if z >= ROOM_Z:
            break
        out.append(PLANE % (k, z))
    out.append(TAIL)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="케이스 폴더 이름 또는 전체 경로")
    ap.add_argument("--root", default=os.path.join(os.path.expanduser("~"),
                                                   "smartfarm-cfd", "cases", "fan-study"))
    a = ap.parse_args()
    case = a.case if os.path.isdir(a.case) else os.path.join(a.root, a.case)
    if not os.path.isdir(os.path.join(case, "system")):
        raise SystemExit("케이스가 아니다: " + case)
    path = os.path.join(case, "system", "volumeGrid")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dict_text())
    print("%s  <- 수평면 %d 장 (%.2f m 간격)" % (path, NZ, DZ))


if __name__ == "__main__":
    main()
