# 트윈 구조 — 임시값과 교체 지점

2026-09-11 기준.

## 루프

```
임시값으로 구동 (지금) → 실측 도착(R1) → 어긋남 발견 → PINN 이 입력값 역산·보정
→ 보정된 CFD 재계산 → PINO 재학습 → 실시간 예측 교체
```

## 역할

| 것 | 역할 | 화면 연결 |
|---|---|---|
| 수식 모델 (`src/models/`) | 즉석 예측 — [SF 갱신]이 돌림. 신경망 아님, 상수는 vane25 단순 피팅 | ✅ 유일 |
| 실측 (R1) | 임시값이 틀렸는지 판정 | — |
| PINN (`src/ml/`) | 틀린 입력값(벽 열손실, 풍량 등)을 실측에서 역산. 리허설만 완료 | ❌ 아직 |
| PINO (`src/ml/`) | 보정된 CFD 를 학습해 실시간 응답 (검사 기능 없음). 리허설만 완료 | ❌ 아직 |

> 헷갈림 방지(9/15): 화면의 예측은 전부 **수식**이다. PINN/PINO 는 아직
> 파이프라인에 연결돼 있지 않다. 화면 데이터 출처는 `data/frames/manifest.json`
> 의 `source` 가 정답 (`acRoom-vane25`=진짜 CFD, `MOCK-live`=수식).

## 임시값 → 교체 지점

| 임시값 | 현재 | 파일 | 교체 트리거 |
|---|---|---|---|
| 온도·기류 예측 | 수식 모델 | `src/models/predict_mock.py` | 케이스 라이브러리 → PINO |
| 조명 발열 | 480 W (240×2단) | `src/models/vane_mock.py` LIGHT_W | 스펙시트 소비전력 |
| 배광 | 반각 35° 근사 | `web/3d.html`, UE RectLight | IES 파일 (LM-63) |
| 냉방 COP | 3.5 (1등급 추정) | `src/models/power_model.py` COP | 전력 실측 |
| 방 열손실 | 641 W/K (역산) | `src/models/vane_mock.py` UA_EFF | PINN 재역산 |
| 재배단 기류 차단 | 없음 (열원만) | CFD 케이스 | 재배단 포함 격자 재계산 |
| PINO 교재 | mock 750쌍 | `src/ml/make_dataset.py` | 진짜 CFD 케이스 |
| 실측 | CFD 백업 2케이스(가짜) | `data/archive/vane25`, `data/archive/vert` | R1 실측 CSV (스키마 동일) |
| PINN 역산 | 격자 최소제곱 3파라미터 | `src/ml/pinn_check.py` | 후보: DeepXDE 리허설 (아래) |
| PINN 본체 | DeepXDE 역문제 리허설 | `src/ml/pinn_rehearsal.py` | 실측 CSV + (필요시) 이류 포함 물리 |

## 검사 실행 (PINN 자리)

```
py -m src.ml.pinn_check data/archive/vane25/probes.csv        # 실측 오면 경로만 교체
```

잔차 → dT_end(열부하/UA)·s_tau(풍량)·s_delay(유로) 역산 → 판정
(≤0.5℃ 적합 / ≤1.0 주의 / 초과 불일치). 결과 `data/pinn_check.json`.
현재(가짜 실측): vane25 보정 후 0.55℃ · vert 1.55℃ = 불일치 감지 ✓

```
py -m src.ml.pinn_rehearsal        # DeepXDE PINN 리허설 (GPU ~6분)
```

센서 12점 + 단순화 열수지만으로 장 복원 → 단면 정답지 채점:
PINN 0.62/0.90℃ vs mock 수식 1.57/1.92℃ (수평/수직). Wei & Ooka(2023) 방식.
근거·한계·skopt DLL 우회는 파일 머리주석. 결과 `data/pinn_rehearsal.json`.

## 임시값 검증 ↔ 실측 매핑

| 임시값 | 검사 센서 |
|---|---|
| 배광 모양 | PPFD (선반 위 수 지점) |
| 조명 발열 | 전력계 |
| 온도장 | 온도 A~D (0.1/1.1/1.7 m) |
| 냉방 전력 | 전력계 |

## 데이터 계약 (바꾸면 전부 깨짐)

- 좌표: UE m, x = CFD x + 4.0. 방 8.0×5.7×2.7 D자
- frames: `x,y,z,T(K),Ux,Uy,Uz,p,source` + manifest(time_s), 15프레임 0~900 s
- slices/jets/probes 스키마 = 각 make_* 헤더 참조
- PINO 교재: `data/dataset/meta.json`

## 제조사 요청 (조명)

① IES(LM-63) ② 스펙시트(소비전력·PPF) ③ 스펙트럼(가능 시).
IES 없는 모델은 선정 제외.
