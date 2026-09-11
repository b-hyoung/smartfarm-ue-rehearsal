# PINN 리허설 결과 — 센서 12점으로 방 전체 온도장 복원

2026-09-11. 코드 `src/pinn_rehearsal.py` · 결과 `data/pinn_rehearsal.json`

## 한 줄 요약

센서 12점의 시계열만 주면, PINN이 물리식과 함께 방 전체 온도장을
**평균 오차 0.62℃**로 복원한다 (기존 수식 모델은 1.57℃).

## 데이터 흐름

```
가짜 실측 = vane25 CFD 결과 (data/_real-vane25/)
   │
   ├─ 센서 12점 시계열만 PINN에 입력  (A~D × 0.1/1.1/1.7 m, 0~900 s)
   │      + 물리: 단순화 열수지 u_t = aΔu + k(u_eq − u), 미지수 a·k·u_eq 역산
   │
   └─ 나머지 전체 단면은 채점용 정답지로만 사용 (PINN은 못 봄)
```

## 채점 (RMS 오차, ℃ — 온도가 아니라 "정답과 몇 도 어긋나는가")

| 채점면 | PINN (12센서) | 기존 mock 수식 |
|---|---|---|
| 1.1 m 수평 단면 (~5,600점 × 15시각) | **0.62** | 1.57 |
| 2.0 m 수직 단면 (~3,100점 × 15시각) | **0.90** | 1.92 |

방 온도가 900초간 28.85→21℃대(약 7℃ 변화)로 움직이는 걸 평균 0.6℃
이내로 추적 — 실무 온도센서 자체 오차(±0.5℃) 수준의 복원.

## 역산된 미지 입력

| 값 | 결과 | 해석 |
|---|---|---|
| 냉각 시정수 | 304 s | 방이 식는 속도 |
| 유효확산 | 9×10⁻² m²/s | 분자확산의 수천 배 = 난류 혼합 스케일 (정상) |
| 평형온도 | 16.4℃ | ⚠ 아래 주의 |

## 주의 (정직하게)

- 평형온도가 급기온도와 같게 나옴 — 900초 안에 평형 미도달이라
  냉각률×온도차 **곱만** 데이터에 구속됨. 역산값 개별 해석은 조심.
- 정답지 채점은 가짜 실측(CFD)이라 가능했던 것. 진짜 실측 땐 이 수치가
  "PINN을 믿는 근거"로 남는다.
- 물리는 이류(바람) 생략한 단순판 — PINN 실패모드 문헌 권고대로 쉬운
  방정식부터. 필요 시 이류 추가가 다음 단계.

## 실행 · 교체 지점

```
py -m src.pinn_rehearsal          # GPU ~6분 (deepxde 1.15 + torch/cu126)
```

- 실측 도착 → 입력 CSV 경로만 교체 (스키마 `t_s,point,ue_x,ue_y,z,T_C`)
- `pinn_check.py`(격자 최소제곱, 판정)와 공존 — 실측에서 잘 맞는 쪽 채택

## 근거

- Wei & Ooka, *Indoor airflow field reconstruction using PINN*,
  Building and Environment (2023) — 방식
- [DeepXDE 역문제 데모](https://deepxde.readthedocs.io/en/latest/demos/pinn_inverse/diffusion.1d.inverse.html) — 구현 틀
- Raissi et al., J. Comput. Phys. (2019) — PINN 원전
- ⚠ 이 PC 앱 제어 정책이 sklearn DLL 차단 → skopt 스텁 우회
  (`src/pinn_rehearsal.py` 머리주석, hanes `pandas-dll-blocked-sac.md`)
