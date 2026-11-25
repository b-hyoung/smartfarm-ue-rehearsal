# 4번 케이스 결과 · 상단 순환팬 가동

냉방기와 상단 팬 7대를 가동하고 하단 팬은 정지한 상태로 냉방 600초를 계산했다. OpenFOAM v2512, 149,426셀, CPU 12프로세스. 초기 공기 28.85°C, 방 벽·재배선반 단열, 4방향 급기 18°C. 계산과 후처리는 2026년 11월 25일 03:07 KST에 종료됐다.

## 캐노피 온도

재배판 위 15 cm 평가면에서 공기 온도를 면적평균했다. 양단의 1초 간격 기록에서 두 평균이 동시에 21~23°C인 첫 시각은 **181초**, 마지막 시각은 **296초**였다. 297초에 하단이 20.996°C로 떨어졌다. 600초에는 하단 18.9174°C, 상단 18.9245°C였다. [하단 1초 기록](postProcessing/lowerMeanT15cm/0/surfaceFieldValue.dat) · [상단 1초 기록](postProcessing/upperMeanT15cm/0/surfaceFieldValue.dat)

| 결과 | 파일·단위 |
|---|---|
| 300~600초, 30초 간격 상·하단 온도 | [11개 시점의 온도표](canopy_300-600s.csv), °C |
| 방 평균 공기 온도 | [1초 간격 체적평균](postProcessing/roomMeanT/0/volFieldValue.dat), K |
| 각 단의 풍속·온도 분포 | [canopyMaps](postProcessing/canopyMaps), 60초 간격 총 10시점. 재배판 위 15·18 cm의 좌표(m), 속도벡터(m/s), 온도(K) |
| 보조 측정점 42곳 | [literatureProbes10cm](postProcessing/literatureProbes10cm/0), 300·600초의 U와 T |
| 복원된 전체 3D 장 및 입력 | [fields](fields), 시점별 OpenFOAM 파일과 공통 격자·입력 |
| 상태·점검 | [CPU 사용 기록](cpu_health.csv), [격자 검산](mesh-check.txt), [종료 상태](status.txt) |

## 전체 3D 장 열기

빈 작업 폴더에 `constant-and-inputs.tar.gz`와 필요한 시점의 압축 파일을 함께 풀면 OpenFOAM 케이스가 된다. 예를 들어 `fields-600.tar.gz`를 풀면 `0/`, `constant/`, `system/`, `600/`이 같은 경로 아래에 놓인다. ParaView의 OpenFOAM 리더로 열려면 이 위치에 빈 `case.foam` 파일을 만든다. 각 압축 파일은 복원 원본과 대조했으며 [SHA-256 목록](fields/SHA256SUMS)을 제공한다.

원본 솔버 로그는 작업 PC 바탕화면의 `스마트팜_CFD_4번_완료로그_20261125/log.run`에 보관했다. 파일 크기 941,677,944바이트, SHA-256 `ea960e02748fce118fdd4fe076ee7b4520072709850299a4a32214dc22d6715a`.
