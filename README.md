# smartfarm-ue-rehearsal

반원 800×570×270cm 공간의 냉각 데이터를 만들어, 언리얼(Niagara) "온도색 기류"
시각화 파이프에 넣는다. 데이터 경로가 두 개이고 **둘의 CSV 스키마는 완전히 같다**.

| | 무엇 | 내는 것 |
|---|---|---|
| **목(mock)** | `src/` — 가짜 5분 냉각 데이터. 진짜 CFD 오기 전 파이프 리허설용 | `data/frames/` |
| **실(real)** | `cfd/` — 실제 OpenFOAM 시뮬레이션 (`buoyantPimpleFoam`, v2512) | `cfd/frames/<조건>/` |

UE 쪽 코드는 어느 쪽에서 왔는지 몰라도 된다 — 폴더만 바꿔 끼우면 된다.
진짜 시뮬레이션을 돌리는 법은 **[`cfd/README.md`](cfd/README.md)** 를 볼 것.

> ⚠ UE 컬러맵·화살표 스케일은 `geometry.json`(목값)이 아니라
> [`cfd/real-values.json`](cfd/real-values.json) 의 실측 범위로 맞춰야 한다.
> 실제 온도 하한이 17.82 °C(목 20.0), 최대 유속이 1.846 m/s(목 0.8)다.

## 목데이터 경로

- 설계(spec): `docs/specs/2026-09-03-ue-rehearsal-mock-cfd.md`
- 계획(plan): `docs/plans/2026-09-03-ue-rehearsal-mock-cfd.md`
- UE 반입: `docs/ue-import-guide.md`
- 모든 값: `geometry.json` (실데이터 오면 값만 교체, 코드 불변)

## 실행 (이 머신은 `python` 깨져 `py` 사용)

```bash
py -m pip install numpy pandas matplotlib pytest
py -m pytest -v                    # 테스트
py -m src.generate_frames          # data/frames/ 에 15프레임 CSV + manifest
py -m src.preview                  # data/preview/ 에 단면 PNG
```

## 산출물
- `data/frames/frame_00..14.csv` — 스키마 `x,y,z,T,Ux,Uy,Uz,p,source` (진짜 CFD와 동일)
- `data/frames/manifest.json` — 프레임별 시각·온도·기류 범위
- `data/preview/slice_z_frame_*.png` — 눈검증
