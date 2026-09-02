# CSV → 언리얼(Niagara) 반입 가이드

`data/frames/frame_00.csv … frame_14.csv` 를 언리얼에서 "온도색 기류"로 그리는 절차.
CSV는 순수 SI(m, K) — 아래 변환은 UE 쪽에서 적용한다.

## 변환 규칙
- 위치: `x,y,z (m) × 100 = cm` (UE 기본 단위)
- 온도: `T_C = T_K − 273.15`
- 좌표 매핑: CFD(X=직선벽 따라, Y=방 안쪽, Z=위) → UE(X, Y, Z-up).
  UE는 왼손 좌표라 필요하면 Y 부호를 뒤집는다(임포트 후 방향이 좌우 반전이면 Y*-1).
- 컬러맵: 고정 범위 **20~29 ℃**(프레임 간 색 비교 가능), 파랑(차가움)→빨강(더움).

## Niagara 절차 (개요)
1. 각 `frame_XX.csv`를 데이터로 읽는다(Data Table 임포트 또는 CSV 파싱).
2. 행마다 파티클 스폰: 위치=(x,y,z)×100, 속도=(Ux,Uy,Uz), 색=컬러맵(T_C).
3. 점이 많으면(수만) **다운샘플**(예: 3칸마다 1점)하거나 텍스처로 베이크.
   - 구체 방식은 UE 버전 확인 후 결정.
4. 타임라인: 프레임 0→14 를 원하는 재생속도로 진행 → 냉각·기류 발달 애니메이션.

## mock → real 교체
진짜 프로젝트 머신의 OpenFOAM 5분 transient 를 타임스텝별로 같은 스키마
(`x,y,z,T,Ux,Uy,Uz,p,source`) CSV 로 export 해 `data/frames/` 를 교체하면
UE 쪽은 한 줄도 안 고친다. `source` 만 `mock→simulated` 로 바뀐다.
