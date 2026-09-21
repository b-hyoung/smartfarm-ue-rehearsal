# 바로 시작하기 — 팬 스터디 30 케이스

이 문서 하나만 읽으면 다른 컴퓨터에서 바로 돌릴 수 있게 적는다.
**정해진 값은 전부 아래 표에 있고, 손으로 고칠 것은 없다.** 배경과 근거는
`FAN-CFD-METHOD.md`, 격자 문헌은 `FAN-CFD-MESH-REFERENCES.md` 에 있다.

작성 2026-09-21 · 브랜치 `feat/rack-fans`

---

## 0. 한 줄 상태

케이스 생성·격자 세분·캐노피 다공체·검산·채점까지 **코드는 다 됐다.**
**아직 한 번도 돌리지 않았다.** 새로 넣은 OpenFOAM 설정 셋(`refineMesh`,
`explicitPorositySource`, `surfaceFieldValue`)이 v2512 에서 실제로 먹는지는
미검증이다. 그래서 **5 번 케이스 하나부터** 돌린다.

---

## 1. 준비물

| 것 | 내용 | 확인 |
|---|---|---|
| 리눅스 환경 | WSL2 우분투 또는 리눅스·맥. 윈도우 네이티브 불가 | `uname -a` |
| 도커 데몬 | **떠 있어야 한다.** 이미지 `opencfd/openfoam-default:2512` | `docker version` |
| 파이썬 3 | 표준 라이브러리만 쓴다 | `python3 -V` |
| 이 저장소 | `feat/rack-fans` 브랜치 | `git log --oneline -1` |
| **템플릿 케이스** | 저장소에 없다. 따로 옮겨야 한다 (2 절) | |
| 디스크 | 케이스당 약 0.5 GB → 30 개면 **15 GB** | |
| 코어 | 12 분할 기준 12 코어 이상 | `nproc` |

---

## 2. 템플릿 케이스 — 이것부터 없으면 시작이 안 된다

생성기는 팬·재배단·캐노피·판정면만 만든다. **방 형상과 에어컨은 기존 케이스에서
복사**한다. 옮길 것은 이 여섯 가지뿐이고, 결과 시간 폴더는 필요 없다.

```
~/smartfarm-cfd/cases/acRoom-vane25/
  0.orig/                    U T p p_rgh k epsilon nut alphat
  constant/g
  constant/thermophysicalProperties
  system/blockMeshDict       반타원 O-그리드 4 블록, 0.10 m 균일, 84,024 셀
  system/topoSetDict         에어컨 취출 4 개 + 리턴
  system/createPatchDict
  system/fvSchemes  fvSolution
```

`constant/turbulenceProperties` 는 **옮기지 않아도 된다.** 생성기가 새로 쓴다.

**템플릿이 없는 컴퓨터라면** `origin/feat/real-cfd-case` 브랜치의 `cfd/case/` 에
위 파일이 대부분 들어 있다. 거기서 꺼내 위 구조로 놓으면 된다.

---

## 3. 미리 정해 둔 값 — 고칠 것 없다

### 격자

| | 값 |
|---|---|
| 방 전체 셀 한 변 | **0.10 m** (blockMesh, 84,024 셀) |
| 세분 상자 | **(−1.8, 1.2, 0.0) ~ (1.8, 2.8, 2.4)** m |
| 세분 상자 크기 | 3.6 × 1.6 × 2.4 m = **13.8 m³** (방의 약 17 %) |
| 그 안 셀 한 변 | **0.05 m** (refineMesh 1 단계) |
| 여유(버퍼) | **0.40 m** — 팬·캐노피에서 이만큼 띄웠다 |
| 세분 뒤 셀 수 | 약 **18 만** (84,024 → +96,767) |
| 팬 지름당 셀 | 2 → **4** |
| 캐노피 두께당 셀 | 2~3 → **5** |

세분 상자는 **30 케이스 전부 같은 좌표**다. 케이스마다 옮기면 조건 효과와 격자 효과가
섞인다. 팬이 꺼진 케이스도, 팬이 아예 없는 1 번도 같은 상자를 쓴다.

