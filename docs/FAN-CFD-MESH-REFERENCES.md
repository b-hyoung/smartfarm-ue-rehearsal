# 격자를 얼마로 잡을 것인가 — 문헌에서 확인한 수치

2026-09-21. 원문(출판사 페이지·DOI·오픈액세스 PDF)을 직접 받아 읽은 내용만 적는다.
초록만 본 것은 그 자리에 **초록만 확인**이라고 밝힌다. 수치는 원문 표기 그대로이고,
우리가 계산해서 얻은 값은 **환산**이라고 따로 표시한다.
배치 근거는 `docs/FAN-REFERENCES.md`, 해석 방법은 `docs/FAN-CFD-METHOD.md` 5절에 있다.

---

## 1. 한 문단 요약

실내 농업 CFD 논문이 실제로 쓰는 격자는 우리보다 훨씬 촘촘하다. 방 크기가 우리와 비슷한
육묘 식물공장(4.37 × 2.6 × 2.45 m)은 전역 0.05 m, 에어컨 취출구 주변 0.025 m 미만으로
418 만 셀을 썼다(Lee 외 2023). 20 ft 컨테이너 수직농장은 최소 0.52 mm · 최대 50 mm 격자로
833 만 셀을 썼고(Sohn 외 2023), 컨테이너형 딸기 농장은 3,320 만 셀에서 GCI 4.25 %를 얻고서야
격자를 확정했다(Jung 외 2026). 체적당 셀 수를 균일 육면체로 환산한 **등가 셀 한 변**으로
보면 이 논문들은 **6 ~ 25 mm** 에 몰려 있고, 우리는 **100 mm** 다. Chen 외(2024)가 쓴 격자의
*최대* 셀 크기가 정확히 100 mm 다. 곧 우리 전역 격자는 최신 식물공장 논문이 방 구석의
빈 공간에나 허용하는 크기다. 다만 절대 크기만으로 판정하면 안 된다. 2 ha Venlo 온실은
0.8 m 격자로 RMSE 3.9 %를 얻었다(Kibwika 외 2023). 기준은 **보려는 것의 크기에 견준 셀 수**다.
우리가 보려는 것은 지름 0.20 m 팬 제트와 두께 0.25 m 캐노피이고, 지금은 각각 2 셀과 2~3 셀이다.
AIJ 지침의 "물체 한 변에 최소 10 셀", 액추에이터 디스크의 7~10 셀, Lee 외(2023)가 지름 0.2 m
취출구에 쓴 0.025 m(지름당 8 셀 이상), 캐노피 두께당 최소 5 셀(Tolladay & Chemel 2021,
SimScale 문서) 어느 기준에도 못 미친다. 다만 0.10 m 를 옹호할 근거가 하나 있다.
Srebric & Chen(2002)은 5.16 × 3.65 × 2.43 m 시험실을 평균 0.09 m 셀로 나누고 셀보다 작은
취출 장치를 운동량 소스로 넣어 격자 독립성과 실측 일치를 모두 얻었다. 그 관행이 성립하는
전제는 **토출 분포를 실측으로 규정하고 제트 자체의 발달은 주장하지 않는 것**이며, 그것을 하지
않았을 때 Nielsen(1998)이 잰 오차가 재실역 풍속 40 % 다. 결론은 둘 중 하나다.
**국소 세분으로 해상도를 올리거나, 주장의 범위를 줄이거나.**

---

## 2. 논문별 격자

### 2-1. 실내 식물공장·수직농장·컨테이너

| 논문 | 대상 공간 | 격자 방식 | 대표 셀 크기 | 총 셀 수 | 국소 세분 | 난류 모델 | y+·벽면 처리 | 정상/과도 | 검증 |
|---|---|---|---|---|---|---|---|---|---|
| **Sohn 외 2023** · Comput. Electron. Agric. 215:108363 · doi 10.1016/j.compag.2023.108363 | 20 ft 컨테이너 수직농장, 유동영역 **5.900 × 2.400 × 2.400 m**, 랙 3 × 층 4, 대칭 절반 | SimScale(OpenFOAM 기반) **육면체 위주 castellated/snappy** | **최소 0.52 mm, 최대 50 mm** | **8,328,473** | 층마다 직육면체 상자 4000 × 630 × 150 mm 를 **level 1**. 외벽 level 0~2, 트레이·LED 등 내부면 level 1~3 | 표준 k-ε | **프리즘 5 층, 목표 y+ = 50**, 표준 벽함수 | 정상 | **실측 검증 없음**(저자가 후속 과제로 명시) |
| **Chen 외 2024** · Agriculture 14:2227 · doi 10.3390/agriculture14122227 | 마이크로 식물공장 **2 × 1.3 × 2 m**, 재배 공간 1.54 × 1.24 × 1.20 m, 3단 | 사면체 + 육면체(Fluent 2022 R1) | **최소 1 mm, 최대 100 mm** | **2.1 × 10⁷** | 급배기구(지름 120 mm)·LED 패널 주변을 proximity·curvature 함수로 | Realizable k-ε | 표준 벽함수, **평균 y+ = 76**(30 < y* < 300) | 정상 | 배추 플러그묘 실험, 재배층 250·300·350 mm 에서 **NMSE 0.032·0.031·0.046**(풍속), 풍속 상관계수 0.95~0.97 |
| **Jung 외 2026** · J. Agric. Eng. doi 10.4081/jae.2026.2241 | 컨테이너형 다단 딸기 스마트팜(충남 예산). **치수는 Figure 1 에만 있고 본문에 없음** | 사면체 기반 혼합격자(ICEM), 풀이는 CFX 2020 R1 | 미보고 | **3.32 × 10⁷** | 재배 베드, 급배기구 주변 | SST k-ω | 미보고 | 정상(05:00~08:30 대표) | **실측 대조 오차 통계 없음.** 경계조건만 실측값 사용 |
| **Gu & Goto 2024** · Agriculture 14:1199 · doi 10.3390/agriculture14071199 | 밀폐형 재배 선반, 식물 피복 면적 0.50 × 0.52 m, 대두 9 주. **영역 치수는 Figure 1 에만** | Fluent Meshing 2021 R2, **폴리헤드라 + 육면체**(poly-hexcore) | 검증 모델 전역 **0.01 m**, 용기 0.004 m, **줄기 0.001 m**, 잎 0.004 m · 케이스 모델 전역 **0.008 m**, **줄기 0.0006 m**, 잎 0.004 m | 식물 없음 **0.2 M**, 식물 있음 **1.3 M**, 케이스 모델 **3.9 M**(A·B·D) 및 **5.7 M**(C) | 줄기·잎 표면 | Realisable k-ε, 난류강도 5 %, 점성비 10 | y+ 수치·벽함수 **미보고** | 정상, SIMPLE, 2차 정확도, 잔차 10⁻³ | 열선풍속계 20 점 × 3 조건. **MAPE 6.7 % / 10.1 % / 12.7 %**, MAE 0.04·0.04·0.06 m/s |
| **Lee 외 2023** · Horticulturae 9:1027 · doi 10.3390/horticulturae9091027 | 육묘 식물공장 **4.37 × 2.6 × 2.45 m**, 대칭 절반 | 사면체(Fluent 2020 R1) | 전역 **0.05 m** | **4.18 × 10⁶** | 에어컨·가습기 취출구 **0.025 m 미만**. 다공판 뒤 0.15 m 순환 공간은 재배 공간과 같은 해상도. 작업 공간은 더 성기게 | Realizable k-ε(4종 비교) | 미보고. 왜도 평균 0.21, 최대 0.84 | 과도 180 s, Δt 1 s, i7 에서 8 시간 | 24 시간 현장 모니터링. 모델 오차 **4.0 %**(Realizable·Standard·RNG), 4.2 %(SST). 최종 온도 5.2 ± 1.1 %, 습도 1.7 ± 1.5 % |
| **Gao 외 2025** · Appl. Sci. 15:4329 · doi 10.3390/app15084329 | 식물공장 **4.4 × 2.2 × 3.3 m**, 재배 트레이 1.6 × 0.5 × 0.15 m, **작물층 두께 0.12 m** | **육면체** | 미보고 | **1,984,032** | LED 조명 벽, 작물 표면, 급배기면 | k-ε 계열(본문 표준, 표에는 Realizable — 논문 내부 불일치) | 미보고 | 정상 | **식물공장 자체 실측 없음.** Blay 외(1992) 환기 공동 벤치마크와만 대조 |
| **Zhang 외 2025** · Agronomy 15:2326 · doi 10.3390/agronomy15102326 | 재배 베드 통합 덕트. 베드 1.1 × 0.12 m, **캐노피 0.18 m**, 환기공 지름 5 mm 13 개 | 캐노피 사면체, 배관 육면체(Fluent 2021 R2) | **초기 셀 높이 0.01 m** | **253,677 셀 / 549,733 절점** | 환기 배관 벽면 | Realizable k-ε, 표준 벽함수, 부력 포함 | 표준 벽함수, y+ 미보고 | 정상, 점성항 **1차 상류** | 12 점 × 4 유속. **MRE 8.5/3.3/8.3/−4.8 %, RMSE 0.07~0.11 m/s** |
| **Wangkahart 외 2024** · Agronomy 14:2808 · doi 10.3390/agronomy14122808 | 밀폐 재배실 **2 × 2 × 2.2 m**, 재배대 1 × 1 m · 높이 0.87 m, 소형 팬 1 m/s | 사면체(ANSYS Meshing v19.1) | 미보고 | **약 1.26 × 10⁶** | 미보고(자동 크기 제어) | k-ε 계열(논문 내부 불일치) | 미보고. 왜도 < 0.95, 직교품질 > 0.1, 종횡비 < 100 | 정상 | SHT20 센서 1 시간. **RMSE 2.02 ℃, R² 0.92(온도)·0.89(풍속)** |
| **Plas & De Paepe 2021** · J. Phys. Conf. Ser. 2116:012076 · doi 10.1088/1742-6596/2116/1/012076 | 수직농장 기류 통로 안 단일 바질·임파첸스. **영역 치수는 Figure 1 에만** | 사면체(Fluent) | **식물 몸체 0.002 m, 주변 공기 0.005 m** | **5,072,398** | 벽면 추가 세분(첫 층 높이 미보고) | **미보고** | 미보고 | 정상(암시) | 증산량 실측 대조. 바질 **26 % 차이** |
| **Yu 외 2023** · Horticulturae 9:660 · doi 10.3390/horticulturae9060660 | 인공광 식물공장 **5.575 × 3.950 × 3.175 m** | **미보고** | **미보고** | **미보고** | — | Realizable k-ε, 작물 다공체 **C_d = 0.32** | 미보고 | 정상(암시) | RMSE 습도 9.21, 기류 5.39, 온도 5.86 |
| **Kang 외 2024** · Biosyst. Eng. 243:148–174 · doi 10.1016/j.biosystemseng.2024.05.004 | 소형 다단 수직농장 | — | — | — | — | RNG k-ε 가 다른 2방정식 모델보다 우수 | — | 정상 | **초록만 확인**(ScienceDirect·TU/e 저장소 모두 403) |
| **Larochelle Martin & Monfet 2022** · eSim 2022 paper 213 | 소형 CEA-HD 공간, **2D 단면** | 2D(ANSYS Fluent R19.2), 종류 미보고 | **미보고** | **미보고** | — | k-ε, 작물 다공체 + UDF | 미보고 | 정상 | 실측 대조 오차 통계 없음 |
| **이정민 외 2024** · 한국콘텐츠학회논문지 24(12):827–837 · doi 10.5392/JKCA.2024.24.12.827 | 컨테이너형 수직농장, 실제 크기와 같은 모의 공간 | 미보고 | 미보고 | **미보고** | — | k-ε | 미보고 | 미보고 | **초록만 확인.** 격자 수치가 공개분에 없다 |
| **Hwang 외 2020** · 대한기계학회논문집 A 44(11):873–879 | 컨테이너형 스마트팜, 양 측벽 4단 재배 선반 | 미보고 | 미보고 | **미보고** | — | 미보고 | 미보고 | 미보고 | **초록만 확인.** 판정 지표는 CO₂ 농도와 공기연령(LMA) |

### 2-2. 온실·축사·저장고(규모 비교용)

