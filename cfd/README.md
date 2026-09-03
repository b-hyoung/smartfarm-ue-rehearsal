# cfd — 진짜 CFD 파이프라인

레포 루트의 `src/` 는 **목데이터** 생성기다(진짜 CFD 나오기 전 UE 파이프를 미리 짜려고 만든 것).
이 폴더는 그 목데이터를 대체하는 **실제 OpenFOAM 시뮬레이션**이다.

두 경로가 내는 CSV 스키마는 완전히 같다 — `x,y,z,T,Ux,Uy,Uz,p,source`.
UE 쪽 코드는 어느 쪽에서 왔는지 몰라도 된다. **폴더만 바꿔 끼우면 된다.**

```
목  : src/generate_frames.py  ->  data/frames/frame_00..14.csv
실  : cfd/sweep.sh            ->  cfd/frames/<조건>/frame_00..14.csv
```

## 무엇이 들어 있나

| 경로 | 내용 |
|---|---|
| `case/` | OpenFOAM 케이스 설정 일체 (메시 정의, 초기·경계조건, 스킴, 함수객체) |
| `case/RUN.sh` | 케이스 1개를 메시부터 재조립까지 실행 |
| `sweep.sh` | 조건을 바꿔가며 여러 케이스를 돌리고 프레임까지 뽑음 |
| `extract_frames.py` | 케이스 → `frame_*.csv` + `manifest.json` (ParaView pvbatch) |
| `real-values.json` | 실제 실행에서 나온 값·실측 범위·목데이터와 어긋나는 지점 |

메시(`constant/polyMesh`)와 계산 결과는 커밋하지 않는다 — `blockMesh` 가 매번 다시 만든다.

## 준비물

**OpenFOAM v2512** — 도커가 가장 간단하다. 설치할 필요 없다.

```bash
docker pull opencfd/openfoam-default:2512
```

**ParaView** — 프레임 CSV 추출용. `pvbatch` 만 있으면 되고 GUI 는 필요 없다.
(개발에 쓴 버전: 6.1.1)

> **함정**: Ubuntu 24.04 이상에는 `libgomp1` 이 기본 설치되지 않아 `pvbatch` 가
> `libgomp.so.1: cannot open shared object file` 로 죽는다. 둘 중 하나로 해결한다.
>
> ```bash
> sudo apt install libgomp1                       # 시스템에 설치하거나
> export LD_LIBRARY_PATH=$HOME/opt/deps/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
> ```

## 케이스 1개 돌리기

```bash
# 1) 케이스 사본 만들기 (원본은 그대로 둔다)
mkdir -p runs && cp -r cfd/case runs/mycase

# 2) 솔버 실행 — 8코어 기준 약 2시간 43분
docker run --rm -v "$PWD/runs:/data" opencfd/openfoam-default:2512 \
    bash -c "cd /data/mycase && NP=8 ./RUN.sh"

# 3) UE 프레임 뽑기
pvbatch cfd/extract_frames.py runs/mycase cfd/frames/mycase
```

## 조건 바꿔가며 여러 개 돌리기

```bash
cfd/sweep.sh              # 정의된 조건 전부
cfd/sweep.sh flow30_289K  # 하나만
DRYRUN=1 cfd/sweep.sh     # 계획만 확인
```

기본으로 잡아둔 조건은 이렇다. 기준선에서 **한 번에 한 변수만** 움직인다.

| 이름 | 풍량 | 토출온도 | 보려는 것 |
|---|---|---|---|
| `base_25cmm_289K` | 25 CMM | 289.5 K | 기준 (지금 UE 에 들어가 있는 조건) |
| `flow30_289K` | 30 CMM | 289.5 K | 세게 틀면 고르게 퍼지나 / 작물에 바람이 직접 닿나 |
| `flow20_289K` | 20 CMM | 289.5 K | 에너지 절감 시나리오 |
| `temp292_25cmm` | 25 CMM | 292.0 K | 급랭 완화 (작물 스트레스) |

조건을 더 넣거나 바꾸려면 `sweep.sh` 위쪽 `VARIANTS` 배열만 수정하면 된다.
값은 `foamDictionary` 로 `0.orig/T`(토출온도)와 `0.orig/U`(체적유량)에 주입된다.

**케이스당 약 2시간 43분**이다(8코어, 900초 시뮬). 4개면 순차 11시간이니 밤에 걸어두는 걸 권한다.
16코어에서 2개를 동시에 돌리면 절반으로 줄지만 CPU 를 꽉 채우므로 UE 작업과 겹치면 안 된다.

## 산출물

```
cfd/frames/<조건>/
    frame_00.csv .. frame_14.csv     # 각 89,600행
    manifest.json                    # 그 케이스의 조건·프레임별 시각
```

CSV 한 행은 메시 절점 하나다.

| 열 | 단위 | 비고 |
|---|---|---|
| `x,y,z` | m | x 는 CFD 좌표(-4..4)에서 **+4.0 시프트**해 UE 좌표(0..8)로 맞춤 |
| `T` | K | 섭씨로 쓰려면 −273.15 |
| `Ux,Uy,Uz` | m/s | |
| `p` | Pa | 절대압 |
| `source` | — | 항상 `simulated`. "가짜"가 아니라 "실측이 아닌 계산값"이라는 뜻 |

## 추출 방식이 왜 이런가 (검증 기록)

`extract_frames.py` 는 기존 `out/ue_frames/*.csv` 를 그대로 재현하도록 맞췄다.
같은 케이스에 돌려 대조한 결과 — 온도 최대 0.005 K, 속도 최대 0.0001 m/s,
좌표 최대 0.1 mm 차이(전부 CSV 자릿수 반올림 수준), 프레임 시각 15개 전부 일치.

맞추는 과정에서 걸린 것 둘:

- **리더의 셀→점 보간을 쓰면 안 된다.** `Createcelltopointfiltereddata=1` 로 두면
  경계 패치 값이 점에 그대로 얹힌다. `walls` 가 `fixedValue $internalField` = 302 K
  (29 °C)라 방 외피 약 10,800점이 302 K 로 칠해져 내부 기류가 안 보인다.
  대신 `CellDatatoPointData` 필터로 **인접 셀 평균**만 쓴다 = 공기 온도장.
- **t=0 은 폴더 스캔으로 안 잡힌다.** `SkipZeroTime=0` 만으로는 부족하고
  `ListtimestepsaccordingtocontrolDict=1` 이라야 0초가 목록에 들어온다.
  대신 controlDict 에만 있고 안 써진 시각이 섞일 수 있어 디스크와 대조해 걸러낸다.

## ⚠ 주의

- **`RUN.sh` 는 시작할 때 이전 결과를 지운다** (`processor*`, 시간 디렉터리, `log.*`).
  반드시 사본에서 돌릴 것. `sweep.sh` 는 그렇게 하도록 짜여 있다.
- `NP` 는 `case/system/decomposeParDict` 의 분할 수와 맞아야 한다.
- 프레임 CSV 는 조건당 93 MB 다. `.gitignore` 에 걸려 있으니 커밋되지 않는다.
- **UE 컬러맵과 화살표 스케일은 `geometry.json`(목값)이 아니라 `real-values.json` 을 봐야 한다.**
  실측 온도 하한이 17.82 °C(목 20.0), 최대 유속이 1.846 m/s(목 0.8)다.