### 팬

| | 값 |
|---|---|
| 지름 · 두께 | **0.20 m · 0.08 m** |
| 기울기 | **15° 하방** |
| 기본 풍량 | **6.0 CMM** (= 0.1 m³/s), 토출 3.18 m/s |
| 추력 | **0.3724 N** (= ρ·Q·U, ρ 1.17) |
| 기본 대수 | 2 단 × 양 끝 = **4 대** |
| 모델 | `vectorSemiImplicitSource`, `volumeMode absolute` |

셀존 상자가 **실제 팬 치수와 같다**(0.05 m 격자 기준). 부풀림 없음.

### 캐노피

| | 값 |
|---|---|
| 영역 | 선반면 위 **0.25 m**, 단마다 2.4 × 0.8 m |
| 아래 단 | z 0.55 ~ 0.80 m |
| 위 단 | z 1.35 ~ 1.60 m |
| 모델 | `explicitPorositySource` / DarcyForchheimer |
| 점성저항 d | **25** (1/m²) |
| 관성저항 f | **1.3** (1/m) |
| 출처 | Zhang 외(2025) Agronomy 15:2326, 상추 |

### 해석

| | 값 |
|---|---|
| 솔버 | `buoyantPimpleFoam` |
| 난류 | **표준 k-ε** (기준선) |
| 물리 시간 | **600 초** |
| 저장 간격 | **30 초** |
| 시간 간격 | 자동 (`maxCo 1.0`, `maxDeltaT 0.5`) |
| 분할 | **12** (`--np 12`, `--cpus 12`) |

### 판정

| | 값 |
|---|---|
| 판정면 | 단마다 2 장 = **4 장**, 면당 4,961 점 |
| 높이(CFD z) | 0.675 / 0.800 / 1.475 / 1.600 m |
| 적정 구간 | **0.3 ~ 1.0 m/s** |
| 1 순위 | **P10** (가장 나쁜 면 기준) ≥ 0.3 |
| 2 순위 | 층간 차이, 작을수록 |

---

## 4. 순서 — 이대로 붙여 넣으면 된다

```bash
# 0) 이미지 (한 번)
docker pull opencfd/openfoam-default:2512

# 1) 케이스 펼치기 — 먼저 5 번 하나만
python3 src/make_foam_cases.py --cases 5-5 --end 600 --np 12 \
        --template ~/smartfarm-cfd/cases/acRoom-vane25 \
        --out ~/smartfarm-cfd/cases/fan-study

# 2) 돌리기
SF_REPO=$PWD bash src/run_foam_cases.sh 5 5

# 3) 검산 — 팬이 실제로 들어갔나
python3 -m src.check_fan --run ~/smartfarm-cfd/cases/fan-study/05_F3

# 4) 채점
python3 -m src.judge --runs ~/smartfarm-cfd/cases/fan-study
```

**여기까지 통과하면** 나머지를 돌린다.

```bash
python3 src/make_foam_cases.py --cases 1-30 --end 600 --np 12 \
        --template ~/smartfarm-cfd/cases/acRoom-vane25 \
        --out ~/smartfarm-cfd/cases/fan-study
SF_REPO=$PWD bash src/run_foam_cases.sh 1 30
python3 -m src.judge --runs ~/smartfarm-cfd/cases/fan-study --cdf
```

케이스당 **약 40 분**(11 코어 기준 추정), 30 개면 **약 30 시간**이다.
세션이 끊겨도 살아 있게 하려면 METHOD 11 절의 분리 컨테이너 방식을 쓴다.

---

## 5. 첫 판에서 확인할 것 셋

새 설정이 실제로 먹는지 보는 게 목적이다. `log.*` 를 순서대로 본다.

| 로그 | 봐야 할 것 |
|---|---|
| `log.refineMesh` | 정상 종료. 셀 수가 18 만 근처로 늘었나 |
| `log.checkMesh` | **비직교성 최대값** — rev2 격자의 이 숫자가 저장소에 처음 기록된다 |
| `log.topoSet` | `cellZoneSet fan_* now size` 가 **8 이상**. 미만이면 Allrun 이 스스로 멈춘다 |
| `log.run` | `explicitPorositySource` 를 읽고 죽지 않았나 |
| `check_fan.txt` | 셀 수 · 힘 밀도 · 희석 배수 |

