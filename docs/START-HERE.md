# 바로 시작하기 — 팬 스터디 30 케이스

이 문서 하나만 읽으면 다른 컴퓨터에서 바로 돌릴 수 있게 적는다.
**정해진 값은 전부 아래 표에 있고, 손으로 고칠 것은 없다.** 배경과 근거는
`FAN-CFD-METHOD.md`, 격자 문헌은 `FAN-CFD-MESH-REFERENCES.md` 에 있다.

작성 2026-09-21 · 브랜치 `feat/rack-fans`

---

## 0. 한 줄 상태

케이스 생성·격자 세분·캐노피 다공체·검산·채점까지 **코드는 다 됐다.**
2026-09-21 에 5 번 케이스로 첫 판을 돌려 **`refineMesh`·`explicitPorositySource`·
`surfaceFieldValue` 가 v2512 에서 도는 것까지 확인했다.** 가는 길에 환경 문제 다섯을
밟았고 전부 고쳐 코드에 넣었다(5-1 절). 600 초 완주와 30 케이스 배치는 아직이다.
새 컴퓨터에서도 **5 번 하나부터** 돌려 확인하고 나머지로 간다.

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
| 코어 | 많을수록 좋다. 실행기가 기본으로 80 % 를 쓴다 | `nproc` |

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
| 분할 | **코어의 80 %** — 24 코어면 `--np 18`, `--cpus 19` |

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
python3 src/make_foam_cases.py --cases 5-5 --end 600 --np 18 \
        --template ~/smartfarm-cfd/cases/acRoom-vane25 \
        --out ~/smartfarm-cfd/cases/fan-study

# 2) 돌리기
SF_REPO=$PWD bash src/run_foam_cases.sh 5 5      # 코어는 알아서 80 %

# 3) 검산 — 팬이 실제로 들어갔나
python3 -m src.check_fan --run ~/smartfarm-cfd/cases/fan-study/05_F3

# 4) 채점
python3 -m src.judge --runs ~/smartfarm-cfd/cases/fan-study
```

**여기까지 통과하면** 나머지를 돌린다.

```bash
python3 src/make_foam_cases.py --cases 1-30 --end 600 --np 18 \
        --template ~/smartfarm-cfd/cases/acRoom-vane25 \
        --out ~/smartfarm-cfd/cases/fan-study
SF_REPO=$PWD bash src/run_foam_cases.sh 1 30
python3 -m src.judge --runs ~/smartfarm-cfd/cases/fan-study --cdf
```

케이스당 시간은 첫 판에서 실측한다. 옛 기록(0.10 m · 11 코어)에서 환산하면
세분 뒤 셀이 2.2 배, 시간 간격이 절반이라 **약 4.3 배**다.
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

## 5-1. 실제로 밟은 함정 다섯 (2026-09-21, 윈도우 + Docker Desktop)

이미 고쳐서 코드에 들어가 있다. **새로 만든 케이스에는 안 나온다.** 다만 손으로
케이스를 만들거나 옛 케이스를 되살릴 때 같은 자리에서 걸리므로 기록해 둔다.
다섯 다 격자나 물리 문제가 아니라 **환경·문법 문제**였고, 하나씩 순서대로 나타났다.
앞 단계를 고쳐야 다음 오류가 드러나는 구조라 순차적으로 깰 수밖에 없었다.
격자 쪽은 첫 판부터 깨끗했다 — 178,000 셀, 비직교성 최대 54.2, 팬 셀존 32 셀씩.

### ① Allrun 이 CRLF 로 저장돼 컨테이너가 못 읽음

```
bash: line 1: ./Allrun: cannot execute: required file not found
```

윈도우 파이썬이 줄바꿈을 LF 가 아니라 CRLF 로 써서, shebang 줄 끝에 캐리지리턴이
붙는다. 리눅스는 그런 이름의 인터프리터를 못 찾는다. 파일은 멀쩡해 보이고 오류
문구도 엉뚱해서 찾기 어렵다.

**고침** — `make_foam_cases.py` 의 `wopen()` 이 생성 파일을 전부 LF 로 쓴다
(`newline=chr(10)`). 확인은 `file Allrun` 이 `CRLF` 를 말하지 않으면 된다.

### ② subsetMesh 가 만든 rackWalls 패치가 `type empty`

```
--> FOAM FATAL IO ERROR: inconsistent patch and patchField types for
    patch type empty and patchField type fixedValue
    file: 0/T/boundaryField/rackWalls
