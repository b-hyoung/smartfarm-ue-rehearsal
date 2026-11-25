# 3번 케이스 결과 · 하단 순환팬 가동

냉방기와 하단 팬 7대를 켜고 상단 팬은 정지한 상태에서 냉방 600초를 계산했다. OpenFOAM v2512의 `buoyantPimpleFoam`, 149,426셀 격자, Apple M4 Pro에서 MPI 9개를 사용했다. 계산과 후처리는 2026년 11월 24일 19:24부터 25일 13:09까지 약 17시간 45분 동안 진행됐다(KST). 컨테이너 종료 코드는 0이며 메모리 부족 종료는 0건이었다.

재배판 위 15 cm에서 공기 온도를 면적평균했다. 1초 간격 기록에서 상·하단이 동시에 21~23°C에 처음 진입한 시각은 **189초**였다. 이때 하단은 22.6767°C, 상단은 22.9844°C였다. 600초에는 하단 18.8828°C, 상단 18.9763°C였다.

| 결과 | 파일 |
|---|---|
| 300~600초, 30초 간격 상·하단 온도(°C) | [11개 시점의 온도표](canopy_300-600s.csv) |
| 1초 간격 상·하단 면적평균 및 방 체적평균(K) | [하단](postProcessing/lowerMeanT15cm/0/surfaceFieldValue.dat) · [상단](postProcessing/upperMeanT15cm/0/surfaceFieldValue.dat) · [방](postProcessing/roomMeanT/0/volFieldValue.dat) |
| 60초 간격 15·18 cm 평가면의 속도·온도 분포 | [canopyMaps](postProcessing/canopyMaps) |
| 300·600초의 10 cm 높이 보조 측정점 42곳 | [literatureProbes10cm](postProcessing/literatureProbes10cm/0) |
| 실행 기록 | [벤치마크](bench.json) · [CPU 상태](cpu_health.csv) · [격자 검산](mesh-check.txt) · [종료 상태](status.txt) |

전체 3D 장은 실행 Mac의 Docker 볼륨 `smartfarm-149426-v1-03_ac_lower-run`에 보관했다. 원본 솔버 로그 `log.run`은 바탕화면의 `SmartFarm_CFD_Case3_Logs_20261125`에 복사했다. 파일 크기는 926,241,059바이트이며 SHA-256은 `93482a96d2e8a2999bb72d6aef311b96fddcfa80deaefacd2a6f89f762c2e663`이다.
