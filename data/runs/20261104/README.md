# 20261104 스마트팜 CFD 공용 작업 지침

| 항목 | 값 |
|---|---|
| GitHub 저장소 | https://github.com/b-hyoung/smartfarm-ue-rehearsal |
| 배포 브랜치 | `cfd/20261104` |
| 저장소 내 작업 폴더 | `data/runs/20261104` |
| 실행 환경 | Windows PowerShell, Git, 실행 중인 Docker의 Linux 컨테이너 모드 |

네 PC에서 같은 Git 커밋과 Docker 이미지 `opencfd/openfoam-default:2512` 사용. 케이스별 공통 격자 403,210셀, 기본 MPI 프로세스 12개. PC마다 지정받은 작업 번호 하나 선택.

| 작업 번호 | 케이스 | 하단 순환팬 | 상단 순환팬 |
|---|---|---:|---:|
| 1 | `01_ac_only` | 정지 | 정지 |
| 2 | `02_ac_all` | 7대 | 7대 |
| 3 | `03_ac_lower` | 7대 | 정지 |
| 4 | `04_ac_upper` | 정지 | 7대 |

## 실험 입력

| 항목 | 공통 조건 |
|---|---|
| 냉방기 | 출구마다 3.5 m/s, 18°C, 수평 기준 하향 30°. 기존 강풍 연구 입력 25 m³/min, 네 방향 균등 분배 시 출구당 6.25 m³/min. |
| 급기면 | 수평 천장면의 하향 속도 1.75 m/s. 슬롯 길이 0.65 m와 유효 폭 약 0.0915751 m로 출구당 유효 면적 0.05952381 m² 산출. 실물 개구 면적은 미측정. |
| 순환팬 | 가동 팬당 0.84 m³/min. 단마다 한쪽 4대·반대쪽 3대의 교차 배열, 재배판 위 15 cm에서 안쪽으로 수평 송풍. |
| 작물 | 18 cm 다공성 캐노피. 점성 저항계수 25 m⁻², 관성 저항계수 1.3 m⁻¹. |
| 초기·경계 | 공기 초기온도 302 K(28.85°C), 초기풍속 0 m/s, 압력 100,000 Pa. 방 벽·재배판·상판에 단열 조건 적용. |
| 격자 | 반타원형 방의 외곽 격자 간격 확대. 4방향 냉기 토출 경로와 두 재배단 주변 국소 세분. 18 cm 캐노피에 하단 32,960셀, 상단 33,000셀 배치. |
| 솔버·시간 | OpenFOAM v2512 `buoyantPimpleFoam`, RAS k–ε, 케이스당 물리시간 900초. 초기 Δt 0.002초, 자동 조절, 최대 Courant 수 1, 최대 Δt 0.5초. |
| 평가 | 재배판 위 15 cm의 상·하단 풍속·온도 분포를 300·600·900초에 비교. 단별 면적평균 온도는 1초 간격 기록. 두 단이 동시에 21~23°C에 처음 진입한 시각 평가. |

## 확인한 범위

OpenFOAM v2512에서 네 케이스의 격자와 팬 입력 검산. 공통 403,210셀, 출구당 풍량 6.25000 m³/min, 네 출구 합계 25.00000 m³/min. 캐노피 높이 각 18.0 cm. 상판 밑면과 윗면 면적 각 1.92000 m². 가동 팬 소스항은 작업 번호 순서로 0·14·7·7개.

4번 단시간 시험에서 재배판 위 15 cm 평가면의 유효 면적은 단당 1.9104 m². 각 PC의 본 계산에서 300·600·900초 풍속과 온도 기록. 장시간 결과의 격자 독립성은 미검증.

## 기존 저장소에서 받기

기존 저장소 루트에서 PowerShell 실행. 첫 번째 명령 묶음은 배포 브랜치로 전환하고 해당 폴더로 이동.

```powershell
git fetch origin
git switch cfd/20261104
git pull --ff-only origin cfd/20261104
Set-Location data/runs/20261104
git branch --show-current
git rev-parse --short HEAD
```

기존 작업 폴더를 사용 중이면 별도 폴더로 받을 수 있음. 아래는 위 명령 묶음을 대신하는 방법.

```powershell
git clone --depth 1 --single-branch --branch cfd/20261104 https://github.com/b-hyoung/smartfarm-ue-rehearsal.git smartfarm-20261104
Set-Location smartfarm-20261104/data/runs/20261104
git branch --show-current
git rev-parse --short HEAD
```

현재 브랜치 표시가 `cfd/20261104`인지, 공동 작업 PC들의 커밋 번호가 같은지 확인.

## 1. 배정 케이스의 격자 준비

작업 번호를 받은 뒤 입력. 번호가 잘못되면 명령 중단. `prepare`는 격자를 생성한 뒤 품질, 캐노피 두께, 상판 면적, 14개 팬 영역, 네 급기면의 풍량을 검사. 같은 번호의 Docker 볼륨에 입력과 검사 기록 저장. 아래의 `run` 명령은 별도로 실행.

```powershell
$Number = Read-Host '지정받은 작업 번호 (1~4)'
.\pc-case.ps1 -Number $Number -Action Prepare
```

## 2. 해당 PC에서 계산을 시작할 때

같은 PowerShell 세션에서 실행. 선택한 케이스 하나가 백그라운드에서 시작되며 계산 기록과 체크포인트는 케이스별 Docker 볼륨에 보관.

```powershell
.\pc-case.ps1 -Number $Number -Action Run
```

## 3. 계산 완료 후 결과 복사

컨테이너 종료 코드 0 확인 후 시간별 풍속·온도 평가 결과와 실행 로그를 호스트에 복사. 보조 측정점 42개는 복원된 전체 장에서 원래 좌표로 추출. 복원된 300·600·900초 전체 장은 볼륨의 `/work/<케이스>/`에 보관.

```powershell
$Case = @{'1'='01_ac_only'; '2'='02_ac_all'; '3'='03_ac_lower'; '4'='04_ac_upper'}[[string]$Number]
$Container = "sf-20261104-403210-$Case"
docker inspect --format '{{.State.Status}} {{.State.ExitCode}}' $Container
$Results = Join-Path $HOME "smartfarm-results/20261104/403210/$Case"
New-Item -ItemType Directory -Force $Results | Out-Null
docker cp "${Container}:/work/$Case/postProcessing" $Results
docker cp "${Container}:/work/$Case/log.run" $Results
```
