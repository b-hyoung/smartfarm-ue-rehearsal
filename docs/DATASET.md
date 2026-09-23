# 학습용 데이터셋 — PINO / PINN 입력

팬 스터디 CFD 결과를 납작한 CSV 로 편 것이다. `py -m src.make_fan_dataset` 가 만든다.

> **⚠ 먼저 읽어라 — 이 데이터에는 알려진 오류 셋이 들어 있다.**
> `cases.csv` 의 `err_*` 열에 표시돼 있고, 내용은 아래 **4 절**과
> `docs/FAN-CFD-ERRATA.md` E-004 · E-005 · E-006 에 있다.
> 절대값을 정답으로 학습시키면 그 오류까지 같이 배운다.

## 0. 어디에 무엇이 있나

| 파일 | 한 행이 무엇인가 | 크기 | 커밋 |
|---|---|---|---|
| `data/fan-dataset/cases.csv` | **케이스 1 건** — 방·재배단·팬·에어컨·격자·물리 조건 전부 | 30 행, 15 KB | ○ |
| `data/fan-dataset/scores.csv` | **케이스 × 판정면** — 분위수·평균·편차 | 100 행, 12 KB | ○ |
| `data/fan-dataset/fields/<run_id>.csv` | **판정면 × 시각 × 점** — 재배 베드 안, 300~450 초 | 케이스당 약 2 만 행 / 1.8 MB | ○ |
| `out/dataset/fields/<run_id>.csv` | 같은 것의 **방 전체 단면 × 전 시각** 판 | 케이스당 약 41 만 행 / 35 MB | ✕ |

`out/` 은 `.gitignore` 에 있다. 장(場) 은 다시 만들면 되므로 커밋하지 않는다.

```bash
py -m src.make_fan_dataset                    # 메타·점수 + 케이스별 CSV (베드 × 채점 구간)
py -m src.make_fan_dataset --fields           # 방 전체 단면·전 시각까지 (케이스당 35 MB)
py -m src.make_fan_dataset --fields --window-only   # 채점 구간 300~450 s 만 (1/3 크기)
```

`docs/FAN-RESULTS.md` 는 **"누가 언제 무엇을 돌렸나" 작업일지**다. 케이스별 표가 아니라
기계별 진행 기록이라 학습에 쓸 형태가 아니다. 그래서 이 데이터셋을 따로 만들었다.

## 1. 좌표와 단위

- **CFD 좌표**를 쓴다. `UE x = CFD x + 4.0`, y·z 는 같다.
- 방은 **반타원**이다. 평벽이 `y = 0`, 곡면 반장축 a = 4.0 m, 반단축 b = 5.7 m, 높이 2.7 m.
  바운딩박스 8.0 × 5.7 × 2.7, 실체적 **96.65 m³**. 직육면체가 아니다 — 격자를 정규화할 때 주의.
- 속도 m/s, 온도 **켈빈**, 길이 m, 풍량 CMM(= m³/min), 추력 N.
- 시간은 초. 해석 시작이 t = 0, 저장은 30 초 간격.

## 2. `cases.csv` — 케이스 조건

케이스 1 건이 1 행이다. 방 형상처럼 모든 케이스에 같은 값도 **행마다 반복해서 넣었다** —
학습 입력에 조건을 통째로 실어 보내기 쉽게 하기 위해서다.

| 묶음 | 열 |
|---|---|
| 식별 | `run_id` `no` `case` `group` `purpose` |
| 방 | `room_shape` `room_Lx_m` `room_Ly_m` `room_Lz_m` `room_volume_m3` |
| 재배단 | `rack_present` `rack_x_cfd_m` `rack_y_cfd_m` `bed_w_m` `bed_d_m` `tier0_z_m` `tier1_z_m` `tier_pitch_m` `canopy_h_m` `canopy_d_1_m2` `canopy_f_1_m` `rack_top_open` |
| 팬 | `fan_layout` `fan_n_per_side` `fans_on` `fan_cmm_each` `fan_cmm_total` `fan_tilt_deg` `fan_height_above_bed_m` `fan_dia_m` `fan_depth_m` `fan_outlet_m_s` `fan_thrust_N` `fan_src_N_m3` `fan_positions` |
| 에어컨 | `ac_on` `ac_x_cfd_m` `ac_y_cfd_m` `ac_z_m` `ac_total_cmm` `ac_supply_T_K` `ac_direction` `ac_slot_area_modeled_m2` `ac_outlet_modeled_m_s` |
| 물리 | `solver` `turbulence` `lighting_included` `wall_T_K` `rackwall_T_K` `wall_heat_W` `rackwall_heat_W` |
| 격자 | `mesh_base_m` `mesh_refined_m` `mesh_cells` |
| 실행 | `endTime_s` `snapshots_in_window` `wall_clock_s` |
| 오류 | `err_E004_ac_vertical` `err_E005_ac_slot_2x` `err_E006_rackwall_heat` |