---

## 6. 깨지면 볼 곳

| 증상 | 원인 | 조치 |
|---|---|---|
| `팬 셀 영역이 너무 작다 (8셀 미만)` | refineMesh 가 topoSet.fans 뒤에 돌았거나 실패 | Allrun 순서 확인. 세분이 셀 번호를 다시 매긴다 |
| `refineMesh` 가 키를 못 읽음 | v2512 문법 차이 | `system/refineMeshDict` 와 `$FOAM_TUTORIALS/mesh/refineMesh/refineFieldDirs` 대조 |
| `explicitPorositySource` 오류 | `coordinateSystem` 문법이 버전마다 다름 | `$FOAM_TUTORIALS/incompressible/porousSimpleFoam/angledDuct/common/constant/porosityProperties` 대조 |
| `surfaceFieldValue` 가 `bounds` 를 모름 | 키 이름 변경 | 그 블록만 빼고 돌려도 된다. 검산 ② 만 못 한다 |
| `There are not enough slots` | 분할 수 > 물리 코어 | `--np` 를 낮춘다 |
| 컨테이너가 쓰기 못 함 | 권한 | `--user "$(id -u):$(id -g)"` 확인 |

---

## 7. 바꿔 돌리는 법

```bash
# 캐노피 저항을 빼고 비교 (순위가 바뀌는지 확인 — 셀이 안 늘어 거의 공짜)
python3 src/make_foam_cases.py --cases 5-5 --canopy off ...
#   -> 05_F3_nocanopy 폴더가 따로 생겨 기준선을 덮지 않는다

# 난류 모델 민감도 (대표·극단 케이스 몇 개만)
python3 src/make_foam_cases.py --cases 5-5 --turbulence realizable ...
#   -> 05_F3_realizable

# 작물이 바뀌어 합격선이 달라졌을 때 — 계산을 다시 돌리지 않는다
python3 -m src.judge --runs ~/smartfarm-cfd/cases/fan-study --band 0.25 1.2
```

---

## 8. 아직 안 된 것 (계산을 돌려야 닫힌다)

- **격자 수렴(GCI)** — 대표 3~4 개를 0.025 m 로 다시 돌려 P10 이 5 % 안쪽인지.
  팬 4 셀은 문헌 권고(지름당 7~12)에 여전히 못 미친다.
- **난류 민감도** — 대표·극단 몇 개를 RNG / realizable 로 돌려 **순위가 유지되는지.**
- **캐노피 저항 유·무 비교** — 특히 H1·H2(팬 높이)와 T1~T3(각도)에서 순위가 뒤집히는지.
- **600 초가 충분한가** — 잔차가 아니라 마지막 구간의 시간평균과 변동폭으로 판단한다.
- **팬 P–Q 곡선** — 실물 팬이 정해지면 배치별 추력을 보정해야 한다. 지금은 배치가
  달라져도 풍량이 그대로라고 가정하고 있다.
- **조명 발열** — 이번 계산은 뺀다(`lighting.included = false`). 넣으면 부력이 달라져
  케이스 순위가 바뀔 수 있다.

---

## 9. 관련 문서

| 문서 | 내용 |
|---|---|
| `FAN-CFD-METHOD.md` | 방법 전체. 5 절 격자, 5-1 캐노피, 5-2 난류, 6 절 판정, 12 절 참고문헌 |
| `FAN-CFD-MESH-REFERENCES.md` | 격자 문헌 19 편 + 1 차 출처 지침. 선택지 A~D 와 비용 |
| `FAN-REFERENCES.md` | 팬 배치 문헌 |
| `FAN-CFD-ERRATA.md` | 오류 기록. E-001(팬이 계산에 안 들어간 사고) |
| `HANDOFF.md` | 이 프로젝트 전체(목데이터·UE 반입)의 이어가기 문서 |
