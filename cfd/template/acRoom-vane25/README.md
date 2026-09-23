# acRoom-vane25 — 이름과 내용이 다르다

**이 템플릿의 에어컨 취출은 수직 아래다. 25° 베인이 들어 있지 않다.**

폴더 이름은 2026-09-10 에 따로 돌린 실물 취출각 계산(`docs/OBJECTIVES.md` 13 절)에서
가져왔지만, 여기 담긴 `0.orig/U` 는 그 이전의 수직 취출본이다. 팬 스터디 30 케이스가
전부 이것을 물려받았다.

    0.orig/U   inletX*/inletY*  flowRateInletVelocity, value (0 0 -3.47)
    system/topoSetDict  취출면은 천장의 수평 띠 (z 2.699~2.701)

`flowRateInletVelocity` 는 패치 법선으로만 분다. 취출면이 수평이라 법선이 곧 아래다.

자세한 내용과 고치는 법은 `docs/FAN-CFD-ERRATA.md` **E-004** 를 봐라.
이름을 바꾸면 다른 컴퓨터의 `--template` 경로가 깨져서 그대로 둔다.