### 알아둘 열

- **`fan_positions`** — 켜진 팬 **전부**의 위치와 방향을 `x,y,z,dx,dy,dz` 여섯 값으로 쓰고
  팬 사이는 `;` 로 잇는다. 두 단 몫이 다 들어 있다. 예(05_F3, 4 대):
  `-1.300,2.000,0.730,0.966,0.000,-0.259;1.300,2.000,0.730,-0.966,0.000,-0.259;...`
  팬은 벽면 경계가 아니라 **유동 영역 안의 운동량 소스**다(`fan_src_N_m3`).
- **`fan_layout`** — `pushpull`(한쪽에서 밀고 반대쪽에서 뽑음) / `ends`(양끝에서 같은 방향)
  / `top`(단 상부에서 하방) / `none`(팬 없음).
- **`rack_top_open` = 1** — 위 단 위로 막힘이 없다. 문헌의 식물공장은 각 단 천장이 LED 패널이라
  막혀 있다. 우리는 뚫려 있고, 이것이 실물과 맞는지는 아직 실측 전이다
  (`docs/specs/2026-09-24-rack-3tier-drop-bottom.md`).
- **`mesh_cells`** — 이 컴퓨터에서 직접 돌린 케이스만 채워진다. 다른 기계에서 받은 케이스는 빈칸.
- **`snapshots_in_window`** — 채점 구간 300~450 s 에 저장본이 몇 장 들어왔나. **6 이 정상**이다.
  1 이면 시간평균이 아니라 한 장짜리고(28·29·30), 0 이면 데이터가 없다(18·20·22).

## 3. `scores.csv` — 채점 결과

(케이스 × 판정면) 이 1 행. 판정면은 단마다 두 장, 모두 넉 장이다.

| 면 | z (CFD) | 뜻 |
|---|---|---|
| `tier0_canopy_mid` | 0.675 | 아래 단 캐노피 중간 (선반면 +0.125) |
| `tier0_canopy_top` | 0.800 | 아래 단 캐노피 윗면 (선반면 +0.250) |
| `tier1_canopy_mid` | 1.475 | 위 단 캐노피 중간 |
| `tier1_canopy_top` | 1.600 | 위 단 캐노피 윗면 |

열: `n_points` `snapshots` `P10` `P50` `P90` `mean` `cov` `band_ratio` `stagnant_ratio`
`spread` `P10_drift_pct` `T_mean_C` `T_sd` `pass_low` `pass_high`.

- 값은 **300 ~ 450 초 여섯 장을 점마다 시간평균한 뒤** 낸 분위수다. 순간값이 아니다.
- **적정 대역 0.3 ~ 1.0 m/s.** Sohn 외 2023 이 같은 대역을 쓴다(`band_ratio` 가 그 안의 비율,
  `stagnant_ratio` 가 0.1 m/s 미만).
- `P10_drift_pct` 는 평균 구간 뒷절반으로 다시 평균했을 때 P10 이 움직인 폭이다. 크면 구간이 짧다.
- **채점 범위는 재배 베드(x ±1.2, y 1.6~2.4) 전체**다. 판정면 자체는 방 전체 단면이라
  베드 바깥 점이 훨씬 많다 — 아래 `in_bed` 참고.

## 4. `fields/<run_id>.csv` — 실제 장(場)

한 행이 (판정면, 시각, 점) 하나다.

| 열 | 뜻 |
|---|---|
| `run_id` `plane` `tier` | 어느 케이스의 어느 면인가 |
| `t_s` | 시각(초). 30 초 간격, 보통 30 ~ 600 |
| `x_m` `y_m` `z_m` | CFD 좌표 |
| `Ux` `Uy` `Uz` `magU` | 속도 성분과 크기 (m/s) |
| `T_K` | 온도 (켈빈) |
| `in_bed` | 재배 베드 안이면 1. **베드 안은 전체의 약 17 %** 뿐이다 |
| `in_window` | 채점 구간 300~450 s 면 1 |

판정면은 방 전체 단면을 자른 것이라 방 구석 점까지 들어 있다. 채점은 베드 안만 쓰지만
(그렇게 안 했던 것이 E-002 였다) **학습에는 방 전체가 오히려 쓸모 있어 전부 남기고
`in_bed` 로 구분만 해 두었다.**