| 논문 | 대상 공간 | 격자 방식 | 대표 셀 크기 | 총 셀 수 | 난류 모델 | y+·벽면 처리 | 정상/과도 | 검증 |
|---|---|---|---|---|---|---|---|---|
| **Kibwika 외 2023** · AgriEngineering 5(3):1395–1414 · doi 10.3390/agriengineering5030087 | Venlo 온실 2 ha | 미보고 | **0.8 m**(기준격자 0.2 m 와 대조해 채택) | **약 5.5 × 10⁶** | RNG k-ε + 강화 벽함수 | 초기 최대 y+ 1800·평균 600 → 인플레이션 4 층·첫 층 **0.04 m**·성장비 1.2 적용 후 **평균 270** | 정상 후 과도 180 s, Δt 1 s | **R² 0.968, RMSE 3.923 %** |
| **Yi & Akdeniz 2026** · Appl. Sci. 16:9227 · doi 10.3390/app16189227 | 측지돔 온실 지름 12.8 m · 높이 5.25 m + 외부 영역 | 사면체 | 미보고 | **26.43 × 10⁶** | 표준 k-ε(Realizable 민감도 비교) | **y+ 32 ~ 291**, 표준 벽함수 | 정상 RANS | **R² 0.905(온도)·0.920(풍속), RMSE 0.375 ℃ · 0.078 m/s** |
| **Shen 외 2026** · Processes 14:1331 · doi 10.3390/pr14091331 | Venlo 온실 768 m², 길이 40 m, 6 스팬, 처마 6.5 m·용마루 7.5 m | 미보고 | 미보고 | **1.6 × 10⁶** | 미보고 | 미보고 | 미보고 | 실측 온도 대조. 작물은 다공체 |
| **Choi 외 2024** · Animals 14(20):3019 · doi 10.3390/ani14203019 | 육계사 터널 환기 | 미보고 | **최소 셀 0.234 → 0.092 m** | **2,065,360** | 미보고 | 최소 직교품질 0.188 | 미보고 | 격자별 R² ≥ 0.94 |
| **Tomasello 외 2019** · Buildings 9(8):183 · doi 10.3390/buildings9080183 | 젖소 프리스톨 우사 | 미보고 | 미보고 | **8,145,537 절점** | 미보고 | 미보고 | 미보고 | 실내 평균 풍속 0.673/0.666/0.637 m/s |

### 2-3. 체적당 셀 수로 환산하면

셀 수는 방 크기를 빼고는 견줄 수 없다. **등가 셀 한 변** = (영역 체적 ÷ 셀 수)^(1/3) 로 환산한다.
아래 환산값은 우리가 계산한 것이며 논문에 적힌 값이 아니다.

| 사례 | 체적 | 셀 수 | 셀/m³ | 등가 셀 한 변 |
|---|---|---|---|---|
| Chen 외 2024 마이크로 식물공장 | 5.2 m³ | 2.1 × 10⁷ | 4,040,000 | **6.3 mm** |
| Sohn 외 2023 컨테이너(대칭 절반 ≈ 17.0 m³) | 17.0 m³ | 8.33 × 10⁶ | 490,000 | **12.7 mm** |
| Lee 외 2023 육묘 식물공장 | 27.8 m³ | 4.18 × 10⁶ | 150,000 | **18.8 mm** |
| Wangkahart 외 2024 밀폐 재배실 | 8.8 m³ | 1.26 × 10⁶ | 143,000 | **19 mm** |
| Gao 외 2025 식물공장 | 31.9 m³ | 1.98 × 10⁶ | 62,000 | **25 mm**(대칭 절반만 계산했다면 20 mm) |
| Shen 외 2026 Venlo 온실 | 약 5,400 m³ | 1.6 × 10⁶ | 300 | **150 mm** |
| **우리 (0.10 m 균일)** | **84.0 m³** | **84,024** | **1,000** | **100 mm** |

Jung 외(2026)는 컨테이너 체적이 본문에 숫자로 없어 환산에서 뺐다. 배기구 위치 수준이
1,500·3,500·5,500 mm 이므로 길이 5.5 m 이상인 것만 확실하다. 20 ft 컨테이너(약 37 m³)로 가정하면
등가 셀 한 변은 10.4 mm 가 된다. 가정에 기댄 값이므로 표에 넣지 않았다.

판단: 실내 농업 CFD 의 등가 셀 한 변은 **6 ~ 25 mm** 대에 몰려 있다. 100 mm 는 5,400 m³
온실에서나 나오는 크기다. 84 m³ 방에 100 mm 균일은 이 문헌 어디에도 없다.

### 2-4. 기존 문서에서 고쳐야 할 것

`docs/FAN-CFD-METHOD.md` 5절 「이 값의 출처」에 적힌 두 문장을 원문과 대조했다.

1. **Gu·Goto(2024)** — "전역 0.008~0.01 m, 줄기 0.0006~0.004 m, 잎 0.004 m, 작물 없음 20 만 셀,
   있음 130 만 셀". 전역·잎·셀 수는 맞다. **줄기 상한 0.004 m 는 틀렸다.** 줄기는 검증 모델
   0.001 m, 케이스 모델 0.0006 m 이고 0.004 m 는 용기와 잎의 크기다. 또한 20 만·130 만은
   **검증용 격자**이고, 실제 케이스 계산에 쓴 격자는 **390 만(A·B·D)과 570 만(C)** 이다.
   격자 수렴 확인은 **210 만 / 470 만 / 640 만** 세 격자로 했고 **470 만**을 골랐다.
2. **저자명 오기** — `docs/FAN-REFERENCES.md` A-2 와 `data/fan_layout.json` 의 `reference`가
   Agronomy 15:2326 을 "왕 외(2025)"로 적고 있다. 원문 저자는 **Zhang, Y.; Chen, C.; Fang, H.;
   Tong, Y.** 다(중국농업과학원). 다음에 그 문서를 손댈 때 **Zhang 외(2025)** 로 고치는 것이 맞다.
3. **"컨테이너형 수직농장 성김·기준·조밀 130 만 / 330 만 / 740 만 셀"** — **출처를 찾지 못했다.**
   후보를 모두 열어 확인했으나 어느 것도 이 숫자가 아니다. Sohn 외(2023)는 390 만 / 833 만 /
   1,359 만, Jung 외(2026)는 1,180 만 / 2,790 만 / 3,320 만, Chen 외(2024)는 980 만 / 2,100 만 /
   3,800 만, Gu·Goto(2024)는 210 만 / 470 만 / 640 만이다. 유일하게 확인 못 한 후보는
   Fang 외(2020) Biosystems Engineering 200:1–12 로, 유료라 본문을 열지 못했다.
   **원문을 확인하기 전까지 이 숫자는 인용하지 않는 것이 맞다.**

---

## 3. 격자 수렴을 실제로 어떻게 확인했나

### 3-1. 1차 출처 — GCI 와 Richardson 외삽

- **Roache, P.J. (1994)** 「Perspective: A Method for Uniform Reporting of Grid Refinement Studies」
  *Journal of Fluids Engineering* 116(3):405–413, doi 10.1115/1.2910291.
  **원문은 유료라 읽지 못했다.** 대신 저자 본인의 책 *Fundamentals of Verification and Validation*
  (Hermosa, 1998/2009) 5장이 "이 장은 주로 Roache(1994)에서 가져왔다"고 밝히고 있어 그 본문을
  인용한다.

  > GCI[fine grid] = Fs·|ε| / (r^p − 1), Fs = 3

  > "We note immediately that for a grid doubling (r = 2) with a 2nd-order method (p = 2),
  > the denominator = 3, and we obtain GCI = |ε|, as intended. … Thus Fs may be interpreted
  > as a 'factor of safety' over the Richardson Error Estimator E₁."

  안전계수 규칙은 5.9.2 절에 이렇게 적혀 있다.

  > "(a) Use Fs = 1.25 for convergence studies with a minimum of three grids to experimentally
  > confirm that the observed order of convergence p_obs for the actual problem is reasonable, and
  > (b) use Fs = 3 for two-grid convergence studies (since a p_obs cannot be calculated and
  > therefore there is no way to demonstrate that the grids are in or at least near the
  > asymptotic regime)."

  곧 **격자 두 개만 비교하면 안전계수 3, 세 개를 쓰고 관측 차수를 확인하면 1.25** 다.
  1994 년 논문이 권한 값은 3 이고, 1.25 는 그 뒤의 완화다.

- **Celik, I.B.; Ghia, U.; Roache, P.J.; Freitas, C.J.; Coleman, H.; Raad, P.E. (2008)**
  「Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications」
  *Journal of Fluids Engineering* 130(7):078001, doi 10.1115/1.2960953. ASME JFE 편집 방침이다.
  다섯 단계 가운데 우리가 지켜야 할 대목을 원문 그대로 옮긴다.

  > **Step 2.** "Select three significantly different set of grids, and run simulations to determine
  > the values of key variables important to the objective of the simulation study, for example,
  > a variable φ critical to the conclusions being reported. **It is desirable that the grid
  > refinement factor, r = h_coarse/h_fine, be greater than 1.3. This value of 1.3 is based on
  > experience, and not on formal derivation.**"

  > **Step 3.** 겉보기 차수 p = (1/ln r₂₁)·|ln|ε₃₂/ε₂₁| + q(p)|,
  > q(p) = ln((r₂₁^p − s)/(r₃₂^p − s)), s = 1·sign(ε₃₂/ε₂₁).
  > "**Negative values of ε₃₂/ε₂₁ < 0 are an indication of oscillatory convergence.**"

  > **Step 5.** 근사 상대오차 e_a²¹ = |(φ₁ − φ₂)/φ₁|,
  > **GCI_fine²¹ = 1.25·e_a²¹ / (r₂₁^p − 1)**

  예비 조건도 명시돼 있다.

  > "Before any discretization error estimation is calculated, it must be ensured that *iterative
  > convergence* (if iterative methods are used) is achieved with at least three orders of
  > magnitude decrease in the normalized residuals for each equation solved."

  같은 문서 앞머리의 JFE 방침은 이렇게 잘라 말한다.

  > "The Journal of Fluids Engineering will not consider any paper reporting the numerical solution
  > of a fluids engineering problem that fails to address the task of systematic truncation error
  > testing and accuracy estimation."

- **ASME V&V 20-2009 (R2021)** 「Standard for Verification and Validation in Computational Fluid
  Dynamics and Heat Transfer」 · 100 쪽 · ISBN 9780791832097. ASME 공식 카탈로그의 범위 문장은
  이렇다.

  > "The scope of this Standard is the quantification of the degree of accuracy of simulation of
  > specified validation variables at a specified validation point for cases in which the conditions
  > of the actual experiment are simulated."

  곧 V&V 20 은 **실측과 견주는 검증(validation)** 의 표준이지 격자 크기를 정해 주는 문서가 아니다.
  격자 절차는 위 Celik 외(2008)가 실무 표준이다. (ASME V&V 10 은 고체역학용이라 해당 없다.)

- **Richardson, L.F. (1911)** *Phil. Trans. R. Soc. A* 210:307–357, doi 10.1098/rsta.1911.0009 ·
  **Richardson & Gaunt (1927)** *Phil. Trans. R. Soc. A* 226:299–361, doi 10.1098/rsta.1927.0008.
  둘 다 DOI 등록정보로만 확인했고 본문은 열지 못했다.

- **Roache, P.J. (1997)** *Annual Review of Fluid Mechanics* 29:123–160,
  doi 10.1146/annurev.fluid.29.1.123. **유료라 내용 확인 못 함.**

### 3-2. 실제 논문이 쓴 판정 방식

원문을 연 20 여 편 가운데 **GCI 를 실제로 계산한 농업 시설 논문은 Jung 외(2026) 하나뿐**이었다.