```

`subsetMesh -patch rackWalls` 가 노출면 4,512 장짜리 패치를 만들면서 타입을
`empty` 로 준다(v2512). `0/` 쪽은 `walls` 를 복사해 `fixedValue` 라 어긋난다.
면이 0 장이면 몰라도 4 천 장이 `empty` 인 것은 명백한 오류인데 메시 단계에서는
아무 말이 없고 **솔버 첫 스텝에서야 죽는다.**

**고침** — Allrun 이 subsetMesh 바로 뒤에서 고친다.

```bash
foamDictionary constant/polyMesh/boundary -entry entry0/rackWalls/type -set wall
foamDictionary constant/polyMesh/boundary -entry entry0/rackWalls/inGroups -set '1(wall)'
```

같은 이유로 사람 쾌적도 필드(`PMV`·`PPD`·`DR`)는 아예 지운다. 작물에 의미가 없고
`rackWalls` 항목이 없어 읽다가 죽는 원인만 된다.

### ③ mpirun 이 root 실행을 거부

```
mpirun has detected an attempt to run as root.
```

윈도우 바인드 마운트에는 uid 매핑이 없어 `--user "$(id -u):$(id -g)"` 를 쓸 수 없고,
그러면 컨테이너가 root 로 돈다. OpenMPI 가 이를 막는다.

**고침** — `run_foam_cases.sh` 가 윈도우를 감지해 환경변수로 푼다.

```bash
-e OMPI_ALLOW_RUN_AS_ROOT=1 -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
```

리눅스·맥에서는 `--user` 를 그대로 쓴다. 이 변수는 윈도우에서만 붙는다.

### ④ explicitPorositySource 딕셔너리 구조

```
Entry 'selectionMode' not found in dictionary
    "canopy_t0/explicitPorositySourceCoeffs"
```

`selectionMode` 와 `cellZone` 을 항목 맨 위에 두면 안 된다. **`explicitPorositySourceCoeffs`
안에** 들어가야 하고, 그 안에 다공체 모델 `type DarcyForchheimer` 가 또 온다.
`vectorSemiImplicitSource`(팬)는 반대로 맨 위에 두는 구조라 헷갈린다.

```
canopy_t0
{
    type            explicitPorositySource;
    active          yes;

    explicitPorositySourceCoeffs
    {
        selectionMode   cellZone;
        cellZone        canopy_t0;
        type            DarcyForchheimer;
        d               (25 25 25);
        f               (1.3 1.3 1.3);
        coordinateSystem { origin (0 0 0); e1 (1 0 0); e2 (0 1 0); }
    }
}
```

### ⑤ surfaceFieldValue 가 `name` 을 요구

```
Entry 'name' not found in dictionary "functions/fanflux_fan_t0_s0"
```

`regionType sampledSurface` 를 쓰면 `sampledSurfaceDict` 만으로는 안 되고 **`name` 항목이
따로 있어야 한다.** 함수오브젝트 이름과 같게 넣으면 된다.

```
fanflux_fan_t0_s0
{
    type            surfaceFieldValue;
    regionType      sampledSurface;
    name            fanflux_fan_t0_s0;     // <- 이것
    sampledSurfaceDict { ... }
    operation       areaNormalIntegrate;
    fields          (U);
}
```

### 덤 — 도커 쪽 둘

- **이미지 엔트리포인트가 작업 디렉터리를 되돌린다.** `-w` 를 믿으면
  `cannot find file "/data/system/controlDict"` 가 난다. 컨테이너 **안에서 직접 `cd`** 한다.
- **Git Bash 는 도커 인자의 경로를 제멋대로 바꾼다.** `MSYS_NO_PATHCONV=1` 을 켜고
  `cygpath -w` 로 윈도우 경로를 만들어 넘긴다. 둘 다 `run_foam_cases.sh` 에 들어 있다.

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
