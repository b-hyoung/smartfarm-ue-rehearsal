# CFD 결과를 VDB 로 — 팬 스터디

언리얼 Sparse Volume Texture 로 방 전체 기류·온도를 띄우려면 `.vdb` 시퀀스가 필요하다.
채점에 쓰는 캐노피 판정면(raw)은 **평면 넉 장뿐**이라 볼륨이 안 된다. 원본 볼륨을 따로 뽑는다.

## 한 줄 요약

```bash
bash src/export_volume.sh 05_F3          # processor*/ -> 수평면 raw   (몇 분)
py   -m src.volume_frames --case 05_F3   # raw -> out/frames/05_F3/*.csv
bash src/make_vdb.sh 05_F3               # csv -> out/vdb/05_F3/*.vdb
```

세 단계 다 도커로 돈다. `05_F3` 자리에 케이스 폴더 이름을 넣는다.

## 어떤 케이스에 되나

**`processor*/` 저장본이 남아 있는 케이스만 된다.** 즉 이 컴퓨터에서 직접 돌린 것들이다.
다른 컴퓨터에서 받은 케이스는 `postProcessing.tar.gz`(판정면)만 커밋돼 있어 볼륨이 없다.
필요하면 그 케이스를 여기서 다시 돌려야 한다.

확인:

```bash
ls ~/smartfarm-cfd/cases/fan-study/05_F3/processor0
```

시각 폴더(`300 330 … 600`)가 보이면 된다.

## 1단계 — 볼륨 뽑기 `src/export_volume.sh`

방을 **0.1 m 간격 수평면 27 장**으로 잘라 `U`·`T` 를 raw 로 쓴다.
`src/make_volume_dict.py` 가 `system/volumeGrid` 를 먼저 써 넣고,
`mpirun postProcess -parallel -func volumeGrid` 가 분할본에서 바로 읽는다.

**`reconstructPar` 를 쓰지 않는다.** 전체 셀을 합치면 케이스당 수십 분에 1 GB 가 더 붙는데,
VDB 복셀이 어차피 0.1 m 라 그만큼의 해상도가 필요 없다. 0.1 m 격자에서 수평면 하나를 자르면
그 층의 셀을 한 번씩 지나므로 담을 정보는 다 담긴다.

```bash
bash src/export_volume.sh 05_F3            # 300 초 이상 전부
TIMES=450,600 bash src/export_volume.sh 05_F3   # 고른 시각만
FROM=0 bash src/export_volume.sh 05_F3     # 처음부터
```

해가 돌고 있는 중에도 된다 — `mpirun --oversubscribe` 를 붙여 뒀고, `postProcess` 는
읽고 자르기만 해 코어를 오래 쥐지 않는다.

결과: `<케이스>/postProcessing/volumeGrid/<시각>/{U,T}_zNNN.raw`, 로그는 `log.volumeGrid`.

⚠ 재배단·팬 상자는 0.05 m 로 세분돼 있다. 그 구간은 한 복셀에 세분 셀이 여러 개 들어가
평균된다. VDB 해상도가 0.1 m 이므로 의도된 결과다.

## 2단계 — 프레임 CSV `src/volume_frames.py`

한 시각의 면 27 장을 한 파일로 합친다.

```bash
py -m src.volume_frames --case 05_F3
py -m src.volume_frames --case 05_F3 --from-time 0
```

`out/frames/05_F3/frame_NN.csv` — 열은 `x,y,z,T,Ux,Uy,Uz`. **온도는 켈빈, 좌표는 CFD 좌표**다.
`manifest.json` 에 시각과 점 개수가 남는다. 한 프레임이 약 28 만 점, 15 MB 다.

열 이름은 master 브랜치 `data/frames` 규약과 같게 맞췄다.

## 3단계 — VDB `src/make_vdb.sh`

0.1 m 복셀 **80 × 57 × 27** 격자에 평균으로 담아 `.vdb` 로 쓴다.
격자 두 장이 들어간다.

| 격자 | 내용 |
|---|---|
| `temperature` | 0 ~ 1 정규화. ℃ = `t_min` + v × (`t_max` − `t_min`) |
| `speed` | m/s 그대로 |

```bash
bash src/make_vdb.sh 05_F3
VDB_SCALE="--tmin 15 --tmax 30" bash src/make_vdb.sh 05_F3
```

**색척도 기본값은 17 ~ 27 ℃ 다.** master 파이프라인의 18.5 ~ 29 ℃ 가 아니다 —
이번 계산은 **조명 발열을 빼고** 풀어서 방이 그만큼 차다(05 F3 에서 17.4 ~ 26.7 ℃).
척도는 시퀀스 내내 고정이라야 프레임끼리 비교가 되므로 자동 맞춤을 쓰지 않는다.
실제로 쓴 값은 `out/vdb/<케이스>/scale.json` 에 남는다.

좌표는 여기서 **UE 로 되돌린다**(CFD x + 4.0 = UE x). 복셀 한 변이 10 UE 단위라
임포트 뒤 방 800 × 570 × 270 에 그대로 맞는다.

openvdb 는 윈도우·맥 파이썬에 없어서 `sf-openvdb:1` 이미지를 한 번 굽고 재사용한다
(처음 한 번만 2 ~ 3 분).

## 4단계 — 언리얼

`ue/sf_import_vdb.py` 가 master 브랜치에 있다. 첫 파일 하나만 지정하면 임포터가
`.####.` 패턴을 보고 애니메이션 SVT 를 만든다.

```
py ue/ue_exec.py -f ue/sf_import_vdb.py
```

⚠ 컴포넌트의 `FrameTransform` 동기화는 **재생 틱에서만** 일어난다
(엔진 `HeterogeneousVolumeComponent.cpp`). 갓 임포트하면 1/10 크기로 보이다가
시퀀서 재생이나 PIE 를 한 번 거치면 방 크기로 맞는다.

## 확인된 것

2026-09-23, `05_F3` 600 초 한 장으로 세 단계 전부 돌려 봤다.

```
frame_00.csv  t= 600.0 s  점 280231
sf_05_F3.0000.vdb  t=600s  채운 복셀 93044/123120  T 17.4~26.7℃  |U| ~3.17
```

채운 복셀이 123,120 중 93,044(75.6 %)인 것은 방이 **반타원**이라 직육면체
바운딩박스의 약 78 % 만 차지하기 때문이다 — 맞는 값이다.

## 용량

| | 한 프레임 | 300 ~ 600 초 11 장 |
|---|---|---|
| raw (volumeGrid) | 약 20 MB | 약 220 MB |
| frames CSV | 15 MB | 165 MB |
| vdb | 0.65 MB | 7 MB |

`out/` 은 커밋하지 않는다. `.vdb` 만 필요하면 그것만 따로 올린다.