| 논문 | 격자 수 | 셀 수 | 세분비 r | 판정 지표 | 임계값 | 채택 |
|---|---|---|---|---|---|---|
| **Jung 외 2026**(컨테이너 딸기) | 3 | 1.18 × 10⁷ / 2.79 × 10⁷ / 3.32 × 10⁷ | **r₂₁ = 1.06, r₃₂ = 1.33** | **배기구 질량유량** 46.236 / 46.256 / 47.798 × 10⁻⁵ kg/s | **GCI < 5 %** | 조밀. p = 2.00, 외삽 44.664 × 10⁻⁵, e_a 3.38 %·3.51 %, **GCI 4.25 %** |
| **Sohn 외 2023**(컨테이너 수직농장) | 3 | 3,900,396 / 8,328,473 / 13,590,833 | 미보고 | **한 단계 조밀 격자 대비 풍속 RMSE** | **5 % 이내** | 중간(2번). RMSE 3.17 %·2.74 % |
| **Gu & Goto 2024** | 3 | 2.1 M / 4.7 M / 6.4 M | 미보고 | 네 개 풍속 프로파일 선 | **NRMSE < 10 %**(조밀 격자 기준) | 중간 4.7 M |
| **Chen 외 2024** | 3 | 9.8 × 10⁶ / 2.1 × 10⁷ / 3.8 × 10⁷ | 미보고 | 중간 재배층 중심의 풍속·온도·습도 | 없음("little difference") | 2.1 × 10⁷ |
| **Gao 외 2025** | 3 | 552,789 / 1,984,032 / 2,847,910 | 미보고 | z 축 풍속·온도 프로파일(y = 0.6, x = 0.55 m) | 없음("minimal") | 1,984,032 |
| **Shen 외 2026**(Venlo 온실) | 4 | 0.5 / 1.0 / 1.6 / 2.0 백만 | 미보고 | **작물 캐노피 중심 온도 · 팬 출구 풍속 · 상부 평균 온도** | 최조밀 격자 대비 **상대오차** 3.2 → 1.5 → 0.3 % | 1.6 백만 |
| **Yi & Akdeniz 2026**(측지돔) | 4 | 19.64 / 26.43 / 31.00 / 33.13 백만 | 미보고 | 온실 중심 z = 1.3 m 의 온도·풍속 | 없음(더 세분해도 변화 없음) | 26.43 백만 |
| **Kibwika 외 2023**(Venlo 2 ha) | 10(셀 크기 0.2 ~ 3.0 m) | 최종 5.5 백만 | 미보고 | **0.2 m 기준 격자 대비** 평균 풍속(0.654 m/s)과 세 높이 프로파일 | **RMSE ≤ 5 % 이고 R² ≥ 0.95** | 0.8 m. R² 0.968, RMSE 3.923 %, 셀 38 % 절감 |
| **Choi 외 2024**(육계사) | 6 | 99,004 ~ 16,522,880 | 미보고 | z = 1 m, 6 개 구역 중심의 풍속·압력, 최조밀 대비 R² | **R² ≥ 0.94**, 압력 R² = 0.99 로 확정 | 2,065,360 |
| **Hu 외 2024·2025·2026**(계사 3편) | 5~6 | 184 만 ~ 933 만 | 미보고 | **6~9 지점 공기 온도** | 평균 상대오차 **< 1 %**(2026 년 편은 < 2 %) | 422 만 / 467 만 / 596 만 |
| **Ajmani 외 2025**(강의실) | 3 + 1 | 32 / 66 / 99 백만 폴리헤드라, h = 0.0406 / 0.0319 / 0.0279 m | **셀 수 기준 2 배·1.5 배**, r 은 Celik 식으로 환산 | 호흡 플룸 안 1 점, 급기구 전단층 안 1 점의 풍속 | 고정 % 없이 점근영역 비(≈ 1)로 판단. **GCI 1.47 % · 0.57 %** | 85 백만. Celik 외 2008 + Roache 1994, Fs = 1.25 |
| **Mohd Zainuddin 외 2023**(UFAD 실) | 3 | 1,414,933 / 3,981,287 / 5,668,675 | **r = 2**(명시) | 착좌 높이 z = 1 m, x = 2·4·6·8 의 x 방향 풍속 프로파일 | **GCI < 5 %** | 중간. 중간-조밀 평균오차 0.08 ~ 0.14 % |
| **Zhang 외 2025**(재배 베드) | 5 만 ~ 50 만 훑기 | 253,677 채택 | 미보고 | **명시 없음**("격자 품질과 수렴 속도의 균형") | 없음 | 253,677 |
| **Lee 외 2023**(육묘 식물공장) | — | — | — | — | — | **자체 격자 수렴 시험 없음.** "선행 연구의 격자 독립성 평가 결과에 근거해 설계" |

판단:

1. **농업 시설 CFD 에서 형식을 갖춘 검증은 사실상 없다.** 확인한 농업 논문 가운데 겉보기 차수
   p 를 계산하고 Richardson 외삽값과 GCI 를 낸 것은 Jung 외(2026) 하나다. 나머지는 "더 조밀한
   격자와 비교해 차이가 작았다"로 끝낸다.
2. **세분비 r 을 적는 논문이 거의 없다.** 농업 논문 중 r 을 밝힌 것은 Jung 외(2026)(1.06·1.33)와
   Tomasello 외(2019)(셀 크기 1.1·1.2, 저자 스스로 부족하다고 인정) 정도다. Jung 의 r₂₁ = 1.06 은
   Celik 외(2008)가 권한 **r > 1.3** 에 한참 못 미친다. GCI 값을 냈어도 그 절차 요건은 못 맞춘 것이다.
3. **사실상의 합격선은 감시 스칼라 1 ~ 5 %** 다. < 1 %(Hu 2024·2025), < 2 %(Hu 2026), 0.3 %(Shen 2026),
   RMSE ≤ 5 % 이고 R² ≥ 0.95(Kibwika 2023), RMSE < 5 %(Sohn 2023), NRMSE < 10 %(Gu·Goto 2024),
   GCI < 5 %(Jung 2026, Mohd Zainuddin 2023).
4. **판정 지표는 대개 몇 개 지점의 평균 온도나 점 풍속**이다. 우리가 쓰려는 "캐노피 평균 풍속"과
   "적정구간 비율" 같은 균일도 지표를 수렴 판정에 쓴 논문은 확인한 범위에 **없다**.
   온도로 보인 격자 독립성은 균일도 지표에 그대로 옮겨 가지 않는다. 이 점은 우리가 선례 없이
   직접 밝혀야 한다.

### 3-3. 우리가 따라 할 수 있는 절차

Celik 외(2008)와 COST 732 를 그대로 옮기면 이렇게 된다.

1. **격자 셋**을 만든다. 둘만 쓰면 겉보기 차수를 못 구하고 안전계수 3 을 써야 한다(Roache 5.9.2).
2. **세분비 r = h_조밀 ÷ h_성김 ≥ 1.3**(Celik Step 2). 3 차원 구조 격자에서 방향마다 1.3 배면
   셀 수는 2.2 배다. AIJ·COST 의 더 엄한 해석은 방향마다 1.5 배, 곧 셀 수 3.4 배다.
3. 감시할 물리량 φ 와 **그 위치를 명시**한다. 우리에게는 캐노피 판정면의 평균 풍속이 1 순위,
   적정구간 비율이 2 순위다. 둘을 따로 보고해야 한다.
4. p, φ_ext, e_a, GCI 를 Celik 식 (3)~(7)로 계산하고 **점근영역 비가 1 에 가까운지** 확인한다.
5. 잔차가 정규화 기준으로 **3 자릿수 이상** 떨어졌는지 먼저 확인한다(Celik 예비 조건).
6. ε₃₂/ε₂₁ 이 음수면 진동 수렴이므로 안전계수 1.25 를 쓰면 안 된다(Roache 5.9.2 단서).

COST 732 의 대응 문장은 이렇다.

> "However, for validation simulations, a systematic grid convergence study using generalised
> Richardson extrapolation should be tried. … **For the Richardson extrapolation, at least
> solutions on three systematically refined/coarsened grids are necessary.**"

비정렬 격자에서는 세분비를 셀 수로 환산해도 된다.

> "On tetrahedral or unstructured meshes in general the refinement factor r can also be defined
> by (Roache, 1998) **r₂₁ = (N₁/N₂)^(1/D)** where N_k is the number of nodes or cells of the mesh
> and D the dimension of space."

---

## 4. 팬·취출구 주변 해상도

### 4-1. 논문이 실제로 쓴 값

**어느 논문도 "취출구 지름당 몇 셀"이라고 직접 쓰지 않았다.** 아래는 논문에 적힌 개구부 치수와
그 주변 셀 크기를 나란히 놓고 우리가 나눈 값이다. 나눗셈은 우리 것이고 저자의 주장이 아니다.

| 논문 | 개구부 | 그 주변 셀 크기 | 지름·변 길이당 셀(환산) |
|---|---|---|---|
| **Lee 외 2023** Horticulturae 9:1027 | 에어컨 취출구 **지름 0.2 m** 6 개(천장), 가습기 토출 지름 0.1 m 2 개·흡입 지름 0.2 m | 전역 0.05 m, **취출구·가습기 주변 0.025 m 미만** | 0.2 m 취출구에 **8 셀 이상**, 0.1 m 토출구에 **4 셀 이상** |
| **Chen 외 2024** Agriculture 14:2227 | 급기구·배기구 **지름 120 mm** | 전역 최대 100 mm, **최소 1 mm**. 급배기구·LED 패널을 proximity·curvature 함수로 세분 | 세분 후 크기를 밝히지 않아 환산 불가. 다만 **최소 1 mm** 가 이 부근에 쓰였을 것이다 |
| **Sohn 외 2023** Comput. Electron. Agric. 215:108363 | Case 1 급기 **지름 250 mm**, Case 2 급기 **지름 100 mm**, Case 3·4 층 길이 방향 **높이 50 mm** 벤트형 슬롯 | 기본 최대 **50 mm**, 재배층 상자 안 level 1 → **25 mm**, 내부면(트레이·LED 등) 표면 세분 level 1~3 → 최소 **0.52 mm** | 250 mm 급기 **10 셀 이상**, 100 mm 급기 **4 셀 이상**, 50 mm 슬롯 **2 셀 이상**. 표면 세분이 걸리면 훨씬 촘촘하다 |
| **ASHRAE Handbook—HVAC Applications, Ch. 59** 사무실 예 | 재실자(인체) | 방 기본 **300 mm**, 재실자 주변 **약 25 mm** | 관심 물체 주변을 기본의 **1/12** 로 |

### 4-1-1. 개구부 셀 수를 명시한 유일한 실측 사례

**Hwang, Y.; Gorlé, C. (2022)** 「Large Eddy Simulations to Quantify the Impact of Inflow and
Wind Direction Uncertainty on Natural Ventilation」 *Frontiers in Built Environment* 8:911005,
doi 10.3389/fbuil.2022.911005 (오픈액세스).

> "The baseline and fine meshes meet the requirement of having **at least 10 cells across an area
> of interest, i.e., along the edges of the openings** (Franke et al., 2007)"
> "**the coarse mesh has only five to 6 cells along the opening height**" … "the coarse mesh
> results show more noticeable discrepancies"

성긴 격자(배경 32 mm, 최소 3.0 mm, 48.3 만 셀)는 조밀 격자 대비 **평균 공기연령을 20 % 낮게**
예측했다. 기준 격자는 16 mm / 1.5 mm / 321 만 셀, 조밀은 8 mm / 0.75 mm / 2,410 만 셀이다.

곧 **개구부에 5~6 셀만 두어도 환기 지표에 20 % 가 움직인다.** 우리는 2 셀이다.

### 4-1-2. 취출구를 단순화하면 무엇이 얼마나 틀어지는가 — Nielsen

실내 기류 CFD 는 취출구를 **해상하는 대신 대체**하는 것이 정석이다. 이 방법론의 출발점이
P.V. Nielsen(올보르대)이고, 대체에 따른 오차 크기까지 숫자로 적어 두었다.

**Nielsen, P.V. (1997)** 「The Box Method: a Practical Procedure for Introduction of an Air Terminal
Device in CFD Calculation」 Aalborg University, Gul serie R9744 No. 34, ISSN 1395-7953.

> "The supply momentum flow from diffusers depends on small details in the design. This means that
> a numerical prediction method should be able to handle small details in the order of a few
> millimetres to room dimensions of many metres. **This wide range of geometry necessitates the use
> of many grid points and demands, therefore, a large computer or a procedure which can reduce the
> number of grid points.**"
> "The details of the flow in the immediate vicinity of the supply opening are ignored…
> **First, it is not required to use a grid as fine as is the case with fully numerical prediction
> of the development from an inlet flow to a wall jet.**"

**Nielsen, P.V. (1998)** 「The Prescribed Velocity Method — A Practical Procedure for Introduction
of an Air Terminal Device in CFD Calculation」 Aalborg University.

> "The inlet profiles are given as boundary conditions at the diffuser in the usual way, although
> they are **represented only by a few grid points**."
> IEA Annex 20 에 대해: "The 84 nozzles in the IEA diffuser are replaced by a rectangular opening
> with the same supply area, aspect ratio and velocity direction… This method is called the
> **simplified boundary condition method**. Figure 6 shows that **simplified boundary conditions
> will overestimate the velocity in the occupied zone by 40%.**"
> Svidt(1994) 축사 사례: 규정속도법을 쓰자 재실역 최대 풍속이 "**from a 27% underestimate to an
> underestimate of only 9%**" 로 개선됐다.

**이 40 % 가 우리가 하는 일의 직접 대응물이다.** 실제 송풍 장치를 같은 면적·같은 운동량의
단순 소스로 바꾸고 토출 분포를 실측으로 보정하지 않으면, 방 규모 풍속이 40 % 어긋났다.
Nielsen 이 그것을 되돌린 방법은 **격자를 촘촘히 하는 것이 아니라 토출 속도 분포를 규정하는 것**
이었다.

### 4-1-3. 우리와 같은 0.09 m 격자로 검증에 성공한 사례 — 그리고 그 단서

**Srebric, J.; Chen, Q. (2002)** 「Simplified Numerical Models for Complex Air Supply Diffusers」
*HVAC&R Research* 8(3):277–294, doi 10.1080/10789669.2002.10391442.

> 시험실 "17 ft (5.16 m) long, 12 ft (3.65 m) wide, and 8 ft (2.43 m) high."
> "The number of control volumes used for the simulations were 44×26×24, **59×38×33**, and
> 72×53×44. The grid independence was found with a grid resolution of 59×38×33 and finer…
> **This grid number is comparable to that used for a room without diffusers**… This also implies
> that **the method to simulate the diffuser does not increase the computing time.**"