빈 `T_K` 는 그 점에서 온도 raw 가 없다는 뜻이다(속도와 온도의 샘플 점이 드물게 어긋난다).

## 5. ⚠ 학습 전에 반드시 알아야 할 것

### 5-1. 알려진 물리 오류 셋 — 30 케이스 전부에 들어 있다

| | 무엇 | 크기 |
|---|---|---|
| **E-004** | 에어컨 취출이 **수직 아래**다. 실물은 4Way 베인 **25°** | 이전 계산에서 방 기류 구조가 통째로 뒤집혔다 |
| **E-005** | 취출면이 격자보다 좁아 **2 배로 잡혔다**. 실측 0.060 m² | 풍량은 맞고 **운동량이 절반** (1.74 m/s, 설계 3.47) |
| **E-006** | 재배단 선반이 방 외벽의 **29 ℃ 고정**을 물려받았다 | 캐노피 바로 아래에서 **278 W** 주입. 뺀 조명열 480 W 의 58 % |

`cases.csv` 의 `err_E004_ac_vertical` `err_E005_ac_slot_2x` `err_E006_rackwall_heat` 로 표시해 뒀다.
**지금은 모든 행이 1 이다.** 고친 뒤 다시 돌리면 0 이 되고, 그때 두 벌을 대조군으로 쓸 수 있다.

영향의 크기는 캐노피 풍속 기준으로는 작다 — 에어컨만 켠 02_R1 의 P90 이 0.206,
팬을 켠 05_F3 이 1.333 로 **6.5 배** 차이다. 하지만 방 규모 재순환과 부력에는 작지 않다.

### 5-2. 데이터가 고르지 않다

- **24 케이스**만 채점 구간 여섯 장이 다 찼다 (1~17, 19, 21, 23~27).
- **28 · 29 · 30** 은 300 초에서 멈춰 **한 장**뿐이다. 시간평균이 아니다.
- **18 · 20 · 22** 는 데이터가 없다.
- `08_F6` 은 510 초, `16_L2` 는 450 초에서 끝났다. 판정 구간은 덮으므로 채점에는 문제없다.

### 5-3. 물리 설정

- 과도해석(`buoyantPimpleFoam`), 표준 k-ε, 적응 Δt(`maxCo 1.0`).
- **조명 발열을 뺐다**(`lighting_included = 0`). 대신 벽 1458.5 W + 선반 278.3 W 가
  의도치 않게 들어가 있다(E-006).
- 캐노피는 DarcyForchheimer 다공체. `d` 25 1/m², `f` 1.3 1/m — Zhang 외 2025 상추.
  Sohn 2023 은 같은 작물에 `C1` 50, `C2` 2 를 쓴다. **저항값이 정해진 상수가 아니다.**
- 벽은 29 ℃ 고정. 단열도 대류계수도 아니다.

## 6. 읽는 예

```python
import pandas as pd

cases  = pd.read_csv("data/fan-dataset/cases.csv")
scores = pd.read_csv("data/fan-dataset/scores.csv")

# 쓸 수 있는 케이스만
ok = cases[cases.snapshots_in_window == 6].run_id

# 한 케이스의 장(場) — 이미 베드 안 · 채점 구간만 담겨 있다
f = pd.read_csv("data/fan-dataset/fields/05_F3.csv")

# 방 전체가 필요하면 (--fields 로 따로 만든 것)
# f = pd.read_csv("out/dataset/fields/05_F3.csv")

# 조건을 장에 붙인다
f = f.merge(cases, on="run_id")

# 팬 위치 풀기
def fans(s):
    if not isinstance(s, str) or not s:
        return []
    return [tuple(float(v) for v in p.split(",")) for p in s.split(";")]
```

## 7. 볼륨 데이터가 필요하면

판정면 넉 장으로는 3D 를 못 채운다. 방 전체 볼륨은 따로 뽑는다 —
`docs/VDB-EXPORT.md` 의 세 단계다.

```bash
bash src/export_volume.sh 05_F3          # processor*/ -> 0.1 m 간격 수평면 27 장
py   -m src.volume_frames --case 05_F3   # -> out/frames/05_F3/frame_NN.csv (x,y,z,T,Ux,Uy,Uz)
```

**`processor*/` 가 남아 있는 케이스만 된다** — 이 컴퓨터에서 직접 돌린 것들이다.
다른 기계에서 받은 케이스는 판정면만 커밋돼 있다.
