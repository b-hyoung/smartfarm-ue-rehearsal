# smartfarm-ue-rehearsal

반원 800×570×270cm 공간의 **가짜 5분 냉각 데이터**를 만들어, 진짜 CFD 데이터가
오기 전에 언리얼(Niagara) "온도색 기류" 시각화 파이프를 리허설한다.

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