5.16 × 3.65 × 2.43 m 를 59×38×33 으로 나누면 평균 셀이 **0.087 × 0.096 × 0.074 m** 다.
곧 **우리 0.10 m 와 사실상 같은 격자로, 셀보다 작은 취출 장치를 운동량 소스로 두고,
격자 독립성과 실측 일치를 모두 얻은 논문이 있다.** 이것이 0.10 m 를 옹호할 수 있는
가장 강한 근거다.

다만 같은 논문에 단서가 붙는다.

> "**The momentum method failed to predict the jet development. The jet decay predicted is too
> fast… The results are much worse if the grid number is reduced.**"
> "…the flow mixing is too complex for the momentum method to handle… **To properly simulate this
> flow, a very fine grid resolution is required.**"
> 결론: "The momentum method is recommended for the displacement diffuser and the mixing diffusers
> that discharge combined jets. The mixing diffusers, such as the nozzle, slot and valve diffusers,
> that discharge several jets that merge and combine in front of them should use the box method,
> since **the momentum method performs poorly**."

그리고 같은 저자들의 RP-1009 보고서(Srebric & Chen 2001, 「A Method of Test to Obtain Diffuser
Data for CFD Modeling of Room Airflow」)는 그 소스를 **실측으로 먹여야** 한다고 못박는다.

> "To model detailed diffuser geometry would require **millions of grid cells**… but this does not
> guarantee a successful simulation."

정리하면 이렇다. **0.10 m 급 격자 + 셀 이하 취출 장치 = 검증된 관행**이다. 단 두 조건이 붙는다.
(1) 토출 분포를 실측이나 해석식으로 규정할 것, (2) 제트 자체의 발달·감쇠는 주장하지 말 것.
우리는 (1)을 하지 않았고 (2)가 바로 우리가 보려는 것이다.

### 4-1-4. 운동량 소스법 자체의 격자 의존성

**Deng, B.; Wang, J.; Tang, J.; Gao, J. (2018)** 「Improvement of the momentum method as the
diffuser boundary condition in CFD simulation of indoor airflow: Discretization viewpoint」
*Building and Environment* 141, doi 10.1016/j.buildenv.2018.05.050 (**초록만 확인**).

> "**The momentum method was considered to be not applicable for a fine grid adjacent to the
> diffuser.** … **A large error may be introduced for the convective-flux momentum method when the
> first grid interval adjacent to the diffuser is very small.** The total-flux momentum method is
> presented to include both the convective flux and the diffusion flux in the momentum source…"

방향이 우리에게 유리한 쪽이다. 고전적 운동량법은 **성긴** 소스 셀을 전제로 만들어졌고
오히려 지나치게 촘촘하면 나빠진다. 다만 이것은 **면 경계조건**에 대한 이야기이고,
우리처럼 부피에 분산된 body force 를 2 셀로 두어도 된다는 근거는 아니다.

### 4-2. 운동량 소스·액추에이터 디스크 계열의 관행

실내 농업 CFD 에서 팬을 운동량 소스로 두고 **그 셀 영역의 해상도를 규정한 문헌은 찾지 못했다.**
가장 가까운 정량 기준은 풍력 쪽에 있다.

> "The uniformly spaced domain around the wind farm has a cell size equal to **D∕8**, following a
> grid refinement study of previous work"
>
> — van der Laan, M.P.; Andersen, S.J.; Réthoré, P.-E. (2019) 「Brief communication:
> Wind-speed-independent actuator disk control for faster annual energy production calculations
> of wind farms using computational fluid dynamics」 *Wind Energy Science* 4:645–651,
> doi 10.5194/wes-4-645-2019

곧 **로터 지름당 8 셀**이 액추에이터 디스크의 통상 하한이다. 같은 계열의 다른 1차 출처도
비슷한 수를 댄다.

| 출처 | 규정 |
|---|---|
| **Sanderse, B.; van der Pijl, S.P.; Koren, B. (2011)** 「Review of computational fluid dynamics for wind turbine wake aerodynamics」 *Wind Energy* 14(7):799–819, doi 10.1002/we.458 | "It was observed that **10 cells per rotor diameter are sufficient; a similar number is typically found in other studies as well.**" 단, 같은 문단에 두 가지 한계가 붙는다. "modeling the wake by using forces is a good approximation for the mean flow quantities **at distances larger than a rotor diameter** from the wind turbine" 그리고 "the forces **fail to represent the mechanical turbulence generated at the blade location**" |
| **Revaz, T.; Porté-Agel, F. (2021)** 「Large-Eddy Simulation of Wind Turbine Flows: A New Evaluation of Actuator Disk Models」 *Energies* 14(13):3745, doi 10.3390/en14133745 | "**The grid resolution is not found to be critical once a reasonable resolution is used, i.e., in the order of 10 grid points along each direction across the rotor.**" 수렴 지점은 "**little resolution dependence when more than 8 and 12 grid points are used along the spanwise and vertical directions**". 가장 성긴 격자(로터면 6·9 점)에서도 추력계수 +4.3 %, 출력계수 +8.2 % 로 치우쳤다 |
| **Stipa, S.; Ajay, A.; Brinkerhoff, J. (2024)** 「The actuator farm model…」 *Wind Energy Science* 9:2301–2332, doi 10.5194/wes-9-2301-2024 | "the **ADM requires at least seven grid points across the turbine diameter** for sufficient spatial resolution" |
| **Shapiro, C.R.; Gayme, D.F.; Meneveau, C. (2019)** *Wind Energy* 22, doi 10.1002/we.2376 (초록만 확인) | "At typical grid resolutions, simulations cannot capture all of the vorticity shed behind the disk and subsequently **over-predict power by upwards of 10%**." |

이것은 자유 대기 중 수십 m 로터를 대상으로 한 값이라 0.20 m 소형 축류팬에 그대로 옮겨도 되는지는
별도 논거가 필요하다. 다만 방향은 분명하다. **7 ~ 10 셀이 하한이고, 2 셀을 옹호한 문헌은 없다.**

### 4-2-1. 농업·실내 시설에서 팬을 셀 영역으로 둔 사례

| 논문 | 팬 표현 | 팬 주변 격자 |
|---|---|---|
| **Chen, Fabian-Wheeler, Cimbala, Hofstetter & Patterson (2020)** *Animals* 10(6):1067, doi 10.3390/ani10061067 | "the entire fan volume was considered a **fluid cell zone**, which simulated the effect of an axial fan by applying a **distributed momentum source**"(압력 상승 18 Pa 일정) — 우리와 같은 방식이다 | 허브 반지름 5 cm, 날개끝 반지름 46 cm, 두께 5 cm. **총 1,210 만 셀.** 허브 5 cm 자체가 격자에 그려져 있다. 지름당 셀 수는 논문에 없다 |
| **You 외 (2026)** *Scientific Reports* 16:23128, doi 10.1038/s41598-026-53723-w | 터널 제트팬 | "tunnel grid size was set to **0.4 m**, with refinement to **0.1 m in the fan and surrounding regions**". 팬 지름 0.5 ~ 1.6 m → **지름당 5 ~ 16 셀**. 팬 부근만 4 배 세분했다 |
| **Choi 외 (2024)** *Animals* 14(20):3019 | 터널팬을 **속도 입구**(제조사 곡선 UDF) — 팬 몸체 없음 | 셀 0.184 ~ 0.392 m. 팬 영역이 없으니 해상할 것도 없다 |
| **Naranjani 외 (2022)** *Int. J. Heat Mass Transfer* 186:122460 — 실내 수직농장 | **팬을 아예 모델링하지 않음.** 질량유량 입구 + 압력 출구, 팬 동력은 P = QΔp 로 역산 | 팬 국소 해상도 개념이 없다 |

판단: **실내·농업 문헌은 대개 팬을 경계면(속도 입구·압력 점프)으로 처리해 이 문제를 비켜 간다.**
팬을 셀 영역 body force 로 둔 Chen 외(2020)는 허브 5 cm 를 격자에 그릴 만큼 촘촘했다.
우리처럼 팬 몸체 전체를 8 셀로 대표한 사례는 확인되지 않는다.

### 4-2-2. 지름당 2 셀에 가장 가까운 공식 기록

Thunderhead Engineering 의 PyroSim/FDS 공식 문서 「Modeling Jet Fans」
(https://www.thunderheadeng.com/docs/2026-1/pyrosim/examples/applications/modeling-jet-fans/)가
우리 상황을 가장 정확히 옮겨 놓았다. 제트팬 한 변 250 mm 에 격자 125 / 62.5 / 31.25 mm,
곧 **한 변당 2 / 4 / 8 분할**을 비교했다.

> "The fine mesh where the grid size is **1/20 of the outlet vent side** provides reasonable results."
> "a mesh of **1/16 the vent side** was needed to obtain a reasonably accurate solution"
> "**it is not feasible to simulate full scale parking garages with such a fine mesh**, even if
> multiple meshes are used, so in this section we examine alternate approaches."

그리고 2 분할(= 우리 상황)에서 실험과 맞추려면 **팬 하류에 슈라우드 형상을 덧대야** 했다.

> "The shroud maintains the outlet flow in the axial direction, ensuring that the one dimensional
> axial velocity is preserved at the fan outlet."

곧 2 분할 자체로는 제트 방향과 유인이 틀어지고, 별도 장치를 붙여야 맞았다는 기록이다.

### 4-3. 물체 크기에 견준 해상도 규정

| 출처 | 규정 | 우리 팬(0.20 m)에 옮기면 |
|---|---|---|
| AIJ 지침 §4.1 | "the minimum of **ten grids** is required on **one side of a building**" | 0.020 m |
| AIJ 지침 §4.2 | "minimum grid resolution … about **1/10 of the building scale**" | 0.020 m |
| COST 732 | "at least **10 cells per cube root of the building volume**" | 0.020 m |
| ASHRAE Fundamentals Ch. 13 | "If a grid has cell sizes of 10 mm, then flow field features **smaller than 20 mm cannot be solved**" | 0.10 m 격자는 0.20 m 미만 구조를 못 푼다 |
| 풍력 액추에이터 디스크 | D/8 | 0.025 m |
| Lee 외 2023 실측값 | 지름 0.2 m 취출구에 0.025 m 미만 | 0.025 m |

다섯 기준이 **0.020 ~ 0.025 m** 로 수렴한다. 우리 0.10 m 는 그 4 ~ 5 배다.

### 4-4. 취출구 경계조건 자체가 실내 기류 CFD 의 고전적 실패 지점

Chen, Q.; Zhai, Z. (2004) 「The use of CFD tools for indoor environmental design」,
*Advanced Building Simulation*, Spon Press, pp. 119–140. 저자가 대학원생들에게 같은 문제를 풀린
뒤 정리한 실패 유형 다섯 가운데 둘이 우리 문제와 같다.

> "• Incorrect setting of boundary conditions for the air-supply diffuser
> • Inappropriate selection of grid resolution"

> "Simulation of a specific problem of indoor environment requires creative approaches.
> One typical example is how to simulate the air-supply diffuser … **we found that only experienced
> CFD users may know how to simulate such a diffuser.**"

우리가 팬을 벽면 패치가 아니라 내부 운동량 소스로 둔 것은 이 함정을 피하는 방향이다.
질량 보존이 깨지지 않고 총 운동량이 격자와 무관하게 보존된다. **틀어질 수 있는 것은 총량이
아니라 분포다.**

한 가지 더. 복잡한 취출구를 단순화해 넣으면 **그 주변 풍속에 20 % 안팎의 오차**가 남는다는
정량값이 ASHRAE RP-1133 의 기준 사례에 적혀 있다.

> "Since the diffuser was a perforated surface with an effective area, the CFD simulation
> artificially increased the momentum for the velocity component normal to the wall by a factor
> of 1/(effective area ratio). This is an approximation method (Chen and Moser 1991) for
> simulating complex diffusers. This again introduced an error in the CFD simulation.
> **The error is about 20% for the velocity near the diffuser.**"
>
> — Srebric, J.; Chen, Q. (2002) *ASHRAE Transactions* 108(2):185–194

곧 격자를 아무리 촘촘히 해도 장치를 단순화한 이상 근방 풍속에는 이 정도 오차가 남는다.
우리 팬도 날개를 그리지 않으므로 같은 성격의 오차가 있다. 이것은 격자로 없앨 수 있는 오차가
아니다. 격자를 키워서 더 보태지 않는 것이 우리가 할 수 있는 전부다.

### 4-5. 지름당 2 셀인 사례가 있는가

**균일 body force 로 2 셀을 두고 근거리 제트를 주장한 사례는 찾지 못했다.**
2~3 셀을 명시적으로 쓴 사례가 셋 있는데, 셋 다 보정 장치를 달고 있다.

1. **Stipa 외 (2024)** *Wind Energy Science* 9:2301–2332, doi 10.5194/wes-9-2301-2024 의
   Actuator Farm Model.

   > "the AFM utilizes a **single actuator point at the rotor center** and **only requires two to
   > three mesh cells across the rotor diameter**… the AFM, as the name suggests, is developed to
   > **model wind farm clusters rather than isolated turbines**"

   2~3 셀은 전용 투영 함수(로터면 축대칭 + 유하방향 가우시안)로 벽법칙 스케일을 복원해서 산 것이고,
   **균일 body force 가 아니며 개별 로터의 근거리장을 명시적으로 포기한다.**
2. **Revaz & Porté-Agel (2021)** 의 가장 성긴 격자 G1 은 유하방향 3 점이지만 **로터면에는 6·9 점**이
   있다. 저자들은 투영이 "유하방향보다 로터면 방향에서 훨씬 더 중요하다"고 못박는다.
3. **PyroSim/FDS 공식 문서**의 제트팬 2 분할 — 위 4-2-2. 슈라우드 형상을 덧대야 맞았다.

가장 가까운 실내 사례는 Sohn 외(2023) Case 3·4 의 높이 50 mm 슬롯이 재배층 상자 안 25 mm
격자에서 2 셀이 되는 경우인데, 이는 우리가 논문의 두 수치를 나눠 얻은 값이고 저자가
"슬롯에 2 셀"이라고 쓴 적이 없다. 그 슬롯면에는 level 1~3 표면 세분이 걸려 있어 실제로는
최소 6.25 mm 까지 내려간다.

### 4-6. 우리 팬 셀 영역의 실제 힘 밀도

`vectorSemiImplicitSource` 가 `volumeMode absolute` 에서 하는 일은 **주어진 양을 선택된 셀들의
부피 합으로 나누는 것**이다(6-1 의 소스 인용 참조). 그러므로 총 추력은 정확히 보존되지만
**단위 부피당 힘은 cellZone 이 몇 셀을 잡느냐로 정해진다.** 5 번 케이스(F3, 6.0 CMM,
추력 0.372 N)를 예로 들면 이렇다.

| 기준 부피 | 부피 | 힘 밀도 |
|---|---|---|
| 물리적 팬 디스크 (π/4 × 0.20² × 0.08) | 0.00251 m³ | 148.0 N/m³ |
| `fan_params.json` 의 `momentum_source_N_m3` 가 쓰는 상자 (0.08 × 0.20 × 0.20) | 0.00320 m³ | **116.2 N/m³**(기록된 값) |
| `cellZone_box_cfd_m` 공칭 상자 (0.12 × 0.20 × 0.20) | 0.00480 m³ | 77.5 N/m³ |
| **0.10 m 격자에서 실제로 잡힌 8 셀** | **0.00800 m³** | **46.5 N/m³** |

곧 **추력은 물리적 팬 부피의 3.2 배에 걸쳐 퍼진다.** `FAN-CFD-METHOD.md` 4절과
케이스 표의 "소스 116.4 N/m³" 는 상자 기준 공칭값이고 solver 가 실제로 쓰는 값이 아니다.
입력은 N 단위이므로 계산이 틀린 것은 아니지만, 그 숫자를 "실제로 적용된 힘 밀도"로 읽으면 안 된다.
이 점은 격자를 바꿀 때마다 달라지므로 문서에 단서를 붙이는 것이 좋다.

이 희석이 낳는 오차의 방향은 Revaz & Porté-Agel(2021)이 그대로 적어 두었다.

> "**a larger part of the force is projected outside of the turbine rotor, the force is
> concentrated in the center of the rotor and the force is underestim[ated]**"

---

## 5. 캐노피(작물층) 해상도

### 5-1. 논문이 쓴 값

**캐노피 두께당 셀 수를 저자가 직접 밝힌 논문은 없다.** 캐노피 두께와 셀 크기를 둘 다 적은
논문에서만 나눗셈으로 얻을 수 있다.

| 논문 | 캐노피 표현 | 캐노피 두께 | 그 안의 셀 크기 | 두께당 셀(환산) |
|---|---|---|---|---|
| **Zhang 외 2025** Agronomy 15:2326 | 상추를 **다공체**(점성저항 25, 관성저항 1.3) | **0.18 m**(재배판 위 공간 전체) | 초기 셀 높이 **0.01 m** | **약 18** |
| **Gao 외 2025** Appl. Sci. 15:4329 | 작물을 **다공체** | **0.12 m** | 미보고(총 셀 수에서 환산 약 0.025 m) | **약 5** |
| **Sohn 외 2023** Comput. Electron. Agric. 215:108363 | 상추를 **다공체**(Darcy–Forchheimer, 공극률 0.9, Kozeny) | **0.10 m**(4000 × 630 × 100 mm) | 세분 상자(높이 150 mm) level 1 → **0.025 m** | **약 4** |
| **Chen 외 2024** Agriculture 14:2227 | 배추를 **다공체**(공극률 0.9, LAD 41.2, 특성 잎 길이 40 mm) | 재배층 높이 250·300·350 mm | 전역 최소 1 mm ~ 최대 100 mm | 환산 불가(다공체 영역의 셀 크기 미보고) |
| **Gu & Goto 2024** Agriculture 14:1199 | **실제 식물 형상**을 그림(다공체 아님) | — | 잎 **0.004 m**, 줄기 0.0006 ~ 0.001 m | 해당 없음. 잎 한 장을 여러 셀로 나눈다 |
| **Yu 외 2023** Horticulturae 9:660 | 다공체, S_i = −LAI·C_d·ρU², **C_d = 0.32** | 미보고 | **미보고** | 환산 불가 |

판단: 확인 가능한 세 사례가 **4, 5, 18 셀**이다. 하한이 4 셀이고, 그마저도 컨테이너 수직농장에서
0.10 m 캐노피를 0.025 m 로 나눈 경우다. **우리 0.25 m 캐노피를 0.10 m 로 나누면 2~3 셀이고,
이는 확인된 하한보다 낮다.**

### 5-1-1. 캐노피 두께당 셀 수를 명시적으로 규정한 두 출처

거의 유일하게 숫자로 못박은 것이 둘 있다.

**Tolladay, J.; Chemel, C. (2021)** 「Numerical Modelling of Neutral Boundary-Layer Flow Across a
Forested Ridge」 *Boundary-Layer Meteorology* 180:457–476, doi 10.1007/s10546-021-00628-y.
캐노피를 운동량 흡수원 F_c = −C_d·a·|u|u 로 두었다.

> "The grid is stretched such that the lowest level has a height of approximately h/h_c = 0.1,
> **providing 10 levels within the canopy**. A lowest grid level height of **h/h_c = 0.2 was also
> considered** but the results are not shown because **the difference between the two cases was
> negligible**."
> "a **vertical resolution of 0.1 to 0.2 h_c was appropriate**"

곧 **캐노피 두께의 0.1 ~ 0.2 배**, 두께당 **5 ~ 10 셀**이고 5 셀이면 충분하다고 직접 보였다.
우리 0.10 m ÷ 0.25 m = **0.4 h_c** 로, 이들이 시험한 가장 성긴 값의 두 배다.

**SimScale 공식 문서 「Porosity & Porous Media」**
(https://www.simscale.com/docs/simulation-setup/advanced-concepts/porous-media/) —
OpenFOAM 기반 상용 솔버의 공식 문서이며, 조사 범위에서 **도구 문서 가운데 유일하게 숫자를 댄다.**

> "**Make sure at least 5 mesh cells are placed across the porous media thickness.**"

**Kibwika, Seo & Seo (2023)** *AgriEngineering* 5(3):1395–1414 는 온실에서 이 요건을 맞추려고
아예 형상을 바꿨다.

> "**To have more than one grid cell across the plant canopy rows** during model discretization,
> 3 plant rows in the standard greenhouse were simplified into 1 row in the model greenhouse."

곧 2 ha 온실에서 0.8 m 격자를 쓰면서도, 캐노피 줄에 셀이 하나도 안 들어가는 것은 못 받아들여
작물 줄을 합쳤다.

### 5-1-2. 시설원예 쪽의 실제 캐노피 격자

| 논문 | 캐노피 | 캐노피 안 셀 |
|---|---|---|
| **Bouhoun Ali, H.; Bournet, P.-E.; Cannavo, P.; Chantoiseau, E. (2019)** *Biosystems Engineering* 186:130–145, doi 10.1016/j.biosystemseng.2019.06.021 | **0.33 m**(화분 포함) — 우리 0.25 m 와 가장 가깝다 | "**The canopy consisted of 10 × 100 cells**" (전체 151 × 330 구조 격자). 두께 방향 **10 셀** |
| **Majdoubi 외 (2009)** *Agric. For. Meteorol.* 149:1050–1062, doi 10.1016/j.agrformet.2009.01.002 및 **Majdoubi 외 (2016)** *Open J. Fluid Dyn.* 6:88–100, doi 10.4236/ojfd.2016.62008 | 1 ha 온실, 2.6 m 두께 토마토 다공체, LAD 2.3 m⁻¹, C_D 0.32 | "Grid-cell dimensions inside the greenhouse vary between **(0.26, 0.44, 0.032)** near the soil and walls and **(0.75, 1.25, 0.1)** at 2.5 m high". 곧 **0.10 m 는 이들의 캐노피 안 가장 성긴 연직 셀**이고, 그 위치는 캐노피 꼭대기다 |

### 5-1-3. 캐노피를 성기게 그렸을 때 생기는 오차

- **Hou 외 (2025)** *Agronomy* 15(3):586, doi 10.3390/agronomy15030586 — 작물 다공체를 육면체
  블록으로 두면 RMSE **0.99 ℃**, 평균상대오차 **4.3 %**. LiDAR 볼록껍질 형상으로 더 잘게
  그리면 **0.71 ℃**, **2.9 %**. 곧 다공체 형상의 거칢만으로 온도 RMSE 0.3 ℃, 오차 1.4 %p 가 났다.
  (셀 수는 10~20 배 늘어난다.)
- 두께당 셀 수를 1 → 10 으로 훑으며 다공체 항력의 격자 민감도를 잰 최근 연구가 하나 있는데
  (Tokiwa, Yin, Onishi, arXiv:2605.25096), **동료심사 전 프리프린트**라 수치를 근거로 쓰지 않는다.
  참고로만 적으면, 통상적인 일정-C_D 다공체 모델의 총 항력이 격자 해상도만으로
  표준편차 약 27 % 를 보였다고 보고한다.

### 5-2. 우리 경우의 특수성

`docs/FAN-CFD-METHOD.md` 10절이 밝힌 대로 **우리는 작물을 다공체로 넣지 않았다.** 캐노피 자리는
비어 있고 판정면만 두 장 놓았다. 그래서 위 논문들과 성격이 조금 다르다.

- 좋은 쪽: 다공체 저항을 풀지 않으므로 캐노피 안 저항 구배를 해상할 필요가 없다.
  두께당 셀 수 요건이 다공체 사례보다는 느슨하다.
- 나쁜 쪽: 판정면이 선반면 +0.125 m 와 +0.25 m 두 장인데, **0.10 m 격자에서 이 두 높이는
  기껏해야 두 셀 차이다.** 두 판정면이 사실상 같은 셀 줄을 읽을 위험이 있다.
  "캐노피 중간과 윗면의 차이"를 논하려면 두 면 사이에 셀이 적어도 두세 줄은 있어야 한다.
  0.05 m 로 가면 두 면 사이가 2~3 셀이 되어 최소 요건을 채운다.
- 앞으로 다공체를 넣게 되면(10절의 교체 지점) 두께당 4 셀 이상이 사실상 하한이 된다.
  그때는 0.05 m 로도 5 셀이라 겨우 맞고, 0.10 m 로는 못 맞춘다.

---

## 6. 1차 출처 지침 인용

### 6-1. OpenFOAM 공식 문서

**`vectorSemiImplicitSource` 의 `volumeMode`** — OpenFOAM v2306 API Guide,
`Foam::fv::SemiImplicitSource<Type>` (https://api.openfoam.com/2306/classFoam_1_1fv_1_1SemiImplicitSource.html)

> Options for the volumeMode entry:
> absolute | Values are given as \<quantity\>
> specific | Values are given as \<quantity\>/m3

우리는 `absolute` 로 추력을 N 단위로 준다. 곧 **셀 영역이 커지든 작아지든 방에 들어가는 총
운동량은 변하지 않는다.** 격자가 바꾸는 것은 그 운동량이 어디에 어떻게 퍼지느냐다.
`docs/FAN-CFD-METHOD.md` 4절의 설명은 이 문서와 어긋나지 않는다.

구현을 소스에서 확인하면 더 분명하다. `SemiImplicitSource.C`
(https://api.openfoam.com/2506/SemiImplicitSource_8C_source.html)

```cpp
if (volumeMode_ == vmAbsolute)
{
    VDash_ = V_;
}
...
const dimensioned<Type> SuValue("Su", SuDims, iter2.val()->value(tmVal)/VDash_);
```

그리고 `V_` 는 부모 클래스 `cellSetOption`
(https://api.openfoam.com/2506/classFoam_1_1fv_1_1cellSetOption.html)에서
**"Sum of cell volumes"** — 선택된 셀들의 부피 합으로 정의된다.

곧 `absolute` 는 **준 값을 선택된 셀 부피의 합으로 나눠** 체적력으로 바꾼다.
총 추력은 보존되고, **힘 밀도는 cellZone 이 잡는 셀 수에 반비례한다.** 4-6 절의 표가 그 결과다.

**`boxToCell` 의 셀 중심 판정** — OpenFOAM v2306 API Guide, `Foam::boxToCell`
(https://api.openfoam.com/2306/classFoam_1_1boxToCell.html)

> A topoSetCellSource to select all cells whose **cell centre** inside given bounding box(es).

`docs/FAN-CFD-ERRATA.md` E-001 의 원인 진단은 공식 문서와 정확히 일치한다. 상자가 격자 한 변보다
얇으면 셀 중심을 하나도 못 잡을 수 있다는 것은 구현상의 우연이 아니라 문서에 적힌 동작이다.

**국소 세분 도구** — OpenFOAM v2306 API Guide

> `refineHexMesh` : "Refine a hex mesh by **2x2x2 cell splitting** for the specified cellSet."
> (https://api.openfoam.com/2306/refineHexMesh_8C.html)

> `refineMesh` : "Utility to refine cells in multiple directions. … If `-all` specified or no
> refineMeshDict exists, refine all cells. If `-dict <file>` specified refine according to
> `<file>`. … When the refinement of all cells is selected apply 3D refinement for 3D cases and
> 2D refinement for 2D cases."
> (https://api.openfoam.com/2306/refineMesh_8C.html)

> `hexRef8` : Description "Refinement of (split) hexes using polyTopoChange."
> `setRefinement()` : "**Insert refinement. All selected cells will be split into 8.**"
> `consistentRefinement()` / `consistentUnrefinement()` 가 이웃 셀과의 **2:1 세분 단계 제약**을
> 강제한다. (https://api.openfoam.com/2306/classFoam_1_1hexRef8.html)

곧 한 단계 세분은 셀 하나를 여덟 개로 쪼개고, 그 안의 셀 한 변은 절반이 된다.
우리 0.10 m 상자 안을 0.05 m 로 만드는 데 필요한 것이 이것이다.
한 단계면 0.05 m(팬 지름당 4 셀, 캐노피 5 셀), 두 단계면 0.025 m(팬 지름당 8 셀,
캐노피 10 셀, 팬 두께 약 3 셀)가 된다.

**격자 품질 규정은 있다.** ESI 사용자 안내서의 `meshQualityDict` 기본값은
`maxNonOrtho 65`, `maxBoundarySkewness 20`, `maxInternalSkewness 4`, `maxConcave 80`,
`minVol 1e-13`, `minTetQuality 1e-15`, `minDeterminant 0.001`, `minVolRatio 0.01`,
`minTwist 0.02`, `minFaceWeight 0.05` 다
(https://doc.openfoam.com/2306/tools/pre-processing/mesh/generation/snappyhexmesh/meshquality/).

**그러나 OpenFOAM 공식 문서 어디에도 "소스 영역·다공체 영역·개구부를 가로지르는 최소 셀 수"에
관한 규정은 없다.** 확인한 범위에서의 부정적 결과다.

### 6-1-1. 우리가 안 쓰고 있는 OpenFOAM 기본 기능 둘

- **`actuationDiskSource`** (https://api.openfoam.com/2506/classFoam_1_1fv_1_1actuationDiskSource.html)
  — "applies momentum sources to velocity … to simulate actuator disk models for horizontal-axis
  turbines". `diskArea`, `diskDir`, `Cp`, `Ct` 를 받고 `cellSetOption` 을 상속한다.
  해상도 요건은 문서에 없다. 우리 팬을 추력계수로 다루고 싶으면 이쪽이 더 자연스러울 수 있다.
- **`atmPlantCanopyUSource`** (https://api.openfoam.com/2506/classFoam_1_1fv_1_1atmPlantCanopyUSource.html)
  — "Applies sources on velocity (i.e. `U`) to incorporate effects of plant canopy for atmospheric
  boundary layer modelling". 입력이 **`Cd`(항력계수)와 `LAD`(엽면적밀도, 1/m)** 다.
  근거는 Sogachev & Panferov (2006) *Boundary-Layer Meteorology* 121(2):229–266,
  doi 10.1007/s10546-006-9073-5. 나중에 작물을 넣을 때 Darcy–Forchheimer 대신 쓸 수 있는
  **기본 제공 대안**이고, 시설원예 문헌이 쓰는 LAD·C_D 값을 그대로 넣을 수 있다.
- `explicitPorositySource` 는 "**The porous region must be selected as a cellZone.**" 이라고만
  적혀 있고 역시 해상도 규정이 없다.

### 6-2. AIJ 지침 — 건물 한 변에 최소 10 셀

**Tominaga, Y.; Mochida, A.; Yoshie, R.; Kataoka, H.; Nozu, T.; Yoshikawa, M.; Shirasawa, T. (2008)**
「AIJ guidelines for practical applications of CFD to pedestrian wind environment around buildings」
*J. Wind Eng. Ind. Aerodyn.* 96(10–11):1749–1761, doi 10.1016/j.jweia.2008.02.058.
(출판사판은 유료. 도쿄공예대 풍공학연구센터가 공개한 저자 원고 전문을 읽었다.)

> **§4.1** "According to cross comparisons results for a simple building model …,
> **the minimum of ten grids is required on one side of a building to reproduce the separation
> flow around the upwind corners.**"

> **§4.1** "Grid shapes should be set up so that the widths of adjacent grids are similar,
> especially in regions with a steep velocity gradient. In these regions, **it is desirable to
> set a stretching ratio of adjacent grids of 1.3 or less.**"

> **§4.2** "**The minimum grid resolution should be set to about 1/10 of the building scale
> (about 0.5–5.0 m)** within the region including the evaluation points around the target building.
> Moreover, **the grids should be arranged so that the evaluation height (1.5–5.0 m above ground)
> is located at the 3rd or higher grid from the ground surface.**"

> **§4.3** "It should be confirmed that the prediction result does not change significantly with
> different grid systems. **The number of fine meshes should be at least 1.5 times the number of
> coarse meshes in each dimension (Ferziger and Peric, 2002).**"

> **§4.3** "COST indicates that at least three systematically and substantially refined grids
> should be used so that **the ratio of cells for two consecutive grids should be at least 3.4**
> … The value of 3.4 means finer grids with 1.5 times the grid number in three dimensions,
> i.e., 1.5³ = 3.375."

AIJ 지침은 **실외 보행자 풍환경**용이고 실내 기류용이 아니다. 그대로 적용할 수는 없다.
다만 "관심 물체의 한 변에 최소 10 셀", "인접 셀 확대비 1.3 이하", "세분은 방향마다 1.5 배"라는
세 규정은 물체 크기에 견준 해상도 기준이라 우리 팬(0.20 m)과 캐노피(0.25 m)에 옮겨 읽을 수 있다.
일본건축학회가 펴낸 **실내** 기류 CFD 지침은 찾지 못했다. 일본에서 실내를 다루는 것은
공기조화·위생공학회(SHASE)의 『はじめての環境・設備設計シミュレーション CFDガイドブック』
(オーム社, 2017, ISBN 978-4-274-22153-8)이고, 2장 4절이 「メッシュの品質チェック」인 것까지는
목차로 확인했으나 **본문은 확보하지 못했다.** 수치를 인용하지 않는다.

### 6-3. ASHRAE — 숫자로 된 격자 규정은 없다

**ASHRAE Handbook—Fundamentals, Chapter 13 "Indoor Environmental Modeling"**(2021 SI판 전문 확인).
격자 크기를 정해 주는 수치 규정은 **없다.** 「Grid Independence」 항의 원문은 이렇다.

> "**Grid Independence.** The level of grid independence from the flow field solution is important
> to determine in advance. … Grid independence can be achieved experimentally by using successive
> grid refinements in areas with sharp gradients or cell skewness. This allows solutions obtained
> with coarser and finer grids to be compared. **If results of two successive trials are comparable,
> then both models are grid-independent.** … new CFD users should not assume a solution is grid
> independent: different levels of grid can yield results different enough to make conclusions
> drawn from the flow field unreliable."

수치에 가장 가까운 두 문장은 이렇다.

> "At the interface of the block-structured grid, the ratio of cell size change (i.e., large to
> small cells) between two blocks **is recommended to be no more than two** (Ferziger and Peric 1997)."

> "**If a grid has cell sizes of 10 mm, then flow field features smaller than 20 mm cannot be
> solved.** Therefore, sharp gradients of flow field variables necessitate a finer mesh."

마지막 문장이 우리에게 가장 아프다. 이 기준을 그대로 쓰면 **0.10 m 격자는 0.20 m 보다 작은
유동 구조를 풀 수 없다.** 우리 팬 지름이 정확히 0.20 m 이고 캐노피 두께는 0.25 m 다.
곧 팬 제트의 내부 구조는 원리상 풀리지 않고, 캐노피 두께 방향 분포도 겨우 경계에 걸린다.

**ASHRAE Handbook—HVAC Applications, Chapter 59 "Indoor Airflow Modeling"** 에는 실제 수치 예가 있다.

> "The base size of cells in the room might be relatively large depending on the complexity of the
> flow regime, but **a grid independence test should be conducted** to determine that a balance
> between calculation time and accuracy has been achieved."

> 사무실 예: "**The 300 mm base size was also checked for grid independence, where smaller base size
> did not yield a change in results in monitor points near the occupants** (due to the refinement,
> the cell size is roughly 25 mm near the occupants…)."

여기서 쓰는 방식이 정확히 우리가 검토 중인 것이다. **방 전체는 0.3 m 로 두고 관심 물체 주변만
0.025 m 로 12 배 세분한다.** ASHRAE 가 실내 기류 해석의 표준 관행으로 싣고 있는 구성이다.

수술실 예는 격자 수렴을 이렇게 했다.

> "The grid refinement study was conducted on the following grids: 70 × 58 × 45 (180 k cells),
> 87 × 73 × 57 (362 k cells), 106 × 91 × 70 (675 k cells), 124 × 111 × 86 (1.2 million cells),
> and 155 × 142 × 108 (2.4 million cells). … **the computational error is typically below 10%,
> and absolutely below 30%. Based on this, and to minimize the simulation time, the 362k mesh
> was chosen** for various parametric simulations."

ASHRAE Standard 55 는 온열 쾌적 기준이라 격자 규정이 없다.

### 6-4. Chen & Srebric (2002) — ASHRAE RP-1133 절차

**Chen, Q.; Srebric, J. (2002)** 「A procedure for verification, validation, and reporting of indoor
environment CFD analyses」 *HVAC&R Research* 8(2):201–216. (저자 공개본 전문 확인.)

> "**Therefore, it is not sufficient to perform CFD computations on a single fixed grid.**
> The difference in grid size and time step between two cases should be sufficiently large in
> order to identify the differences in CFD results. **The common way is to repeat the computation
> by doubling the grid number and compare the two solutions** (Wilcox 1993). The study is very
> important to separate numerical error from turbulence-model error, since no objective evaluation
> of the merits of different turbulence models can be made unless the discretization error of the
> numerical algorithm is known."

보고 요건은 이렇다.

> "**The CFD report should also include grid refinement studies. Since the coarse grid introduces
> more numerical viscosity, grid-refinement study is essentially necessary to achieve a
> grid-independent solution. Although it may not be realistic to conduct grid refinement for the
> complete system, such a grid refinement should be conducted for benchmark cases, in order to
> estimate the errors introduced in the complete system.**"

마지막 문장이 우리에게 그대로 들어맞는다. **30 케이스 전부에 격자 수렴을 할 필요는 없고,
대표 케이스 하나에만 하고 그 오차를 전체에 적용해 보고하면 된다.**

RP-1133 의 실제 수치 예(Srebric & Chen 2002, *ASHRAE Transactions* 108(2):185–194)는 이렇다.

> 2 차원 벤치마크: "The systematical refinement of the grid resolution is conducted in this study
> for the grid number from **35×32, 40×40, to 50×50**. … **The comparison indicates that the
> calculation with 35×32 grids already produces accurate results with a less than 3% difference,
> compared with finer grids.**"

> 3 차원 실: "A grid dependent study was also performed with three different grid resolutions:
> **29×30×19, 48×44×24, and 72×66×36**. **For such a complicated system, it is very difficult to
> reach grid independent results. The results show that the difference between two finer grids is
> very small. Therefore, 48×44×24 grids were considered to be sufficient.**"

Chen & Srebric 은 스스로 표준이 아님을 밝힌다.

> "This paper provides a manual … **but its intent is not to develop standards.** The extent of
> CFD's capability in modeling has not yet developed to the point where standards can be written."

같은 저자의 다른 글(Chen, Q.; Zhai, Z. 2004, 「The use of CFD tools for indoor environmental design」,
*Advanced Building Simulation*, Spon Press, pp. 119–140)은 실내 기류 CFD 초심자가 틀리는 지점을
다섯 개로 정리했는데, 그 가운데 둘이 우리 문제다.

> "• Incorrect setting of boundary conditions for the air-supply diffuser
> • Inappropriate selection of grid resolution"

### 6-5. COST Action 732 — 최소 해상도와 확대비

**Franke, J.; Hellsten, A.; Schlünzen, H.; Carissimo, B. (eds.) (2007)** 「Best Practice Guideline
for the CFD Simulation of Flows in the Urban Environment」, COST Action 732. (전문 확인.)

> "Ideally the grid is equidistant. Therefore, grid stretching/compression should be small in
> regions of high gradients, to keep the truncation error small. **The expansion ratio between two
> consecutive cells should be below 1.3 in these regions.**"

> "**In the area of interest, at least 10 cells per cube root of the building volume should be used
> and 10 cells per building separation to simulate flow fields. This must be understood as an
> initial minimum grid resolution.**"

> "With regard to the shape of the computational cells, **hexahedra are preferable to tetrahedra**,
> as the former are known to introduce smaller truncation errors and display better iterative
> convergence."

세분비에 대한 논의도 실려 있다.

> "For code verification it was stated that the ideal case is **r = 2** … **Ferziger & Peric (2002)
> recommend at least an increase of 50% of the cells in each coordinate direction, corresponding to
> r ≈ 3.4.** Stern et al. (2001) state that for industrial applications **r = 2^(1/2)** is an
> appropriate choice and **Roache (1998) shows that even r = 1.1 is enough for simple meshes.**"

주의: AIJ·COST 의 "3.4"는 **셀 수** 비이고, Celik 의 "1.3"은 **셀 크기** 비다. 단위를 섞으면 안 된다.
방향마다 1.5 배 = 셀 크기 비 1.5 = 셀 수 비 3.4 이고, 이는 Celik 의 1.3 을 넉넉히 넘는다.

---

## 7. 우리 케이스에 대한 권고

**최종 결정은 사람이 한다.** 여기서는 선택지와 각각의 근거·비용만 정리한다.

### 7-1. 지금 상태를 숫자로

| 항목 | 값 |
|---|---|
| 격자 | 0.10 m 균일 육면체, 구배 없음, **84,024 셀** |
| 등가 셀 한 변 | 100 mm (문헌 6 ~ 25 mm) |
| 팬 지름 0.20 m 를 가로지르는 셀 | **2** |
| 팬 셀 영역이 잡는 셀 수 | **8**(2 × 2 × 2, E-001 확인 로그) |
| 캐노피 두께 0.25 m 를 가로지르는 셀 | **2 ~ 3** |
| 선반 두께 0.05 m · 기둥 0.06 m | **1 셀 미만** — 형상이 격자에 맞춰 부풀어 있다 |
| 케이스당 벽시계 | 약 14 분 / 11 코어 |
| 30 케이스 합계 | 약 **7 시간** |

### 7-2. 선택지

계산량 배수는 셀 수 증가와 쿠랑수 기반 시간 간격 축소를 함께 본 값이다(적응 Δt 기준).
Δt 를 고정한다면 셀 수 배수만 곱하면 된다.

| 안 | 내용 | 팬 지름당 셀 | 캐노피 두께당 셀 | 셀 수 | 계산량 | 30 케이스 |
|---|---|---|---|---|---|---|
| **A** | 0.10 m 그대로 | 2 | 2~3 | 84,024 | 1× | 7 시간 |
| **B** | 재배단+팬을 감싸는 상자만 `refineHexMesh` **1 단계**(그 안 0.05 m) | **4** | **5** | 약 13 만 | 약 3× | 약 **22 시간** |
| **C** | 같은 상자 1 단계 + 팬·캐노피만 **2 단계**(그 안 0.025 m) | **8** | **10** | 약 25 만 | 약 12× | 약 **3.5 일** |
| **D** | 전역 0.05 m | 4 | 5 | 672,192 | 약 16× | 약 **4.7 일** |

**A — 0.10 m 유지.** 생각보다 근거가 있다. 그리고 한계도 분명하다.

옹호할 수 있는 쪽: Srebric & Chen(2002)은 5.16 × 3.65 × 2.43 m 시험실을 **평균 0.087 × 0.096
× 0.074 m** 셀로 나누고, 셀보다 작은 취출 장치를 운동량법으로 넣어 **격자 독립성과 실측 일치를
모두 얻었다**. 곧 "방 규모 격자 + 셀 이하 송풍 장치"는 검증된 실내 기류 CFD 관행이다.
게다가 `volumeMode absolute` 이므로 **방에 들어가는 총 운동량은 격자와 무관하게 정확하다**
(OpenFOAM 소스에서 확인, 6-1). 케이스 사이의 상대 비교는 성립한다.

옹호할 수 없는 쪽: 같은 논문이 "**The momentum method failed to predict the jet development.
The jet decay predicted is too fast… The results are much worse if the grid number is reduced.**"
라고 적어 두었고, 그 관행이 성립하는 전제는 **토출 분포를 실측으로 규정하는 것**이다
(RP-1009). 우리는 그 실측이 없다. 토출 분포를 규정하지 않고 같은 면적·같은 운동량으로
대체했을 때 Nielsen(1998)이 잰 오차가 **재실역 풍속 40 %** 다. 그리고 ASHRAE Fundamentals
13 장의 "10 mm 격자는 20 mm 보다 작은 구조를 못 푼다"를 그대로 쓰면 0.10 m 격자는
0.20 m 보다 작은 구조를 못 푼다. 팬 제트의 퍼짐이 바로 그 크기다.
캐노피 2~3 셀은 명시적 하한 5 셀(Tolladay & Chemel 2021, SimScale 문서)보다 낮다.

A 를 고른다면 본문에 이렇게 적어야 한다. **"팬이 방에 넣는 총 운동량과 케이스 사이의 상대
순위만 주장한다. 캐노피 풍속의 절댓값, 제트의 도달거리·감쇠·유인은 주장하지 않는다."**

**B — 국소 1 단계 세분. 이것을 권한다.** 이유는 넷이다.
1. ASHRAE HVAC Applications 59 장이 싣는 실내 기류 표준 관행이 정확히 이 구성이다.
   방 전체 300 mm, 재실자 주변 25 mm.
2. Sohn 외(2023)가 컨테이너 수직농장에서 쓴 구성과 같다. 기본 50 mm, 재배층 상자만 level 1.
3. 팬 지름당 4 셀, 캐노피 두께당 5 셀이 된다. **캐노피 5 셀은 문헌이 명시한 하한과 정확히 같다.**
   Tolladay & Chemel(2021)이 "0.2 h_c 로도 차이가 무시할 만했다"고 직접 보인 값이고,
   SimScale 공식 문서가 "다공체 두께에 최소 5 셀"이라고 적은 값이며, Gao 외(2025)의 0.12 m
   작물층 해상도(환산 약 5 셀)와도 같다. 팬 4 셀은 여전히 액추에이터 디스크 하한(7~10 셀)에
   못 미친다.
4. `src/fan_bc.py` 의 `MESH_CELL` 을 0.05 로 바꾸면 `zone_box()` 의 부풀림이 사라지고
   **실제 팬 치수 0.08 × 0.20 × 0.20 m 를 그대로 셀 영역으로 쓸 수 있다.** E-001 의 임시방편이
   필요 없어진다.

   계산량 3 배는 30 케이스에 22 시간이다. 하룻밤이면 끝난다.

**C — 팬·캐노피만 2 단계.** 팬 지름당 8 셀, 캐노피 10 셀, 팬 두께 약 3 셀이 된다.
**이것이 문헌이 실제로 요구하는 수준이다.** 근거가 여럿 겹친다.

- Lee 외(2023)는 지름 0.2 m 에어컨 취출구를 0.025 m 미만으로 나눴다(지름당 8 셀 이상).
- van der Laan 외(2019)의 D/8, Sanderse 외(2011)의 "10 cells per rotor diameter are sufficient",
  Revaz & Porté-Agel(2021)의 "8 and 12 grid points" 수렴 지점, Stipa 외(2024)의 "at least seven
  grid points across the turbine diameter" — 모두 7 ~ 12 셀로 모인다.
- AIJ 의 "물체 한 변에 최소 10 셀", COST 732 의 "at least 10 cells per cube root of the building
  volume", Hwang & Gorlé(2022)의 "at least 10 cells across … the edges of the openings" 와도 맞는다.
- 캐노피 10 셀은 Bouhoun Ali 외(2019)가 0.33 m 캐노피에 쓴 10 셀과 같다.

다만 3.5 일이 든다. **30 케이스 전부에 쓸 것이 아니라, 격자 수렴 확인용 최조밀 격자로
한 케이스에만 쓰는 것이 합리적이다.**

**E — 격자를 그대로 두고 주장을 줄이거나 소스를 보정한다.** 이것은 B·C 와 배타적이지 않다.
Nielsen(1997·1998)과 Srebric & Chen(2001·2002)이 실제로 권하는 길은 격자를 키우는 것이 아니라
**토출 분포를 규정하고 무엇을 주장하지 않을지 밝히는 것**이다. 우리가 할 수 있는 형태는 둘이다.
- 실물 팬을 정하면 카탈로그 또는 측정 토출 속도 분포를 받아 `fan_params.json` 의 추력을 보정한다.
- 보고서에서 팬 근방(지름 2~3 배 이내) 값은 인용하지 않고, 캐노피 판정면만 인용한다.
  Sanderse 외(2011)가 "at distances larger than a rotor diameter" 라고 한 그 선이다.
  우리 팬에서 캐노피 중앙까지는 약 1.3 m 로 지름의 6.5 배라 이 조건은 이미 충족한다.

**D — 전역 0.05 m.** 권하지 않는다. B 와 해상도가 같은데 계산량이 다섯 배다. 방 구석 빈 공간을
쪼개는 데 시간을 쓴다. Kibwika 외(2023)가 보인 대로, 기울기가 작은 영역을 성기게 두고도
RMSE 4 % 를 얻을 수 있다.

### 7-3. 격자 수렴을 어떻게 확인할 것인가

Chen & Srebric(2002)이 명시했듯 **30 케이스 전부에 할 필요는 없다.** 대표 케이스 하나에만 하고
그 오차를 전체에 적용해 보고한다.

1. **케이스 하나를 고른다.** 5 번 F3(6.0 CMM, 캐노피 목표 0.5 m/s)을 권한다. 풍량 중간값이고
   G1 곡선의 중앙이라 대표성이 있다. `FAN-CFD-METHOD.md` 5절은 3 번 F1 을 권했는데,
   F1 은 가장 약한 풍량이라 제트 구조가 가장 약하다. 격자 민감도를 보려면 중간이 낫다.
2. **격자 셋을 만든다.** A(0.10 m) / B(국소 0.05 m) / C(국소 0.025 m).
   국소 영역 안의 셀 크기 비는 **r = 2** 이고, 이는 Celik 외(2008)의 **r > 1.3** 을 넉넉히 넘는다.
   Celik 의 대표 셀 크기 정의는 영역 평균이지만, 같은 Step 1 에 이런 단서가 있다.

   > "Eqs. (1) and (2) are to be used when integral quantities, e.g., drag coefficient is
   > considered. **For field variables, the local cell size can be used.**"

   우리 판정량은 판정면의 장(field) 변수이므로 **국소 셀 크기 0.10 / 0.05 / 0.025 m 를 h 로 쓰고
   그 사실을 본문에 밝히면 된다.**
3. **감시량 φ 를 둘 정한다.**
   - φ₁ = 단별 캐노피 판정면(선반면 +0.125 m)의 **평균 풍속**
   - φ₂ = 같은 면의 **적정구간(0.3~1.0 m/s) 비율**
   φ₁ 은 문헌 선례가 있고, φ₂ 는 없다. 두 지표의 수렴 거동이 다를 수 있으므로 따로 보고한다.
4. **계산 순서.** 잔차가 정규화 기준으로 3 자릿수 이상 떨어졌는지 먼저 확인한다(Celik 예비 조건).
   그 다음 p = (1/ln r₂₁)·|ln|ε₃₂/ε₂₁| + q(p)|, φ_ext, e_a, GCI_fine = 1.25·e_a/(r^p − 1) 를 낸다.
   ε₃₂/ε₂₁ 이 음수면 진동 수렴이므로 안전계수를 1.25 가 아니라 3 으로 바꾼다(Roache 5.9.2).
5. **판정선.** 문헌의 사실상 합격선은 1 ~ 5 % 다. **GCI ≤ 5 %** 를 1 차 기준으로 둔다.
   Jung 외(2026)가 같은 기준을 썼고, Mohd Zainuddin 외(2023)도 같다.
   - B 의 GCI 가 5 % 이내면 **B 로 30 케이스를 돌린다.**
   - B 가 5 % 를 넘고 C 가 5 % 이내면 **B 와 C 의 차이를 보정 계수로 써서 B 로 돌리고 오차를
     명시하거나**, 캐노피 절댓값을 쓸 일이 있으면 C 로 간다.
   - A 만 돌릴 수밖에 없다면, Kibwika 외(2023) 방식으로 **C 를 기준 격자 삼아 A 의 RMSE 와 R² 를
     내고 RMSE ≤ 5 %·R² ≥ 0.95 를 넘는지 본다.** 넘으면 A 를 쓸 근거가 생긴다.
6. **보고.** 어느 쪽이든 `FAN-CFD-METHOD.md` 5절에 세 격자의 셀 수, r, p, e_a, GCI, 감시량과
   그 위치를 숫자로 적는다. Chen & Srebric 이 요구하는 보고 항목이 그것이다.

추가 비용은 대표 케이스 하나를 B 와 C 로 한 번씩 더 돌리는 것뿐이다.
14 분 × (3 + 12) ≈ **3.5 시간**이면 격자 근거가 선다. 30 케이스 7 시간에 견주면 싸다.

### 7-4. 격자와 함께 손봐야 할 것

- **차분 기법.** Kang 외(2024)는 "1 차 상류 기법은 특히 성긴 격자에서 실험과 크게 어긋난다"고
  보고했다(초록만 확인). 성긴 격자를 쓸수록 대류항을 2 차 이상으로 두는 것이 중요하다.
  `fvSchemes` 의 `div(phi,U)` 가 무엇인지 확인해야 한다.
- **`MESH_CELL` 상수.** `src/fan_bc.py` 의 `MESH_CELL = 0.10` 은 격자를 바꾸면 반드시 함께
  바꿔야 한다. 안 바꾸면 셀 영역이 필요 이상으로 부풀어 팬이 실제보다 두껍게 작동한다.
  총 추력은 같지만 운동량이 퍼지는 부피가 달라진다.
- **`momentum_source_N_m3` 의 의미.** 이 값은 실제 팬 상자(0.0032 m³) 기준 공칭값이고
  solver 가 쓰는 힘 밀도가 아니다. 0.10 m 격자에서 실제로 잡히는 8 셀(0.008 m³) 기준으로는
  그 **2.5 분의 1**이다(4-6). `volumeMode absolute` 라 총 추력은 정확하므로 계산이 틀린 것은
  아니지만, 문서에서 이 숫자를 "적용된 힘 밀도"로 읽히게 두면 안 된다. 단서를 붙이거나
  실제 cellZone 부피 기준 값을 함께 적는 것이 좋다.
- **판정면 사이 간격.** 판정면이 선반면 +0.125 m 와 +0.25 m 인데 0.10 m 격자에서는 두 면이
  사실상 같은 셀 줄을 읽을 수 있다. 0.05 m 로 가면 사이에 2~3 셀이 생긴다(5-2).
- **빈 셀 영역 검사.** `Allrun` 의 `cellZoneSet .* now size 0` 검사는 격자를 바꿔도 그대로 유효하다.
  유지한다.
- **선반·기둥.** 두께 0.05 m 선반과 0.06 m 기둥은 0.10 m 격자에서 한 셀도 못 채운다.
  `subsetMesh` 로 덜어내면 실제보다 두꺼운 판이 된다. 0.05 m 로 가면 선반이 1 셀, 기둥이 1 셀이
  되어 적어도 존재는 하게 된다. 이것도 B 를 택할 이유다.

---

## 8. 찾지 못한 것 / 열린 질문

### 8-1. 원문을 구하지 못한 것

| 문헌 | 왜 필요한가 | 상태 |
|---|---|---|
| **Roache (1994)** JFE 116(3):405–413 | GCI 원 논문 | **유료.** ASME Digital Collection 403. 저자 본인 책(1998/2009) 5장으로 대신 인용했다 |
| **Roache (1997)** Annu. Rev. Fluid Mech. 29:123–160 | GCI 후속 정리 | **유료. 내용 확인 못 함** |
| **Celik 외 (2008)** JFE 130:078001 | 다섯 단계 절차 | 출판판은 유료. **미국 NRC 가 공개한 JFE 편집방침 문서 사본**으로 전문 확인 |
| **Richardson (1911), Richardson & Gaunt (1927)** | Richardson 외삽 원전 | DOI 등록정보로 서지만 확인. **본문 못 읽음** |
| **ASME V&V 20-2009 (R2021)** | 표준 원문 | 유료. **공식 카탈로그의 범위 문장만 확인** |
| **Kang, Zhang, Kacira & van Hooff (2024)** Biosyst. Eng. 243:148–174 | 수직농장 CFD 의 **격자 해상도 민감도**를 정면으로 다룬 유일한 논문 | OA 로 표시되는데 ScienceDirect·TU/e 저장소 둘 다 403. **초록만 확인.** 가장 아쉽다 |
| **Kang & van Hooff (2024)** Dev. Built Environ. 17:100304 | 측면 급기 수직농장 최적화 | 같은 이유로 **초록만 확인** |
| **Fang 외 (2020)** Biosyst. Eng. 200:1–12 | "130 만/330 만/740 만 셀"의 유일한 미확인 후보 | **유료. 못 열었다** |
| **Larochelle Martin & Monfet (2024)** Eng. Appl. Comput. Fluid Mech. 18:2297027 | CEA-HD 기류 최적화, CC-BY 인데 접근 불가 | Taylor & Francis 403. 2022 년 eSim 학회판은 전문 확인 |
| **SHASE 『CFDガイドブック』(2017)** | 일본의 **실내** 기류 CFD 지침 | 목차(2 장 4 절 メッシュの品質チェック)만 확인. **본문 미확보. 수치 인용 안 함** |
| **Baker, Kelly & O'Sullivan (2019)** Int. J. Ventilation 19(4) | 실내 기류 프로파일의 GCI 와 격자 형식 영향 | **유료. 초록만** |
| **이정민 외 (2024)**, **Hwang 외 (2020)** | 국내 컨테이너형 수직농장 | KCI 공개분에 **격자 수치가 없다.** 본문은 RISS·DBpia 유료 |
| **Nielsen, P.V. (2015)** 「Fifty years of CFD for room air distribution」 Build. Environ. 91:78–90 | 실내 기류 CFD 50 년 정리 | **유료. 초록만 확인.** 격자에 관한 인용 가능한 문장 없음 |
| **Abdelmaksoud, W.A. (2015)** 「Effect of CFD Grid Resolution and Turbulent Quantities on the Jet Flow Prediction」 ASHRAE Trans. 121(1), CH-15-002 | 제트 지름당 최소 셀 수를 정면으로 다룬 유일한 논문 | **유료. 본문 못 구함.** 검색 스니펫에 "1~6 cells per jet radius" 가 보이나 **원문 대조 못 함. 인용하지 않는다** |
| **Deng 외 (2018)** Build. Environ. 141 | 운동량법의 격자 의존성 | **초록만 확인** |
| **Shapiro 외 (2019)** Wind Energy 22 | 저해상 액추에이터 디스크의 출력 과대예측 | **초록만 확인** |
| **Martínez-Tossas 외 (2015)** Wind Energy 18(6), **Jha 외 (2014)**, **Shives & Crawford (2013)**, **Wu & Porté-Agel (2011)** | 액추에이터 라인·디스크 해상도 | **유료.** 수치는 이들을 인용한 공개 논문을 통한 **2 차 인용**이므로 본문에 쓰지 않았다 |
| **Boulard & Wang (2002)** Comput. Electron. Agric. 34:173–190 · **Bournet & Boulard (2010)** 74:195–217 · **Bournet & Rojano (2022)** 201:107277 · **Bartzanas/Kittas (2004)** · **Piscia 외** | 온실 다공체 캐노피의 고전 문헌 | **모두 유료, 저장소 사본 없음. 격자 수치 못 얻음** |
| **COST Action 732 지침** | 실외지만 격자 규정의 1 차 출처 | 전문은 읽었으나 **제3자가 올린 사본**이다. 공식·대학 호스트 사본을 못 찾았다 |

### 8-2. 문헌에서 답을 못 찾은 질문

1. **"130 만 / 330 만 / 740 만 셀" 의 출처.** `FAN-CFD-METHOD.md` 5절에 적힌 이 숫자는
   확인한 후보 어디에도 없다. Fang 외(2020)를 열기 전까지 **인용하지 않는 것이 맞다.**
2. **균일 운동량 소스를 지름당 2 셀로 두고 근거리장을 주장한 published 사례.** 찾지 못했다.
   2~3 셀을 쓴 사례는 셋 있으나 모두 전용 투영 함수(Stipa 외 2024), 로터면에는 6~9 점 확보
   (Revaz & Porté-Agel 2021), 또는 슈라우드 형상 추가(PyroSim/FDS 문서)라는 보정을 달고 있다.
   실내 사례로는 Sohn 외(2023)의 50 mm 급기 슬롯이 기본 25 mm 격자에서 약 2 셀이 되는 경우가
   가장 가까운데, 우리가 역산한 값이고 저자가 밝힌 값이 아니며 표면 세분이 따로 걸려 있다.
3. **캐노피 두께당 셀 수를 명시한 시설원예 논문.** 거의 없다. Bouhoun Ali 외(2019)가
   "The canopy consisted of 10 × 100 cells" 로 유일하게 직접 적었다. Zhang 외(2025)는 캐노피
   0.18 m 와 초기 셀 0.01 m 를 함께 적어 18 셀이 역산되고, Gao 외(2025)는 작물층 0.12 m 와
   총 셀 수에서 약 5 셀이 역산된다. 명시적 하한은 시설원예 밖에서 왔다 —
   Tolladay & Chemel(2021)의 5~10 셀, SimScale 문서의 "최소 5 셀".
   **우리가 이 숫자를 명시하면 이 문헌군에서 앞서는 부분이 된다.**
4. **균일도 지표(상대표준편차, 적정구간 비율, 정체 비율)로 격자 수렴을 판정한 논문.**
   확인 범위에 없다. 판정 지표는 거의 다 점 풍속이나 점 온도다. 온도에서 보인 격자 독립성이
   균일도 지표에 그대로 옮겨 간다는 보장은 없다.
5. **운동량 소스 방식 팬의 셀 영역 최소 해상도를 규정한 문헌.** 실내 농업 쪽에서는 못 찾았다.
   OpenFOAM 공식 문서에도 없다. 풍력 액추에이터 디스크의 7~10 셀 관행을 빌려 쓰는 수밖에
   없는데, 이는 자유 대기 중 수십 m 로터를 대상으로 한 값이라 0.20 m 팬에 그대로 적용해도
   되는지는 별도 논거가 필요하다. 레이놀즈수도 스케일도 다르다.
6. **실내·농업 문헌이 팬을 대부분 경계면으로 처리하는 이유.** 조사한 범위에서 팬을 셀 영역
   body force 로 둔 농업 논문은 Chen 외(2020, *Animals* 10:1067) 하나였고, 나머지는 속도 입구
   (Choi 외 2024), 압력 점프, 또는 아예 팬 없이 질량유량 입구(Naranjani 외 2022)였다.
   우리 방식이 소수파인 것은 분명한데, 그것이 방법론적 결함 때문인지 단순한 관행 차이인지는
   문헌만으로 판단하지 못했다. ANSYS Fluent 공식 문서는 팬 경계조건을 "A fan is considered to
   be **infinitely thin** … the fan zone is a type of **internal face zone**" 로 규정하고
   "The fan model **does not provide an accurate description of the detailed flow through the fan
   blades**. Instead, it predicts the amount of flow through the fan." 라고 한계를 밝힌다.
   면 기반으로 가면 "지름당 몇 셀" 문제 자체가 사라지지만, 우리가 팬을 내부 순환 장치로 둔
   이유(질량 보존)도 함께 사라지는지 따져 봐야 한다.
7. **일본건축학회(AIJ)의 실내 기류 CFD 지침.** 존재하지 않는 것으로 보인다. AIJ 지침은
   실외 보행자 풍환경용이다. 실내는 SHASE 소관이고 그 본문은 확보하지 못했다.
8. **우리 방이 D 자(반타원) 형상이라는 점이 격자에 주는 영향.** 곡면 벽을 계단형으로 근사하는
   현재 블록 격자의 오차를 다룬 문헌은 찾지 않았다. 캐노피 기류와 직접 관련이 적다고 보아
   이번 조사 범위에서 뺐다. 필요하면 따로 봐야 한다.
