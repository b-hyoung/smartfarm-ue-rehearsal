# 얼마나 오래 돌릴 것인가 — 문헌에서 확인한 수치

2026-09-22. 원문(출판사 페이지·DOI·오픈액세스 PDF·저자 원고)을 직접 받아 읽은 내용만 적는다.
초록만 본 것은 그 자리에 **초록만 확인**이라고 밝힌다. 수치는 원문 표기 그대로이고,
우리가 계산해서 얻은 값은 **환산**이라고 따로 표시한다.
격자 조사는 `docs/FAN-CFD-MESH-REFERENCES.md`, 해석 방법은 `docs/FAN-CFD-METHOD.md` 6·8절,
정해 둔 값은 `docs/START-HERE.md` 3절에 있다.

---

## 1. 한 문단 요약

**"몇 초를 돌려라"는 규정은 어느 1차 지침에도 없다.** ASHRAE Fundamentals 13장,
ASHRAE HVAC Applications 59장, COST Action 732, AIJ 지침, Chen & Srebric(2002) RP-1133 을
다 읽었지만 모사 시간을 정해 주는 문장은 하나도 없다. 이들이 규정하는 것은 **격자와 시간 간격을
체계적으로 바꿔 보라**는 것, **잔차만 보지 말고 감시점의 목표 변수를 함께 기록하라**는 것뿐이다.
숫자로 된 관행은 **LES 의 flow-through 배수** 하나뿐이다 — 초기 5~100 배를 버리고 20~250 배를
평균한다(Gousseau 외 2013, van Hooff 외 2017, Hwang & Gorlé 2022·2023). 그런데 그쪽의
flow-through time 은 **체적÷유량이 아니라 영역 길이÷기준 속도**이고, 배수만 옮기면 우리 방에서
기준 속도에 따라 20 배가 벌어진다. **배수 자체는 옮겨지지 않는다.** 옮겨지는 것은 **방법**이고,
그것을 농업 시설에서 실제로 해 보인 논문이 하나 있다. **Janke 외(2020)** 는 OpenFOAM LES 로
젖소 우사를 풀면서 **발달 구간과 평균 구간을 따로 유도**했다 — 발달은 영역 길이 ÷ 구동 속도,
평균은 **관심 영역을 약 18 회 통과**할 만큼, 그리고 **구간을 옮겨 재평균해 사후 검증**한다.
이 처방을 우리 캐노피 판정면(폭 2.4 m, 그 안 실측 P50 0.152 m/s)에 넣으면 **평균 구간 284 초**가
나오고, 이는 우리 자신의 실측("300 초부터 P10 이 0.4 % 안에서 머문다")과 거의 같다.
**서로 다른 두 경로가 같은 자리를 가리킨다.** 환기횟수 쪽 선례는 1.65 회(Oh 외 2023)에서
93 회(Choi 외 2024)까지 흩어져 있고, 흩어짐의 원인은 **판정 대상과 허용오차의 차이**다 —
같은 방식으로 가장 엄한 Colombari 외(2024)는 감시 변수 10⁻³ 기준에서 교환 11~20 회를 썼고,
우리 방에 옮기면 2,500~4,700 초가 된다. 실내 농업 쪽 과도해석은 드물다. 이번에 온실·식물공장
MDPI 12 편과 축사 오픈액세스 약 160 편을 훑었지만 진짜 과도는 **7 편**이었고, **식물공장·수직농장
선례는 Lee 외(2023) 하나뿐**이며 그것이 180 초다. 결정적인 증거는 문헌이 아니라 **우리가 이미
잰 숫자**다. 이 방의 열 시상수는 **τ = 232 초 = V/Q 와 0.2 % 이내로 일치**한다
(`docs/OBJECTIVES.md` 9절, 900 초 실행 회귀, RMS 0.018 K). 그러면 필요한 시간은 **무엇을 얼마나
엄하게 주장하느냐**로 정해진다 — 온도를 10 % 오차로 말하려면 534 초, 1 % 면 1,069 초,
Colombari 의 10⁻³ 이면 1,603 초다. **600 초는 온도 오차 7.5 % 자리**다. 그런데 우리 판정 지표는
온도가 아니라 속도이고(`FAN-CFD-METHOD.md` 6절이 온도를 순위에서 명시적으로 뺐다),
속도는 훨씬 빨리 자리 잡는다 — 5번 케이스에서 300 초와 600 초의 캐노피 P10 차이가 **0.4 %** 로,
조사 범위에서 가장 엄한 공표 기준인 van Hooff 외(2017)의 **0.5 %** 안에 이미 들어 있다.
**결론은 이렇다. 600 초라는 길이 자체는 맞다. 틀린 것은 그 600 초를 쓰는 방법이다** —
지금은 600 초 전부를 발달 구간으로 쓰고 **마지막 한 장**을 읽는다. 문헌이 말하는 구성은
**300 초 발달 + 300 초 시간평균**이고, 비용은 똑같다. 부력이 섞인 실내 흐름은 정상에 도달하지
않고 계속 흔들린다는 보고가 일관되며(Yao & Yao 2022: 잔차를 10⁻¹²까지 떨어뜨려도 진동,
**5,500 초를 시간평균**), 같은 조건에서 두 개의 안정 해가 공존하기도 한다
(Heiselberg 외 2004, Hunt & Linden 2005). Blocken(2015)은 할 일을 한 문장으로 적어 두었다 —
**"저장해서 평균하라."** 우리는 이미 30 초마다 전 필드를 저장하고 `purgeWrite 0` 이다.
**시간평균은 계산을 한 번도 더 돌리지 않고 채점만 고쳐서 지금 당장 할 수 있다.**

---

## 2. 과도해석을 한 논문들

### 2-1. 실내 농업·온실·축사

| 논문 | 대상 공간·체적 | 환기량/ACH | 모사한 물리 시간 | 시간 간격 | 정상 먼저? | 난류 모델 | 총 계산 시간 | 충분하다는 근거 | 접근 |
|---|---|---|---|---|---|---|---|---|---|
| **Lee 외 2023** · Horticulturae 9:1027 · doi 10.3390/horticulturae9091027 | **육묘 식물공장** 4.37 × 2.6 × 2.45 m = 27.8 m³(대칭 절반) | 천장 취출구 지름 0.2 m × 6. 유량 미보고 | **180 s** | **1 s** 고정 | 아니오 | Realizable k-ε | i7 · **약 8 h** | **"After 120 s, the internal average temperature showed minimal variation, indicating that the system reached a nearly steady state."** — 감시 스칼라(방 평균 온도) | 원문 확인 |
| **Kibwika 외 2023** · AgriEngineering 5(3):1395 · doi 10.3390/agriengineering5030087 | Venlo 온실 **2 ha** | 자연환기(외부 3.1 m/s) | **본문에 두 값이 어긋난다.** "The transient simulation flow time was **10 min**" 와 "conducted for a total of **180 s**" | **1 s** 고정 | **예.** "The model was initially simulated in the steady state until convergence and then switched to the transient regime" | RNG k-ε + 강화 벽함수 | i7 · **12~60 h** | **없다.** 과도로 넘어간 목적은 CO₂ 추적가스 환기효율 계산 | 원문 확인 |
| **Li 외 2020** · PLOS ONE 15(9):e0239851 · doi 10.1371/journal.pone.0239851 | **아치형(중국식) 온실** 60 × 10.4 m, 재배면적 540 m². 체적 미보고 | 환기율 3.79 → 3.13 s⁻¹(외부 풍속 3.5 → 5.5 m/s, 원문 표기 그대로) | **600 s**(60 s 와 600 s 두 시각의 결과를 보고) | **미보고** | **예.** "the steady-state results are executed as initial values of the transient simulation to determine the greenhouse microclimate in the ventilated state" | Realizable k-ε + DO 복사 + 태양 광선추적 | Xeon E5-2678 v3 · 24 프로세서 · 벽시계 미보고. 약 65 만 다면체 셀 | **없다.** 실측 쪽 문장만 있다 — "The measured data were collected with constant time step of 30 s." | 원문 확인 |
| **Odhiambo 외 2020** · Sustainability 12(24):10412 · doi 10.3390/su122410412 | **난방 반밀폐 Venlo 온실** 83.6 × 40.59 m(약 3,393 m²), 처마 5.0 m·용마루 6.0 m. 팬코일 83 대 × 16.02 kW | ACH 미보고. 팬코일 토출을 속도 입구로 | **28,800 s**(09:00~17:00 = 480 min. 60·300·480 min 시점 보고). 시간 간격 시험용으로 **3,600 s** 별도 실행 | **60 s** 고정. **10 / 30 / 60 s 독립성 시험을 거쳐 선정** | 아니오(정상은 격자 독립성 시험에만). 초기조건은 실측 센서값 | **Lam-Bremhorst 저레이놀즈 k-ε** + DO 복사, 2차 유계 음해, 잔차 10⁻⁶ | Xeon Gold 6226 듀얼 24 코어 · 벽시계 미보고. 319 만 요소 | 물리 시간의 근거는 **없다.** 시간 간격은 있다 — **"to obtain a simulation solution independent of the time step, three transient simulations were carried out for a period of 3600 s … Independence tests were conducted with three time steps: 10 s, 30 s, and 60 s … There was no substantial difference between the three time steps."** | 원문 확인 |
| **Si 외 2023** · Energies 16:2305 · doi 10.3390/en16052305 | 중국식 태양광 온실(토양·작물·배면벽 연성) | 상부 환기창 개폐 | **3,600 s (1 h)** | **300 s (5 min)** | 아니오 | 표준 k-ε + 표준 벽함수(y⁺ 10~150), 작물역 층류 | 미보고 | **없다** | 원문 확인 |
| **Liu 외 2020** · PLOS ONE 15(4):e0231316 · doi 10.1371/journal.pone.0231316 | 중국식 태양광 온실 배면벽 내표면 구조 | 미보고 | **미보고** | **미보고**(시간 간격마다 최대 20 회 반복) | 아니오 | 표준 k-ε + 표준 벽함수 | 미보고 | **없다.** 10 분마다 자동 저장했다는 서술만 | 원문 확인 |
| **Colombari, Masoero & Della Torre 2024** · AgriEngineering 6(2):1525–1548 · doi 10.3390/agriengineering6020087 | **혼합환기 젖소 우사**(이탈리아 CerZoo, 약 100 두). HVLS 팬·순환팬·용마루 굴뚝. 체적 미보고 | **ACR 명시**: 겨울 폐쇄 **10.81 /h**, 겨울 개방 **11.08 /h**, 여름 폐쇄 **80.70 /h**, 여름 개방 **83.46 /h**. 최소 요구 4~10 /h | **정상에 도달할 때까지.** 관측값: **여름 15 min, 겨울 1 h** | 겨울 **1 s**, 여름 **0.1 s** | **뒤집혀 있다.** 과도 적분 자체가 정상해에 이르는 수단이다 | **OpenFOAM `buoyantKEpsilon`** + ABL 입구. 시간 1차 Euler. GAMG(10⁻⁷)·PBiCGStab(10⁻⁸), 스텝당 잔차 10⁻⁵ | 메시당 500~550 만 셀. 코어·벽시계 미보고. **격자 독립성은 하지 않았다고 명시** | **조사 범위에서 가장 직접적인 근거 문장.** 아래 3-2 에 전문 인용 | 원문 확인 |
| **Yeo 외 2020** · Agronomy 10(11):1828 · doi 10.3390/agronomy10111828 | **비육돈사** + 복잡 지형 외부 영역 | MWPS 기준 두당 환기요구량으로 산정. ACH 미보고 | **600 s (10 min)** (검증 실행). 케이스 108 개 | **5 s** 고정. **1 / 5 / 10 / 20 s 시험을 거쳐 선정** | 미보고 | **표준 k-ε**(RNG·Realizable·LES 와 RMSE·R² 비교해 선정) | 격자 376~873 만 요소. 코어·벽시계 미보고 | 물리 시간의 근거는 **없다.** 시간 간격은 있다 — **"the time steps of 1, 5, 10, and 20 s were considered for a calculation time of 10 min … Considering the excessive calculation time when using the 1 s time step, the 5 s time step was selected as the most economic time step value."** | 원문 확인 |
| **Choi 외 2024** · Animals 14(20):3019 · doi 10.3390/ani14203019 | **터널환기 육계사**(상용, 육계 30,000 수). 바닥 **87 × 15 m**, 용마루 5 m·처마 3.5 m. 측면 유입 배플 29 × 2 | **배기팬 14 대 × 37,000 m³/h**(팬 곡선, 압력차 의존). ACH 미보고. **환산**(전부 가동 가정) 약 93 /h, τ_n ≈ 39 s | **3,600 s**(2023-03-24 18:00~19:00 실측 구간) | **1 s** 고정 | **예**(격자 독립성만 정상, 이후 과도) | RNG k-ε + 표준 벽함수, Boussinesq, SIMPLE, 2차 | 미보고 | **없다.** 구간은 실측 시간대일 뿐이다. 수렴 기준만 — "The convergence criteria for the energy and other variables were set as 1.0 × 10⁻⁶ and 1.0 × 10⁻³" | 원문 확인 |
| **Janke 외 2020** · Comput. Electron. Agric. 175:105546 · doi 10.1016/j.compag.2020.105546 | **자연환기 젖소 우사**, 1:100 풍동 모형. 우사 높이 H ≈ 0.11 m, 폭 W = 0.34 m, Re ≈ 37,200 | 우사 통과 유량 실측 **12.96 × 10⁻² m³/s**. 계산값 13.25(OpenFOAM, +2.2 %)·13.11(ParMooN, +1.6 %) | **총 7 s.** 통계는 **[1, 7] s** 구간에서 수집 | OpenFOAM **적응 Δt**(Courant ≤ 3, 평균 2 × 10⁻⁴ s). ParMooN 고정 **2.5 × 10⁻⁴ s**(Crank–Nicolson), **28,000 스텝** | **아니오.** "In practice, the initial condition is not known. For this reason, one has to start with an arbitrary initial flow field" | **LES.** OpenFOAM PIMPLE + 1 방정식 와점성 SGS(`kEqn`), ParMooN 변분 다중스케일 | OpenFOAM **8.6 h · 120 CPU**(중간 격자 4,608,675 셀). ParMooN **80~100 h · 50 프로세서** | **조사 범위에서 유일하게 모사 시간을 유도하고 사후 검증까지 한 농업 논문.** 아래 3-1 에 §2.7 전문 인용 | 원문 확인(WIAS Preprint 2644) |
| **Oh, Seo & Seo 2023** · AgriEngineering 5(3):1378–1394 · doi 10.3390/agriengineering5030086 | **비육돈사 돈방** 12 m × 15.6 m × 3.2 m = **599 m³**(환산), 12 구획 · 300 두 | **AER 0.55 / 0.75 / 0.85 / 1.0 min⁻¹**(= 33~60 /h). **환산** τ_n = 109 s(0.55) ~ 60 s(1.0). 입구 3.71 m/s | **300 s**(60·180·300 s 시점 보고) | **미보고.** 결과 전체가 300 초 감쇠 곡선인데 Δt 가 어디에도 없다 | **예.** "The CFD model was initially initialized in the steady state, then modeled in the unsteady state for the ventilation efficiency analysis using the TGD method." | URANS, Realizable k-ε(4 모델 비교, R² 0.859) | 미보고 | **부분적으로 있다 — 물리량의 평탄화로 판단.** "The maximum ammonia reduction rate increased significantly from 28.8% at a ventilation time of 60 s to 42.6% at a ventilation time of 180 s. **However, there was no significant increase beyond 180 s**, with the reduction rate remaining at 42.5% at a ventilation time of 300 s." | 원문 확인 |
| **Manbeck 외 2016** · Frontiers in Public Health 4:108 · doi 10.3389/fpubh.2016.00108 | **비육돈사**(450 두) 12.2 × 30.5 × 3.05 m + **슬랏 덮개 분뇨조** 12.2 × 30.5 × **2.44 m 깊이** = **908 m³**(환산) | 분뇨조 팬 **지름 610 mm · 4.5 m³/s** → **환산** τ_n = 202 s. 축사 환기량은 본문에 **226.0 m³/s** 와 **26.0 m³/s** 가 모순되게 적혀 있다 | **최대 약 750 s.** 보고된 H₂S 배출 시간 163·174·275·286·303·351·510·523·>549·>737 s | Phoenics **10 s**, SolidWorks Flow Simulation **5 s**(낮은 AC 에서는 7 s 가 최적). 고정 | 미보고 | **미보고**(설계보조도구 논문) | 미보고 | **조사 범위에서 가장 명시적인 종료 규칙.** "The design aid sometimes terminates the simulation when … the hydrogen sulfide manure pit concentration **approaches 1 ppm nearly asymptotically**. This avoids excessive computer run time. … **a pit ventilation time of approximately 750 s is a satisfactory ventilation time**". **환산** 750 s = 3.72 τ_n | 원문 확인 |
| **Sousa Junior 외 2018** · Scientia Agricola 75(3):173–183 · doi 10.1590/1678-992X-2016-0110 | **임신돈사** 99.61 × 15.5 × 3.07 m | 입구 0.3 m/s × 유입면적 47 m², 배기팬 8 대(지름 1.38 m). 유량·ACH 미보고 | **블록당 25 s × 최대 10 회 = 250 s 이하** | **0.05 s** 고정(25 s 블록당 500 반복) | **예 — 그리고 과도해석을 물리가 아니라 수렴 가속기로 쓴 가장 분명한 사례다.** "The simulations were first carried out in steady state in 2,000 iterations to get a faster convergence. Thereafter, a total time of 25 s with a time step of 0.05 s was simulated … **This was repeated up to 10 times (loops) in an attempt to converge the variable values.**" | 표준 k-ε(ANSYS CFX), 확장 벽함수 | 미보고 | **물리적 근거 없음. 수렴 기준뿐이다.** "In steady-state, the simulations did not converge after 2,000 iterations … From this result a transient simulation was run and **all the variables converged quickly**, reaching residue below 10⁻⁷ (Moment and Mass), and 10⁻⁵ (Energy)." | 원문 확인(SciELO) |

**판단 넷.**

1. **실내 농업 CFD 는 압도적으로 정상해석이다.** `FAN-CFD-MESH-REFERENCES.md` 에서 원문을 연
   19 편 중 과도는 두 편이었다. 이번 조사에서 온실·식물공장 MDPI 계열 12 편과
   축사 오픈액세스 약 160 편을 추가로 훑었고, 그 가운데 **진짜 과도해석은 7 편**이었다.
   정상해석으로 확인해 제외한 것만 적어 두면: Agriculture 14:2227(마이크로 식물공장),
   Horticulturae 9:660(인공광 식물공장), Sustainability 15:5607, Agronomy 14:876,
   Sustainability 15:3056, Agronomy 13:197, Processes 9:1587, Animals 11:2352,
   Horticulturae 9:183, Sustainability 12:986, Agriculture 11:658, Energies 14:5956,
   Appl. Sci. 10:6054, Appl. Sci. 11:4560, Animals 12:867, Buildings 9:183, Animals 12:1776,
   Energies 6:2605, Agriculture 13:1101, Poult. Sci. 104:105786, Animals 14:2623, Animals 15:2263.
   **식물공장·수직농장 CFD 에서 과도해석 선례는 Lee 외(2023) 하나뿐이고 그것이 180 초다.**
   Janke 외(2020)도 같은 관찰을 적어 두었다 —
   "To the best of our knowledge, the only studies using a non-commercial solver to investigate the
   flow inside or around agricultural buildings … in all cases a steady-state RANS approach was used.
   **No study using transient open source solvers seem to be available.**"
   (우리는 OpenFOAM 과도해석을 하고 있다. 곧 선례가 거의 없는 자리에 있다.)
2. **물리 시간의 길이를 논거로 정당화한 농업 논문은 네 편**이다 — Janke 외(2020)의 flow-through
   유도 + 사후 검증(3-1), Colombari 외(2024)의 환기횟수 설명(3-2), Manbeck 외(2016)의
   점근 도달 종료 규칙, Oh 외(2023)의 물리량 평탄화. Lee 외(2023)의 "120 초 후 평균 온도가
   거의 안 변했다"가 다섯 번째로, 근거라기보다 관찰에 가깝다. 나머지는 그냥 적는다.
3. **과도해석을 물리가 아니라 수렴 가속기로 쓰는 경우가 있다.** Sousa Junior 외(2018)는
   정상해석이 2,000 반복에도 수렴하지 않자 과도로 넘어갔고, Colombari 외(2024)도 같은
   transient-to-steady 방식이다. 이 경우 "물리 시간이 충분한가"라는 질문 자체가 성립하지 않는다.
   **우리는 이쪽이 아니다.** 우리는 팬을 켰을 때의 실제 기류 분포를 보려는 것이다.
4. **시간 간격은 여러 편이 독립성 시험을 했다.** Odhiambo 외(2020) 10/30/60 s,
   Yeo 외(2020) 1/5/10/20 s, Manbeck 외(2016) 5/7/10 s, Markov 외(2020) 0.004~0.5 s.
   **우리는 하지 않았다.** COST 732 §5.10 과 Chen & Srebric(2002)이 요구하는 항목이다.

정상해석을 고르는 쪽의 논거도 적어 둔다. 우리에게 유리한 방향이라 더 조심해서 읽어야 한다.

> "**A steady-state approach was adopted because greenhouse airflow typically evolves towards
> quasi-steady conditions during daytime operation, in the absence of rapid changes in solar input,
> vent motion or wind forcing. The characteristic flow timescale (1–10 s) is significantly shorter
> than the thermal response time of the crop canopy, making transient resolution unnecessary.**"
> … 다만 같은 논문이 한계도 인정한다: "Future work should employ unsteady RANS or large-eddy
> simulation (LES) to capture the transient response."
>
> — Colimba-Limaico 외 (2026) *Eng* 7(5):194, doi 10.3390/eng7050194
>   (열대 터널 온실, OpenFOAM `buoyantSimpleFoam`, 원문 확인)

**"유동 시간척도 1~10 초는 캐노피 열응답 시간보다 훨씬 짧다"** — 이것이 우리 4-4 절의 관찰
(속도는 빨리, 온도는 늦게)과 같은 말이다.

### 2-2. 실내 기류(방·사무실·강의실·건물)

| 논문 | 대상 공간·체적 | 환기량/ACH | 모사한 물리 시간 | 시간 간격 | 정상 먼저? | 난류 모델 | 총 계산 시간 | 충분하다는 근거 | 접근 |
|---|---|---|---|---|---|---|---|---|---|
| **Yao & Yao 2022** · Fluids 7(6):192 · doi 10.3390/fluids7060192 | 모형 방 정육면체 **2.44 m 한 변 = 14.5 m³**. case 3 은 중앙에 **700 W** 가열 상자 | **0.10 m³/s**. **환산** ACH 24.8 /h, 교환 시간 **145 s** | **평균 구간만 20 × 5,000 스텝 = 5,500 s**(환산). 그 앞에 초기 과도 구간이 따로 | **0.055 s** 고정. "defined by the minimum cell size and convective airflow velocity at the inlet slot" | 아니오(균일장 출발) | URANS(k-ε 계열), **잔차 목표 10⁻¹²** | 미보고 | **"After the initial transient stage, and until the `statistically-converged` status is reached…"** 감시점 5 곳 시계열을 10 스텝마다 저장해 FFT | 원문 확인 |
| **Markov 외 2020** · Applied Sciences 10(15):5036 · doi 10.3390/app10155036 | **대학 강의실**(현장 실험실). 팬코일 4 대 × 4 급기 구획 | 구획당 실측 **146~212 m³/h**(16 구획 합 약 2,800 m³/h). 입구 벌크 4.26 m/s | CFD 표본 300 s·2,100 s 규모(표가 PDF 에서 깨져 있어 **재확인 필요**). **실측은 1 h** | **0.5 s** 고정. "The time step value, Δt, was varied … from Δt = 0.004 s to Δt = 0.5 s, and it was found that the lower frequencies and the time-averaged flow patterns were the same" | 아니오(성긴 격자 정상 RANS 를 비교용으로 따로) | URANS 표준 k-ε + 강화 벽처리, Fluent 18.2, SIMPLEC, 시공간 2차 | **3,300 만 육면체 셀**, **최대 504 코어** | **실측에서 준정상 시작 시각을 정했다.** "The temperature records … can be divided into 2 phases: the transient period and the quasi-steady-state period. **The transient phase takes about 1000 s**; the air temperature … drops from 32.44 ± 0.1 °C to 25.16 ± 0.2 °C." → "the assessment … was done for the temperature quasi-steady-state phase only, i.e., **for the period starting from the instant of 1020 s**" | 원문 확인 |
| **Morozova 외 2020** · Building and Environment 184:107144 · doi 10.1016/j.buildenv.2020.107144 | 실내 기류 표준 시험 둘 — 차등가열 공동(Saury), 바닥가열 환기공동(Blay). 실물 크기로 환산하면 1.71 × 6.57 × 1.47 m 아트리움과 1.78 × 1.78 × 0.51 m 방 | — | **무차원 시간 단위로 표기.** 시험 1: 정상 600 / 과도 10. 시험 2: 정상 500 / 과도 10 | 미표기 | — | URANS(OpenFOAM) · LES · 무모델(TermoFluids) 비교 | 논문 전체가 **비용 연구**. 실시간 배수 R 을 보고 | **"All steady simulations run for 600 non-dimensional time units, which was found to be a long enough time-integration period to record the flow statistics for further averaging. All transient simulations were carried out for 10 non-dimensional time units to capture the initial flow development."** | 원문 확인(UPC 저장소 저자 원고) |
| **Chen & Gorlé 2022** · Building and Environment 221:109240 · doi 10.1016/j.buildenv.2022.109240 | **3층 아트리움 사무실**(실물), 부력 단독 자연환기 | 창·루버 개방(유량을 해가 푼다) | **3 h (10,800 s)** | **가변 0.5 / 1.0 / 2.0 / 5.0 / 10 s** | 아니오 | 과도 RANS + 불확실성 정량화 | 미보고 | **"the optimal time steps are 0.5 s, 1.0 s, 2.0 s, and 5.0 s for 0 to 5 mins, 5 to 15 mins, 15 to 30 mins, and 30 to 60 mins … For the remaining two hours of the simulation, the time step is set to 10 s when a quasi-steady state is achieved."** → **준정상 도달이 약 60 분** | 원문 확인(arXiv 2203.05670) |
| **van Hooff, Blocken & Tominaga 2017** · Building and Environment 114:148–165 · doi 10.1016/j.buildenv.2016.12.019 | 고립 건물 횡단환기 | 외부 풍속 구동 | **평균 구간 375,000 스텝 = 75 s = 60 T_ft** | **2 × 10⁻⁴ s**(환산) | — | **LES** 와 정상 RANS 비교 | 미보고 | **"The simulation is terminated when the moving average of the mean velocity at all location remains within 0.5%."** — 조사 범위에서 가장 엄한 공표 기준 | 원문 확인 |
| **Gousseau, Blocken & van Heijst 2013** · Computers & Fluids 79:120–133 · doi 10.1016/j.compfluid.2013.03.006 | 고층 건물 주변 풍환경 | 외부 풍속 구동 | **T_init = 3.2 s = 5.4 T_ft, T_avg = 12.8 s = 21.8 T_ft** | 8 × 10⁻⁴ / 5.33 × 10⁻⁴ s. 최대 Courant ≈ 2.3 | **예.** RANS 해에 잡음을 얹어 출발 | **LES** | 8 프로세서 · **약 30 h** | 감시점 4 곳 이동평균 변동폭 **e_conv** 를 정의하고 **4.1 %** 를 수렴 근거로 | 원문 확인 |
| **Hwang & Gorlé 2022** · Front. Built Environ. 8:911005 및 8:911253 · doi 10.3389/fbuil.2022.911005 · .911253 | 슬럼가 단칸 주택(풍동 1:200) | 외부 풍속 6.6 m/s | **burn-in ≥ 100 τ_ref, 통계 250 τ_ref** | **0.0001 s**, max CFL < 1.0 | 아니오 | **LES**(CharLES) | 미보고 | **"The age of air calculation is performed once a quasi steady-state solution for the flow-field has been obtained, i.e. after the initial burn-in period."** | 원문 확인 |
| **Hwang & Gorlé 2023** · Flow 3:E10 · doi 10.1017/flo.2023.4 | 같은 주택, **부력 포함**(Ri −0.85 ~ 0) | 바람 + 실내외 온도차 | **burn-in ≥ 100 τ_ref, 통계 150 τ_ref** | **0.001 ~ 0.05 s**, max CFL < 1.0 | 아니오 | **LES** | 케이스당 **약 50,000 CPU·h**(544 코어) | **"the scalar is initialized once the burn-in period … has passed and a quasi-steady state condition is reached."** | 원문 확인 |
| **Jiang & Chen 2003** · Int. J. Heat and Mass Transfer 46(6):973–988 · doi 10.1016/S0017-9310(02)00373-3 | **부력 단독 단측 자연환기** 실물 시험실 | 개구부 자연환기 | **미보고** | **0.02 s** | 아니오 | **LES**(70 만 격자) | **10 일**. 같은 문제 정상 RANS 는 **2 일** | 없음. 실험에 대해 **"In the measurements, it took a long time to obtain the steady flow conditions."** | 원문 확인 |
| **Jiang 외 2003** · JWEIA 91(3):331–353 · doi 10.1016/S0167-6105(02)00380-X | 건물 자연환기 풍동 + LES | 외부 풍속(Re 140,000) | **미보고** | **4 × 10⁻⁴ s** | 아니오 | **LES** | 케이스당 **1 주** | **"the averaging time should be long enough to give an accurate ventilation rate."** — 방향만, 숫자 없음 | 원문 확인 |
| **Ajmani, Kirchhof, Rouhi & Mehring 2025** · Fluids 10(5):132 · doi 10.3390/fluids10050132 | 강의실(1D 덕트망 + 3D CFD 연성) | 기계환기 | 본 계산은 **정상(의사 시간전진)**. 과도는 **검증용** | 의사 시간전진 | **예** | RANS | 미보고 | **"the flow field was found to be quasi-steady, with low frequent limited amplitude flow asymmetries along the centerline of the symmetric lecture hall."** | 원문 확인 |
| **Ramponi & Blocken 2012** · Building and Environment 53:34–48 · doi 10.1016/j.buildenv.2012.01.004 | 고립 건물 횡단환기 | 외부 풍속 구동 | 정상 RANS 인데 **진동 수렴**이 나서 **10,000 반복에 걸쳐 감시·평균** | — | — | 정상 RANS(SST k-ω) | 미보고 | **"the oscillatory behavior of the results was monitored over 10000 iterations and the calculated variables were averaged when necessary."** | 원문 확인 |
| **Stavridou & Prinos 2017** · Procedia Environ. Sci. 38:322–330 · doi 10.1016/j.proenv.2017.03.087 | 국소 열원이 있는 자연환기 방 | — | **미보고** | 미보고 | 미보고 | **과도 RANS + RNG k-ε**(우리와 같은 계열) | 미보고 | 없음. 다만 **"the indoor air temperature of both layers increases with time"** — 분석 구간 끝까지 상태량이 흐르고 있다 | **초록만 확인** |

### 2-3. 우리 것과 견줄 수 있게 환산

아래 배수는 우리가 계산한 것이며 논문에 적힌 값이 아니다. **두 종류의 "회전수"를 구분한다.**

- **교환 시간 τ_n = V / Q** — 체적을 유량으로 나눈 값. 스칼라(온도·농도)가 갈리는 시계.
- **flow-through time T_ft = L / U** — 영역 길이를 기준 속도로 나눈 값. LES 문헌이 쓰는 단위.

| 사례 | 어떤 단위인가 | 버린 구간 | 평균·판정 구간 |
|---|---|---|---|
| Gousseau 외 2013(LES, 실외) | T_ft = L_x / U_h. **환산 T_ft = 0.59 s** | **5.4 T_ft** | **21.8 T_ft** |
| van Hooff 외 2017(LES, 횡단환기) | T_ft "through the computational domain". **환산 T_ft = 1.25 s** | 미보고 | **60 T_ft** |
| Hwang & Gorlé 2022(LES) | τ_ref = D_house / U_ref = **0.015 s** | **≥ 100 τ_ref** | **250 τ_ref**(= 약 3.75 s) |
| Hwang & Gorlé 2023(LES, 부력 포함) | τ_ref = L_house / U_wind | **≥ 100 τ_ref** | **150 τ_ref** |
| **Janke 외 2020**(LES, OpenFOAM, 우사) | **두 개를 따로 쓴다.** 발달은 영역 길이 30H ÷ 유입 속도 = **0.8 s**, 평균은 관심 영역 폭 W = 0.34 m 통과 = **1 초에 약 3 회** | **1 s**(≈ 1.25 영역 통과) | **6 s**(≈ **18 회 관심영역 통과**). 구간을 옮겨 재평균해 검증 |
| **Colombari 외 2024**(URANS, OpenFOAM, 우사) | **τ_n = 3600 / ACR**. 여름 **44.6 s**, 겨울 **333 s**(환산) | — | 정상 도달까지 **여름 20.2 τ_n, 겨울 10.8 τ_n**(환산) |
| **Oh 외 2023**(URANS, 돈방 599 m³) | **τ_n = 60 / AER**. AER 0.55 min⁻¹ → **109 s**, 1.0 min⁻¹ → **60 s**(환산) | 없음(정상해로 초기화) | 지표 평탄화가 **180 s = 1.65 ~ 3.0 τ_n**, 총 실행 **300 s = 2.75 ~ 5.0 τ_n**(환산) |
| **Manbeck 외 2016**(분뇨조 908 m³, 팬 4.5 m³/s) | **τ_n = 202 s**(환산) | — | 1 ppm 점근 도달까지 **750 s = 3.72 τ_n**(환산) |
| **Choi 외 2024**(육계사) | 팬 14 대 전부 가동 가정 시 **τ_n ≈ 39 s**(환산) | — | 3,600 s = **약 93 τ_n**(환산). 다만 팬이 켜졌다 꺼졌다 한다 |
| Yao & Yao 2022(URANS, 실내 방) | 저자는 "flow recirculation cycle" 로 셌다. **환산 τ_n = 145 s** | "initial transient stage"(길이 미보고) | **5,500 s = 37.9 τ_n**(환산) |
| Chen & Gorlé 2022(과도 RANS, 실물 건물) | — | **약 3,600 s** 까지가 과도 | 이후 **7,200 s** |
| Markov 외 2020(실측, 강의실) | — | **약 1,000 s** 까지가 과도 | 1,020 s 이후만 사용 |
| Lee 외 2023(식물공장) | — | **120 s**(저자가 안정 시점으로 지목) | 180 s 까지 |

**이 표에서 읽어야 할 것 넷.**

1. **LES 의 배수는 크지만 단위가 작다.** 250 τ_ref 가 실제로는 3.75 초다. 배수만 보고
   "우리는 2.6 배뿐이니 턱없이 모자라다"고 말하면 단위를 잘못 옮긴 것이다.
2. **우리와 같은 단위(τ_n = V/Q)로 읽을 수 있는 것이 다섯 편**이다. 흩어진 폭이 크다 —
   Oh 외(2023) **1.65~5 회**, Manbeck 외(2016) **3.7 회**, Colombari 외(2024) **10.8~20.2 회**,
   Yao & Yao(2022) **37.9 회**, Choi 외(2024) **약 93 회**. 우리는 **2.59 회**다.
   **이 흩어짐은 판정하려는 양과 허용오차가 서로 다르기 때문**이다 —
   Oh 는 암모니아 저감률의 평탄화, Manbeck 은 1 ppm 점근, Colombari 는 온도 10⁻³,
   Yao 는 속도 통계의 평균 구간, Choi 는 실측 시간대다. **배수 하나로 답이 나오지 않는다.**
   4-4 에서 허용오차로 환산해야 비교가 된다.
3. **Janke 외(2020)만 발달 구간과 평균 구간을 따로 유도했다.** 발달은 영역 길이 기준,
   평균은 **관심 영역** 통과 횟수 기준이다. 이 둘을 나눈 것이 우리에게 가장 쓸모 있다(4-5).
4. **실물 방을 실측한 Markov 외(2020)의 1,000 초**가 가장 직관적이다. 강의실을 냉방으로
   32.4 ℃ 에서 25.2 ℃ 로 내리는 데 실제로 1,000 초가 걸렸고, 그 전 구간은 분석에서 뺐다.

---

## 3. 얼마나 돌려야 충분한가 — 1차 출처

### 3-1. flow-through 배수 규정 — LES 쪽에만 있다

**Gousseau, P.; Blocken, B.; van Heijst, G.J.F. (2013)** 「Quality assessment of Large-Eddy
Simulation of wind flow around a high-rise building: validation and solution verification」
*Computers & Fluids* 79:120–133, doi 10.1016/j.compfluid.2013.03.006.

> "Each simulation is initialized with the solution of a preceding RANS simulation on which random
> noise is super-imposed. **After an initialization period T_init = 3.2 s corresponding to 5.4
> flow-through times (T_ft = L_x/U_h, where L_x is the length of the computational domain), the
> statistics are sampled for T_avg = 12.8 s = 21.8 T_ft = 718 tu.** It will be demonstrated in
> Section 5.1 that this averaging period is sufficiently long to provide converged mean values of
> velocity."

그리고 "충분히 길다"를 **숫자로 정의**한다.

> e_conv(I) = 100 × [ max(⟨u⟩_kΔt) − min(⟨u⟩_kΔt) ] / ⟨u⟩_Tavg,  k ∈ I
>
> "This indicator corresponds to the range of values that the moving-average takes within an
> interval I of time steps numbers in the averaging period … **e_conv shows a decreasing trend and
> reaches low values (4.1%) at the end of the averaging period, which indicates sufficient
> statistical convergence of the simulation.**"

감시점 고르는 법까지 적혀 있다.

> "Note that the points P2 and P3 are located in regions of the flowfield where quasi-periodic flow
> patterns occur … and limit the convergence of the statistics. **Observing the evolution of e_conv
> at these points is therefore a conservative way to assess the statistical convergence.**"

결론부의 한 줄이 규정 그 자체다.

> "**A suitable length for the averaging period has been determined by monitoring the moving average
> of velocity at several points in the flow field: 718 time units or 21.8 flow-through times.**"

**van Hooff, T.; Blocken, B.; Tominaga, Y. (2017)** *Building and Environment* 114:148–165,
doi 10.1016/j.buildenv.2016.12.019.

> "…presented here are **averaged over 375,000 time steps, which correspond to a flow time of 75 s,
> i.e. 60 times the flow-through time (through the computational domain). It is verified that the
> averaging time is sufficient to obtain statistically-steady results by monitoring the evolution of
> the mean velocity at several locations inside the enclosure with time (moving average).
> The simulation is terminated when the moving average of the mean velocity at all location remains
> within 0.5%.**"

**이것이 조사 범위에서 가장 명확한 합격선이다 — 모든 감시점의 이동평균이 0.5 % 안에 들어올 때까지.**
그리고 이 케이스는 **등온·운동량 지배**인데도 60 flow-through 가 필요했다.

**Hwang, Y.; Gorlé, C. (2022)** *Frontiers in Built Environment* 8:911253 및 8:911005.

> "**After running the simulations for an initial burn-in period of at least 100 τ_ref, the
> statistics of the quantities of interest are calculated using the flow solution obtained over
> 250 τ_ref, where τ_ref is the flow-through time for the target house (the ratio of the width of
> the house to the wind speed at the reference height, i.e., D_House/U_ref = 0.1/6.6 ≈ 0.015 s).**"

**Hwang, Y.; Gorlé, C. (2023)** *Flow* 3:E10, doi 10.1017/flo.2023.4 — 부력을 넣은 판.

> "**Statistics of the quantities of interest are calculated from flow solutions obtained over
> 150 τ_ref, after an initial burn-in period of at least 100 τ_ref.**"

**Janke, D.; Caiazzo, A.; Ahmed, N.; Alia, N.; Knoth, O.; Moreau, B.; Wilbrandt, U.; Willink, D.;
Amon, T.; John, V. (2020)** 「On the feasibility of using open source solvers for the simulation of
a turbulent air flow in a dairy barn」 *Computers and Electronics in Agriculture* 175:105546,
doi 10.1016/j.compag.2020.105546. **농업 시설 CFD 에서 모사 시간을 유도한 유일한 논문**이고,
우리와 같은 OpenFOAM LES 다. §2.7 「Time Interval」 전문을 옮긴다.

> "**The choice of the final time is briefly motivated in this section. The quantities of interest
> are time-averaged velocity profiles. Hence, one needs a sufficiently long time interval for
> obtaining statistically converged results.** The area of interest is inside the barn, which has a
> maximum height of H ≈ 0.11 m. According to the inflow profile, see Table 4, an air parcel starting
> at the half of this height has a velocity of about u = 4 m/s. **Consequently, the parcel passes the
> whole length of the domain (30H) in an interval of time of approximatively 0.8 s.** The area of
> interest inside the barn has a width of W = 0.34 m. **The given parcel passes this width around
> three times in one second. Based on these considerations, we assumed that a fully developed full
> profile can be obtained within a time interval of 1 s. Furthermore, a time interval of 6 s is
> assumed to be sufficient to achieve statistically converged velocity profiles. These estimate[s]
> were positively validated a posteriori based on the results of our numerical simulations.**"

사후 검증 방법도 적혀 있다.

> "At the time 1 s, a fully developed flow field was reached and the collection of the data was
> performed in the time range [1, 7] (s). **The comparison with different time intervals, e.g.,
> [1, 6] s or [2, 7] s, showed that the obtained results can be considered to be statistically
> converged.**"

**이것이 우리가 그대로 따라 할 수 있는 유일한 처방이다.** 네 단계로 요약된다.

1. **영역 길이 ÷ 구동 속도**로 유동이 한 번 지나가는 시간을 구한다 → **발달 구간**을 그만큼 둔다.
2. **관심 영역의 폭 ÷ 그 안의 속도**로 통과 시간을 구한다.
3. **관심 영역을 약 18 회 통과할 만큼 평균**한다(Janke 는 1 초에 3 회 × 6 초).
4. **평균 구간을 옮겨 다시 평균해 값이 안 바뀌는지 확인**한다([1,6] 대 [2,7]).

**주의.** Janke 의 케이스는 **등온·외부 바람 구동**이다. 우리 방은 부력이 섞여 있고 구동이
내부에 있다. 그래서 **1 단계(발달 구간)는 그대로 옮기면 안 된다** — 4-5 에서 따진다.
2~4 단계는 옮길 수 있다.

**정리.** LES 관행은 **초기 5~100 flow-through 를 버리고 20~250 flow-through 를 평균**한다.
버리는 양이 20 배나 벌어지는 이유는 **초기장을 어떻게 잡았느냐**다. Gousseau 는 RANS 해에
잡음을 얹어 출발해서 5.4 배로 끝났고, Hwang & Gorlé 는 그러지 않아 100 배가 필요했다.
**정상해로 초기화하면 버릴 구간이 크게 줄어든다** — 이것은 규정이 아니라 두 논문의 대조에서
읽히는 사실이고, 농업 쪽 Li 외(2020)·Kibwika 외(2023)가 실제로 쓰는 방법이기도 하다.

### 3-2. 환기횟수(air change) 배수 — 규정은 없다. 관측 보고가 하나 있다.

**"N 회 교환을 지나야 한다"고 규정한 지침은 어느 1차 출처에도 없다.**
ASHRAE Fundamentals 13장, HVAC Applications 59장, COST Action 732, AIJ 지침(2008),
Chen & Srebric(2002) RP-1133, OpenFOAM 공식 문서 어디에도 없다.

그러나 **정상 도달 시각을 환기횟수로 설명한 관측 보고**가 하나 있다.
우리와 같은 솔버 계열(OpenFOAM 부력 k-ε)이라 가장 옮기기 좋다.

**Colombari, D.; Masoero, F.; Della Torre, A. (2024)** 「A CFD Methodology for the Modelling of
Animal Thermal Welfare in Hybrid Ventilated Livestock Buildings」 *AgriEngineering* 6(2):1525–1548,
doi 10.3390/agriengineering6020087 (오픈액세스, 원문 확인).

> "**The barn was simulated as a transient system with constant boundary conditions until a
> steady-state solution was reached.** … **Maximum temperature in animal-occupied zones and
> area-averaged pressure on the east patch were monitored to check whether a steady-state condition
> was reached.** In winter conditions, also, the area-averaged flow rate exiting from the top
> boundary was checked. **For these variables, a relative tolerance of 1 × 10⁻³ was used as the
> convergence criterion.**"

> "**It was observed that the model seemed to reach a steady solution within 15 min of simulation
> time in summer conditions and 1 h in winter ones. This difference is due to the different air
> change rate that strongly shortens the characteristic thermal time between the two
> configurations.**"

> "As a transient-to-steady approach was adopted, **the size of the timestep was not influential on
> simulation results at a steady state.** The timestep was progressively lowered until a good
> compromise between numerical stability and simulation cost was reached."

같은 논문이 환기횟수를 정의하고 값을 적어 두었다.

> "ACR = V̇ / (V·h)" · 겨울 폐쇄 **10.81 1/h**, 겨울 개방 **11.08 1/h**,
> 여름 폐쇄 **80.70 1/h**, 여름 개방 **83.46 1/h**

**우리 환산**:

| | ACR | τ_n = 3600/ACR | 정상 도달 | 교환 배수 |
|---|---|---|---|---|
| 여름(팬 최대) | 80.70 /h | 44.6 s | 15 min = 900 s | **20.2 회** |
| 겨울(굴뚝만) | 10.81 /h | 333 s | 1 h = 3,600 s | **10.8 회** |

**곧 교환 11 ~ 20 회분**이다. 이것이 조사 범위에서 "몇 회 교환"에 가장 가까운 정량 선례다.
다만 이것은 **규정이 아니라 관측**이고, 감시량이 **온도와 압력**이며, 판정 허용오차가
**10⁻³** 이다. 그 허용오차가 얼마나 엄한 요구인지는 4-4 에서 산수로 따진다.

두 번째 선례는 Yao & Yao(2022)다. 14.5 m³ 방에서 **교환 38 회분을 시간평균**했다(2-3 표).
저자가 규정으로 내놓은 값이 아니라 우리가 역산한 것이다.

**규정이 없으므로 만들어 쓰지 않는다.** 우리가 실제로 쓸 수 있는 것은 4절의
"이 방의 시상수를 직접 쟀다"와 "판정 허용오차를 정하면 시간이 따라 나온다"이다.

### 3-3. 준정상 판정법 — 감시점 목표 변수

**Chen, Q.; Srebric, J. (2002)** 「A Procedure for Verification, Validation, and Reporting of
Indoor Environment CFD Analyses」 *HVAC&R Research* 8(2):201–216,
doi 10.1080/10789669.2002.10391437 (ASHRAE RP-1133 매뉴얼). Purdue 공개 저자 원고 전문 확인.

> "For indoor environment modeling, a CFD solution has converged if:
> **Residual for mass = The sum of the absolute residuals in each cell / the total mass inflow
> < 0.1%**
> **Residual for energy = The sum of the absolute residuals in each cell / the total heat gains
> < 1%**"

부력이 섞인 방에는 잔차가 쓸모없다고 못박는다.

> "Note that **for natural convection in a room, the net mass flow is zero.** Therefore, one can
> conclude that a convergence has been reached if there is **little change (no change in the 4th
> digit) on the major dependent variables (temperature, velocities, and concentrations) within the
> last 100 iterations.** However, **a small relaxation factor can always give a false indication of
> convergence** (Anderson et al. 1984)."

시간 간격에 대한 요구는 이 한 문장뿐이다.

> "Another important action in verification testing is **systematically refining the grid size and
> time step.** … **The time step applies only to transient flow simulation.** Therefore, it is not
> sufficient to perform CFD computations on a single fixed grid."

**모사 시간의 길이를 정해 주는 문장은 이 문서 전체에 없다.** 보고 요구 항목에도
"discretization technique, grid size and quality, **time step**, numerical schemes, iteration number,
and convergence criteria" 까지만 있고 총 물리 시간은 없다.

짝 논문 **Srebric, J.; Chen, Q. (2002)** 「An Example of Verification, Validation, and Reporting of
Indoor Environment CFD Analyses」 *ASHRAE Transactions* 108(2), RP-1133 예제편
(Purdue 공개 저자 원고 전문 확인)은 아예 정상해석을 고르고 그 이유를 적는다.

> "Since the office is ventilated by mechanical ventilation and the study is for ventilation design …
> **Therefore, a steady-state flow simulation is sufficient, because the steady state simulated a
> continuous hottest or coldest condition.**"
> "**This flow is a steady state so that the time step is not an issue.**"

### 3-4. 잔차만으로 판단하면 안 된다 — 가장 직접적인 경고

같은 RP-1133 예제편에 우리 상황을 정확히 짚은 문장이 있다.

> "It is also found in the verification process that **if monitoring points are used to assess the
> convergence, they should be placed in a region with higher velocity instead at the core for this
> case, where the velocity is low. This is because the velocity at the core still changes over time
> even though the residual error gets very small.**"

**우리 캐노피 판정면이 바로 그 "저속 코어"다.** 방 평균 속도가 0.15 m/s 대이고 P10 이
0.06~0.08 m/s 다. 잔차가 떨어져도 이 자리는 계속 움직인다는 것이 RP-1133 의 경고다.

**COST Action 732** 「Best Practice Guideline for the CFD Simulation of Flows in the Urban
Environment」(Franke 외 2007) §5.11.

> "In industrial applications typically a termination criterion of 0.001 is used, which is in general
> **too high to have a converged solution. A reduction of the residuals of at least four orders of
> magnitude is recommended.**"
> "**In addition to the residuals the target variables should also be recorded. If these variables
> are constant or oscillate around a constant value, then the solution can be regarded as converged.**"
> "**This procedure should also be followed when unsteady simulations are to be performed.**"

곧 **"목표 변수가 일정하거나 일정한 값 주위에서 진동하면 수렴으로 본다"** 가 COST 의 판정법이고,
과도해석에도 그대로 쓰라고 적혀 있다. **몇 초를 돌리라는 말은 없다.**

**Blocken, B. (2015)** 『Building and Environment』 91:219–245, doi 10.1016/j.buildenv.2015.02.015
(TU/e 저장소 저자 원고 전문 확인) §5.6 은 잔차와 국소 진동의 관계를 갈라 놓는다.

> "**oscillations are found for all residuals (Fig. 18d) but not for all points in the flow field
> (Fig. 18e).** Note that points 2 and 3, which show oscillatory convergence, belong to the regions
> in the actual flow field that are characterized by unsteadiness."

### 3-5. 시간 간격(Δt)에 관한 규정

**COST Action 732 §5.10** 이 조사 범위에서 Δt 를 숫자로 규정한 유일한 1차 지침이다.

> "When performing unsteady simulations, the size of the time step is another important parameter
> for the accuracy of the results. **If the relevant frequency range can be estimated, then the
> highest frequency should be resolved with at least 10 – 20 time steps per period** (Menter et al.,
> 2002). Another method to estimate the time step in advection dominated problems is the relation
> **Δt = CFL · Δx_min / U_max** … Choosing the minimum grid spacing and the maximum velocity makes
> this estimate conservative."
> "To assess the influence of the time step size on the results, **a systematic reduction or increase
> of the time step should be made, and the simulation repeated. The two results can then be analysed
> with the Richardson extrapolation.**"

우리 `maxCo 1.0` 적응 Δt 는 두 번째 방식(CFL 기반)을 그대로 따르고 있다.
**다만 COST 가 요구하는 "Δt 를 체계적으로 바꿔 다시 돌려 보기"는 우리가 아직 하지 않았다.**
농업 쪽에서는 Odhiambo 외(2020)(10/30/60 s), Yeo 외(2020)(1/5/10/20 s)가 했고,
실내 쪽에서는 Markov 외(2020)(0.004~0.5 s)가 했다.

우리 실행과 문헌의 시간 스텝 수를 견주면 이렇다(**환산**).

| | 물리 시간 | Δt | 총 시간 스텝 |
|---|---|---|---|
| Si 외 2023(온실) | 3,600 s | 300 s | **12** |
| Lee 외 2023(식물공장) | 180 s | 1 s | **180** |
| Kibwika 외 2023(온실) | 180 s | 1 s | **180** |
| Odhiambo 외 2020(온실) | 28,800 s | 60 s | **480** |
| Choi 외 2024(육계사) | 약 3,600 s | 1 s | **약 3,600** |
| **우리 (maxCo 1.0)** | **600 s** | **≈ 0.012 s** | **≈ 50,000** |

**시간 스텝 수로는 우리가 식물공장 문헌보다 280 배 촘촘하다.** 시간 간격의 적정성은
우리 쪽이 문제가 아니다. 문제는 **총 물리 시간**과 **무엇을 읽느냐**다.

### 3-6. 지침별 정리 — 무엇을 규정하고 무엇을 규정하지 않는가

| 1차 출처 | 모사 시간 규정 | Δt 규정 | 수렴·준정상 판정 | 접근 |
|---|---|---|---|---|
| **ASHRAE Handbook—Fundamentals Ch. 13 「Indoor Environmental Modeling」**(2021 SI) | **없음** | "systematically refining the grid size and **time step**". 숫자 없음 | RP-1133 과 같은 문장(같은 저자) | 원문 확인 |
| **ASHRAE Handbook—HVAC Applications Ch. 59 「Indoor Airflow Modeling」** | **없음.** 정상/과도 선택 지침만: **"Indoor environments are inherently unsteady, but a steady-state (SS) or a quasi-steady state (QSS) simplification can usually represent the bulk airflow pattern well. … An SS model simulates a snapshot of a moment in time."** | 없음 | 사무실 예제: **"when the absolute values of variables at the user-defined monitoring point did not change by more than about 0.1% over approximately 20 iterations"** | 원문 확인 |
| **Chen & Srebric (2002) RP-1133** · doi 10.1080/10789669.2002.10391437 | **없음** | "systematically refining … time step". 숫자 없음 | 질량 잔차 < 0.1 %, 에너지 < 1 %. **자연대류 방은 주요 변수 4째 자리가 100 반복 동안 안 변할 것.** 감시점은 저속 코어가 아니라 고속 영역 | 원문 확인 |
| **COST Action 732 (Franke 외 2007)** | **없음** | **주기당 10~20 스텝**, 또는 Δt = CFL·Δx_min/U_max. 체계적 변화 + Richardson 외삽 | **"If these variables are constant or oscillate around a constant value, then the solution can be regarded as converged."** 잔차는 4 자릿수 이상 감소 | 원문 확인(제3자 사본) |
| **AIJ 지침 (Tominaga 외 2008)** · doi 10.1016/j.jweia.2008.02.058 | **없음.** 실외 보행자 풍환경용 정상 RANS 지침이다 | 없음 | 격자 독립성과 감시점 대조만 | `FAN-CFD-MESH-REFERENCES.md` 6-2 에서 저자 원고 확인. **이번 조사에서 과도·평균 시간 관련 문장은 찾지 못했다** |
| **Nielsen 외 (2007) REHVA Guidebook No.10** | — | — | — | **못 구했다.** Aalborg VBN·HAL·CERN·Reading 저장소 모두 전문 비공개. **인용하지 않는다** |
| **NASA/TM-2009-215616 · AIAA-2009-948 (Georgiadis, Rizzetta & Fureby)**, AIAA Journal 48(8):1772–1784, doi 10.2514/1.J050232 | 숫자는 없지만 **절차**가 있다(아래) | — | T / 2T 배가 비교 | 원문 확인(NASA NTRS) |

LES 평균화 시간에 대한 **절차 규정**의 1차 출처가 이것이다.

> "**Starting from any initial state, solutions must be evolved for a sufficiently long period so
> that transients are purged from the computational flowfield, and an equilibrium turbulent state is
> achieved. This can be a long process, particularly for low Mach number flows.** If the transients
> have not been entirely removed, then temporal averages and statistical quantities may be corrupted.
> **It is a difficult task to determine exactly when the transients have been eliminated.** … If it
> is possible to initialize the flowfield with a solution obtained from the RANS equations, that
> might reduce the overall computing time."

> "**For example, the solution can be processed for a time period equal to T, and statistical
> information can be extracted. The solution may then be further processed to 2 T, statistics
> computed again, and compared to the prior ones. The procedure can be repeated until statistical
> information has temporally converged.** In this regard, **mean values of primitive variables such
> as u, v, … etc. converge quite rapidly whereas mean values of fluctuating quantities such as
> u'u', v'v', … etc. converge less rapidly** and subsequently require both longer sampling times and
> more careful monitoring."

마지막 문장이 우리에게 중요하다. **평균 속도는 빨리 수렴하고 변동량은 늦게 수렴한다.**
우리 판정 지표(P10·P50·P90)는 평균 속도 쪽에 가깝다.

---

## 4. 우리 숫자 대조

### 4-1. 두 가지 환산을 섞으면 안 된다

우리 방: V = **96.7 m³**, 에어컨 Q = **25 CMM = 0.4167 m³/s**.

| 값 | 계산 | 결과 |
|---|---|---|
| 교환 시간 τ_n = V/Q | 96.7 ÷ 0.4167 | **232.1 s** |
| 환기횟수 | 3600 ÷ 232.1 | **15.51 회/h** |

**질문에 적힌 환산은 맞다.** 600 s = 2.59 τ, 300 s = 1.29 τ, 180 s = 0.78 τ 다.

그러나 **LES 문헌의 "flow-through time" 은 이 τ 가 아니다.** 그쪽은 **영역 길이 ÷ 기준 속도**다.
우리 방에 옮기면 기준 속도를 무엇으로 잡느냐에 따라 값이 20 배 벌어진다(**우리 환산**).

| 기준 속도 U | 무엇인가 | T_ft = 8.0 m ÷ U | 300 s 는 | 600 s 는 |
|---|---|---|---|---|
| 3.18 m/s | 팬 토출 | 2.52 s | **119 배** | **238 배** |
| 1.84 m/s | 이전 실행의 최대 \|U\|(에어컨 취출 BC) | 4.35 s | **69 배** | **138 배** |
| 0.50 m/s | 캐노피 목표 풍속 | 16.0 s | **18.8 배** | **37.5 배** |
| 0.152 m/s | 1 번 케이스 캐노피 P50 실측 | 52.6 s | **5.7 배** | **11.4 배** |

가장 보수적인 마지막 줄로도 600 s = 11.4 T_ft 로 Gousseau 의 평균 구간(21.8)에 못 미치고,
가장 관대한 첫 줄이면 238 배로 넘친다. **이 환산으로는 판정이 나오지 않는다.**
LES 관행을 우리에게 옮기는 것은 무리다 — 그쪽은 외부 풍속이라는 명백한 단일 기준 속도가 있고
우리는 없다. **인정하고 다른 근거를 쓰는 것이 정직하다.**

### 4-2. 팬을 유량에 더하는 것은 틀렸다

질문에 "팬 4대 24 CMM 추가 → 합 49 CMM → 교환 118 초"라고 적혀 있다.
**교환(air change)의 의미로는 틀렸다.** 팬은 `vectorSemiImplicitSource` 로 방 안에 놓인 내부
운동량 소스이고 **입구도 출구도 없다.** 방에 공기를 넣지도 빼지도 않는다.
그러므로 팬이 몇 대 돌든 **τ_n = V/Q_AC = 232 s 는 변하지 않는다.**

118 초라는 숫자가 무의미한 것은 아니다. **내부 순환 회전 시간**이고, "방 공기가 한 번 뒤섞이는 데
걸리는 시간"의 거친 척도다. 팬은 **교환 속도를 바꾸지 않고 혼합의 균일성을 바꾼다.**

| 이름 | 계산 | 값 | 무엇을 뜻하나 |
|---|---|---|---|
| **교환 시간** τ_n | V / Q_에어컨 | **232 s** | 스칼라(온도)가 갈리는 시계. 팬과 무관 |
| **내부 회전 시간** | V / (Q_에어컨 + Q_팬) | **118 s** | 섞이는 속도의 척도. 교환이 아니다 |

Colombari 외(2024)의 ACR 정의 `ACR = V̇/(V·h)` 도 **유입 유량**(hourly inlet flow rate)이지
내부 순환팬 유량이 아니다. 그들의 우사에서도 HVLS 팬과 순환팬은 ACR 에 들어가지 않는다.
우리도 같은 규칙을 지켜야 그 논문의 배수를 옮겨 쓸 수 있다.

### 4-3. 이 방의 시상수는 이미 측정돼 있다

문헌보다 강한 증거가 우리 저장소 안에 있다. `docs/OBJECTIVES.md` 9절,
이전 리허설의 900 초 실행을 역산한 결과다(`src/room_model.py`).

```
CFD 곡선   T(t) = 23.44 + 5.43 exp(-t/232)   RMS 0.018 K
tau = 232초 = V/Q (0.2% 이내)
```

**우리 방의 열 시상수가 V/Q 와 0.2 % 이내로 같다는 것을 우리가 직접 쟀다.**

같은 문서에 붙은 단서도 그대로 옮긴다. **이 방은 완전혼합이 아니다** — 벽 부하가 방 평균온도에
거의 반응하지 않고, 반원 안쪽(0.075 m/s)과 평벽 쪽(0.138 m/s)의 흐름이 다르다.
단일 시상수는 **방 평균 온도**에는 잘 맞지만 국소 값에는 그대로 적용되지 않는다.

### 4-4. 필요한 시간은 "무엇을 얼마나 엄하게 주장하느냐"로 정해진다

1차 지연계에서 허용오차 tol 까지 가는 시간은 **t = −τ·ln(tol)** 이다. τ = 232.1 s 를 넣으면
이렇게 된다(**우리 환산**). 오른쪽 두 칸은 그 허용오차를 실제로 쓴 문헌이다.

| 온도 허용오차 | t/τ | 필요한 물리 시간 | 그 기준을 쓴 문헌 |
|---|---|---|---|
| 10 % | 2.30 | **534 s** | — |
| **7.5 %** | **2.59** | **600 s (지금 이 값)** | — |
| 5 % | 3.00 | **695 s** | 격자 쪽 GCI 합격선과 같은 수준 |
| 1 % | 4.61 | **1,069 s** | Chen & Srebric 의 에너지 잔차 기준 |
| 0.5 % | 5.30 | **1,229 s** | van Hooff 외 2017 의 이동평균 기준 |
| 0.1 % | 6.91 | **1,603 s** | **Colombari 외 2024 의 감시 변수 기준** |

Colombari 외(2024)가 실제로 관측한 배수(10.8 ~ 20.2 회)를 그대로 옮기면 더 커진다.

| | 배수 | 우리 방(τ = 232 s)에 옮기면 |
|---|---|---|
| Colombari 겨울 | 10.8 τ | **2,507 s** |
| Colombari 여름 | 20.2 τ | **4,688 s** |
| Yao & Yao 평균 구간 | 37.9 τ | **8,796 s** |

**순수 1차 지연 산수(6.9 τ)보다 실제 관측(10.8~20.2 τ)이 크다.** 방이 단일 1차 지연계가 아니고
벽·바닥의 열용량과 국소 순환이 더 느린 항을 보태기 때문이다. 우리 방에도 같은 효과가 있다 —
4-3 의 단서("완전혼합이 아니다")가 그 징후다.

**곧 온도를 진지하게 주장하려면 600 초로는 모자라고, 1,000 ~ 2,500 초가 필요하다.**

### 4-5. Janke 외(2020)의 처방을 우리 방에 넣어 보면

3-1 의 네 단계를 그대로 계산한다(**전부 우리 환산**).

**2~3 단계 — 평균 구간.** 우리 관심 영역은 캐노피 판정면이고 폭이 **2.4 m** 다
(`FAN-CFD-METHOD.md` 6절, 단마다 2.4 × 0.8 m). 그 안의 속도는 케이스마다 다르다.

| 판정면 안 속도 | 무엇인가 | 2.4 m 통과 시간 | Janke 의 18 회 = 평균 구간 |
|---|---|---|---|
| 0.152 m/s | 1 번 케이스(팬 없음) 캐노피 P50 실측 | 15.8 s | **284 s** |
| 0.30 m/s | 우리 적정구간 하한 | 8.0 s | 144 s |
| 0.50 m/s | 캐노피 목표 풍속 | 4.8 s | 86 s |

**가장 보수적인 값이 284 초다.** 우리가 실측으로 얻은 "300 초부터 P10 이 0.4 % 안에서 머문다"와
거의 같은 수다. **서로 다른 두 경로가 같은 자리를 가리킨다.**

**1 단계 — 발달 구간은 옮기면 안 된다.** Janke 의 방식대로 하면 방 장축 8.0 m ÷ 에어컨 취출
1.84 m/s = 4.3 초, 곧 **5 초면 발달이 끝난다**는 계산이 나온다. **이것은 우리 케이스에서 틀렸다.**
우리 실측이 150 초에서 300 초 사이에 P10 이 15 % 움직인다고 말하고 있다. 이유는 분명하다 —
Janke 는 등온이고 우리는 부력이 섞여 있어서, 유동은 몇 초면 자리 잡아도 **온도장이 τ_n = 232 초로
끌고 가고 그것이 다시 부력을 통해 유동을 바꾼다.** 발달 구간은 **유동 시계가 아니라 열 시계**를
따른다. 우리 실측값 **300 초**를 쓰는 것이 맞다.

**합치면 이렇게 된다.**

| 구간 | 길이 | 근거 |
|---|---|---|
| 발달(버릴 것) | **0 ~ 300 s** | 우리 실측(150 s 에서 P10 이 아직 15 % 움직인다). 열 시계 1.29 τ_n |
| 평균(쓸 것) | **300 ~ 600 s** | Janke 처방 18 회 통과 = 284 s. 우리 30 초 간격 저장으로 11 장 |
| **합계** | **600 s** | **지금 돌리고 있는 값과 정확히 같다** |

**곧 600 초라는 숫자 자체는 맞다. 틀린 것은 그 600 초를 쓰는 방법이다.**
지금은 600 초를 전부 발달 구간으로 쓰고 마지막 한 장을 읽는다. 문헌이 말하는 구성은
**300 초 발달 + 300 초 평균**이다. 비용은 똑같다.

### 4-6. 그런데 우리는 온도를 주장하지 않는다

`FAN-CFD-METHOD.md` 6절이 온도를 순위에서 명시적으로 뺐다 —
"온도 분포로 판정할 근거가 없다. 조명이 들어오면 같은 파일로 지표를 붙이면 된다."

속도의 시계는 훨씬 빠르다. **우리 실측**(5번 케이스, F3 6.0 CMM):

| 비교 | 캐노피 P10 차이 | 평균 차이 |
|---|---|---|
| **300 s ↔ 600 s** | **0.4 %** | 1.9 % |
| 150 s ↔ 300 s | P10 0.084 → 0.071 (**−15 %**) | — |

**0.4 % 는 van Hooff 외(2017)의 0.5 % 기준 안에 있다.** 조사 범위에서 가장 엄한 공표 기준을
이미 통과한다. 150 초는 통과하지 못한다.

방향이 문헌과 맞는다.
- NASA/AIAA LES 권장 관행: "mean values of primitive variables such as u, v … converge quite
  rapidly whereas mean values of fluctuating quantities … converge less rapidly"
- Colimba-Limaico 외(2026): "The characteristic flow timescale (1–10 s) is significantly shorter
  than the thermal response time of the crop canopy"

운동량은 소스(팬 추력·에어컨 취출 운동량)가 직접 넣어 주므로 몇 회전이면 자리 잡고,
온도는 방 전체 공기를 갈아 끼워야 하므로 τ_n 을 따른다.

**주의 하나.** `docs/OBJECTIVES.md` 프레임 표에서 최대 |U| 가 60 초부터 1.84 m/s 로 고정된 것은
**속도장이 자리 잡았다는 증거가 아니다.** 그 문서 자신이 "취출구 경계조건이니 당연하다"고
적어 두었다. 경계조건이 걸렸다는 점검 지표일 뿐이다.
속도장 정착의 증거는 위의 300 ↔ 600 초 P10 비교 하나다.

### 4-7. 판정

| 질문 | 답 |
|---|---|
| **600 초 = 2.6 회 교환**이 맞는가 | 맞다. τ_n = 232 s 는 우리가 실측으로 확인했다 |
| **팬 포함 49 CMM → 118 초**가 맞는가 | **교환 시간으로는 틀렸다.** 팬은 내부 순환이라 교환에 기여하지 않는다. 혼합 회전 시간으로는 맞다 |
| **몇 회가 필요한가**를 문헌이 정해 주는가 | **규정은 없다.** 관측 선례는 1.65 회에서 93 회까지 흩어져 있고(2-3), 흩어짐의 원인은 판정 대상과 허용오차의 차이다 |
| **300 초로 줄여도 되는가** | **마지막 한 장으로 계속 읽을 것이라면 된다.** P10 차이 0.4 % 가 van Hooff 의 0.5 % 안이다(**150 초는 안 된다**, −15 %). **그러나 300 초로 줄이면 평균할 구간이 사라진다.** Janke 처방이 요구하는 평균 구간이 284 초다 |
| **600 초도 부족한가** | **온도를 순위에 넣는 순간 부족하다.** 600 초는 온도 오차 7.5 % 자리다. 1 % 면 1,069 초, Colombari 기준이면 1,603 초, 그들의 관측 배수면 2,500 초 이상 |
| **그럼 600 초는 맞는 값인가** | **길이는 맞다. 쓰는 방법이 틀렸다.** 300 초 발달 + 300 초 평균이면 우리 실측과 Janke 처방이 둘 다 충족된다(4-5). 지금은 600 초 전부를 발달로 쓰고 한 장만 읽는다 |
| 더 큰 위험은 | 시간이 아니라 **마지막 한 장으로 읽는 것**이다(5절) |

---

## 5. 부력·저주파 진동 — 마지막 한 장이 위험한 이유

### 5-1. 부력이 섞인 실내 흐름은 정상에 도달하지 않는다

**Yao, J.; Yao, Y. (2022)** 「Unsteady Flow Oscillations in a 3-D Ventilated Model Room with
Convective Heat Transfer」 *Fluids* 7(6):192, doi 10.3390/fluids7060192 (오픈액세스, 원문 확인).
**조사 범위에서 우리 상황에 가장 가까운 논문이다** — 2.44 m 정육면체 방, 천장 슬롯 급기,
중앙에 700 W 가열 상자, URANS, k-ε 계열.

> "Based on the thermophysical condition of the model room and the heated box, it is estimated that
> **Gr/Re² ≪ 1 and Re_inlet > 2000** … Hence, **the heat transfer due to the forced convection mode
> will play a major role** …"

> "Double precisions are always defined to have better numerical accuracy, and **the residual target
> is set as 10⁻¹² to achieve a high level of convergence.**"

**강제대류가 지배하고 잔차를 10⁻¹² 까지 떨어뜨렸는데도 흐름은 멈추지 않았다.**

> "**It can be seen that there is no particular trend or similarity in fluctuation variations among
> these three cases and the amplitude of the spikes is generally asymmetric.** The fluctuation
> variation in case 1 seems smaller, e.g., in a range of **0.025–0.075 m/s**, compared to that of
> case 2 and case 3, for which the range of the velocity fluctuation is relatively larger, i.e.,
> **0.01–0.15 m/s.**"

> "Based on the prescribed time step and an inlet velocity 1.378 m/s, **this time period of the
> simulation is equivalent to 10–70 complete flow recirculation cycles.**"

**이 숫자가 우리에게 직접 온다.** 한 감시점의 순간 풍속이 **0.01 ~ 0.15 m/s** 사이를 오간다.
우리 판정 지표 P10 이 **0.059 ~ 0.084 m/s** 대다(`FAN-CFD-METHOD.md` 6절 1번 케이스).
**진동 폭이 판정하려는 값과 같은 크기다.**

그리고 저자들이 한 일이 결정적이다.

> "**After the initial transient stage, the time-averaged 'mean' results are then calculated based on
> a total of 20 successive datasets, each averaging over 5000 time steps during the calculation.**"

**환산**: 20 × 5,000 × 0.055 s = **5,500 초를 시간평균**했다. 그 방의 교환 시간이 145 초이므로
**교환 38 회분을 평균한 것**이다. 마지막 한 장을 쓰지 않았다.

### 5-2. 느린 순환은 자리 잡는 데 오래 걸린다 — 실측 증거

**Markov 외 (2020)** 『Applied Sciences』 10(15):5036, doi 10.3390/app10155036 (원문 확인).
CFD 가 아니라 **실제 강의실의 실측**이다. 이것이 더 강한 증거다.

> "The temperature records at all heights can be divided into 2 phases: the transient period and the
> quasi-steady-state period. **The transient phase takes about 1000 s; the air temperature at the
> inspected locations drops from 32.44 ± 0.1 °C to 25.16 ± 0.2 °C.** … Therefore, **the assessment
> of Tu and DR at the inspected locations was done for the temperature quasi-steady-state phase
> only, i.e., for the period starting from the instant of 1020 s.**"

실물 강의실을 팬코일로 냉방해 7.3 K 를 내리는 데 **1,000 초**가 걸렸고, 저자들은 그 앞 구간을
**분석에서 통째로 뺐다.** 우리 방이 5.4 K 를 내리는 데 τ = 232 초이니 시계는 같은 자릿수다.

**Chen, C.; Gorlé, C. (2022)** 『Building and Environment』 221:109240,
doi 10.1016/j.buildenv.2022.109240 (arXiv:2203.05670 저자 원고 전문 확인).

> "**A small time step is used at the beginning of the simulation to capture the fast initial
> transient** … **the optimal time steps are 0.5 s, 1.0 s, 2.0 s, and 5.0 s for 0 to 5 mins,
> 5 to 15 mins, 15 to 30 mins, and 30 to 60 mins, respectively. For the remaining two hours of the
> simulation, the time step is set to 10 s when a quasi-steady state is achieved.**"

**준정상 도달이 약 60 분.** 다만 이 건물은 3 층 아트리움 실물 규모이고 구동력이 부력뿐이다.
우리 방은 96.7 m³ 에 팬 4 대와 25 CMM 취출이 있어 훨씬 강제대류 쪽이다. **그대로 옮기면 안 된다.**

오차의 공간 분포도 진동을 따라간다.

> "In the hallway and atrium zones … **the maximum discrepancy … is very small at 0.15 °C.** On the
> other hand, considering the zones adjacent to the windows … **the maximum discrepancies are
> higher, up to 0.70 °C.**"
> "**the inflow of cold outdoor air through the windows is an unsteady process with significant
> oscillations in the inflow direction.**"

**진동하는 제트가 지배하는 구역의 오차가 4.7 배였다.** 우리 팬 제트가 같은 성격이다.

**Jiang & Chen (2003)** 도 같은 관찰을 실험 쪽에서 적었다 —
"**In the measurements, it took a long time to obtain the steady flow conditions.**"

### 5-3. 같은 조건에서 해가 둘일 수 있다 (flow bistability)

**Heiselberg, P.; Li, Y.; Andersen, A.; Bjerre, M.; Chen, Z. (2004)** 「Experimental and CFD
evidence of multiple solutions in a naturally ventilated building」 *Indoor Air* 14(1):43–54,
doi 10.1046/j.1600-0668.2003.00209.x. **초록만 확인**(Wiley 접근 불가, Europe PMC 초록).

> "Results from all three methods have shown that **the hysteresis phenomena exist. Under certain
> conditions, two different stable steady-state solutions are found to exist by all three methods for
> the same set of parameters.** … **one of the solutions can shift to another when there is a
> sufficient perturbation.** … **Different initial conditions in the CFD simulations led to different
> solutions, suggesting that caution must be taken when adopting the commonly used 'zero
> initialization'.**"

마지막 문장이 우리를 직접 가리킨다. 우리는 정지 상태에서 출발한다.

**Hunt, G.R.; Linden, P.F. (2005)** 「Displacement and mixing ventilation driven by opposing wind
and buoyancy」 *Journal of Fluid Mechanics* 527:27–55, doi 10.1017/S0022112004002575.
**초록만 확인.**

> "**One of two stable steady flow regimes is established depending on a dimensionless parameter F**
> … **and on the time history of the flow. A third, unstable steady flow solution is identified.**"
> "**The transitions between the two ventilation flow patterns exhibit hysteresis.**"

**주의.** 이 두 편은 **자연환기**(바람 대 부력)다. 우리는 기계 취출과 내부 팬이 구동한다.
구조적 유비는 성립하지만(차가운 취출 제트가 부력과 겨룬다) **그대로 인용하면 과장이다.**
우리 케이스에서 실제로 쌍안정이 나는지는 확인되지 않았고, 확인하려면 초기장을 달리해
같은 케이스를 두 번 돌려 봐야 한다.

**Le Quéré, P.; Behnia, M. (1998)** *JFM* 359:81–107, doi 10.1017/S0022112097008458.
**초록만 확인.** 공기로 채운 밀폐 공동이 정상 → 비정상 → 혼돈으로 가는 고전 결과이고,
저자들이 보고하는 대상이 **시간평균 구조**(time-averaged structure)라는 점이 시사점이다.

**Ajmani 외 (2025)** *Fluids* 10(5):132(원문 확인) — 대칭 강의실에서 저주파 비대칭이 남는다.

> "**the flow field was found to be quasi-steady, with low frequent limited amplitude flow
> asymmetries along the centerline of the symmetric lecture hall.**"

기하와 열이 대칭인 방에서도 저주파로 좌우가 흔들린다. **한 장을 찍으면 그 순간의 쏠림이
설계의 성질인 것처럼 보인다.**

### 5-4. 그래서 시간평균을 써야 하는가 — 문헌이 직접 답한다

**Blocken, B. (2015)** *Building and Environment* 91:219–245, §5.6 (원문 확인).

> "When flow problems that are inherently transient are forced into a steady simulation, and when
> numerical diffusion is limited, it is possible that oscillatory convergence occurs. … **This is not
> an indication of a lower-quality simulation. On the contrary, it indicates that the grid resolution
> is high enough and numerical diffusion is low enough for non-linear effects to influence the
> convergence process.**"

> "A detailed comparison by Ramponi and Blocken of such CFD results with the high-quality Particle
> Image Velocimetry (PIV) measurements by Karava et al. indicated that **accurate results could only
> be obtained by averaging the CFD results over at least a period of oscillatory behavior.**"

> "**The advice is to first allow convergence to continue until residuals do not change any more or
> enter into oscillatory convergence. In the latter case, the iterative process should be continued
> and solutions at different stages in this second stage of the iterative process should be stored
> and averaged to yield the final averaged solution.**"

**Ramponi, R.; Blocken, B. (2012)** *Building and Environment* 53:34–48 (원문 확인)이 실행 사례다.

> "**this apparently minor oscillatory convergence can actually be the result of very strong local
> oscillatory behavior in the flow field, because the scaled residuals provide an overall value
> averaged over all cells in the computational domain.**"
> "Therefore, in this paper, **the oscillatory behavior of the results was monitored over 10000
> iterations and the calculated variables were averaged when necessary.**"
> "**This means that special care should be applied when extracting results from steady RANS results
> of intrinsically unsteady flow phenomena.**"

한 가지 함정도 같이 적혀 있다.

> "The wind speed ratio in point 2 however **shows significant oscillations which however decrease
> with increasing inlet turbulent kinetic energy.** … **The effect of turbulent kinetic energy is
> increased mixing of momentum, which also smoothens out the instabilities.**"

**난류 입력을 올리면 진동이 사라진다.** 곧 "조용해 보이는 결과"가 흐름이 자리 잡은 증거가 아니라
확산이 과한 설정의 증상일 수 있다. 우리가 표준 k-ε 을 쓰고 있다는 점이 여기에 걸린다 —
이 계열에서 가장 확산적인 모델이다.

**정리.** 우리가 **마지막 시각 한 장으로 판정하는 것은 문헌이 명시적으로 피하라고 한 방식**이다.
`src/judge.py` 는 `latest_dir(run)` 으로 마지막 시간 디렉터리 하나만 읽는다. 그게 현재 규격이다.

---

## 6. 권고 — 결정은 사람이 한다

세 축이 독립이다. **(가) 물리 시간을 얼마로 할 것인가, (나) 마지막 한 장이냐 시간평균이냐,
(다) 무엇을 주장할 것인가.** 문헌이 가장 강하게 말하는 것은 (나)이고, 그것이 가장 싸다.

### 권고 1 — 시간평균을 먼저 해 본다. 계산 비용 0.

**이것을 가장 먼저 권한다.**

`controlDict` 이 `purgeWrite 0` 이고 30 초마다 전 필드를 쓴다. 600 초 실행이면
**판정면 스냅샷이 이미 21 장 디스크에 있다.** `src/judge.py` 가 마지막 한 장만 읽고 있을 뿐이다.

- **할 일**: `judge.py` 에 `--average-from 300` 같은 선택지를 붙여, 300~600 초의 11 장을
  **점별로 평균한 필드**에서 분위수를 낸다. 계산은 한 번도 다시 돌리지 않는다.
- **무엇을 알게 되나**: 시간평균 P10 과 마지막 한 장 P10 의 차이가 나온다.
  그 차이가 **300 초 ↔ 600 초 차이(0.4 %)보다 크면, 문제는 물리 시간이 아니라 스냅샷 잡음이다.**
  그러면 물리 시간을 늘리는 것은 돈만 쓰고 답을 못 준다.
- **근거**: Blocken(2015) "solutions at different stages … should be stored and averaged";
  Ramponi & Blocken(2012) "averaged when necessary"; Yao & Yao(2022)가 실제로 한 일;
  **Janke 외(2020)의 "관심 영역 18 회 통과 = 우리 방에서 284 초"**(4-5).
- **바로 이어서 할 것**: 평균 구간을 [300,600] 과 [450,600] 으로 나눠 재평균해 P10 이
  안 바뀌는지 본다. Janke 외(2020)가 [1,6] 대 [2,7] 로 한 사후 검증이고, 비용은 역시 0 이다.
- **단서 둘.**
  1. 30 초 간격 11 장은 **참 시간평균이 아니라 11 점 표본평균**이다. Yao & Yao 가 보고한
     0.4 Hz 진동(주기 2.5 초)은 이 간격으로는 앨리어싱된다. 표본이 서로 독립이라면 표준오차가
     √11 ≈ 3.3 배 줄어든다는 정도로만 읽어야 한다.
  2. **두 가지 평균을 구분해야 한다.** (a) 필드를 먼저 시간평균하고 그 필드의 분위수를 내는 것 —
     문헌이 말하는 시간평균이고 "지속적인 공간 패턴"을 잰다. (b) 모든 시각의 점을 한데 모아
     분위수를 내는 것 — "어느 자리가 얼마나 자주 정체하는가"를 재는 다른 질문이다.
     둘 다 말이 되지만 **섞으면 안 되고, 어느 쪽인지 본문에 적어야 한다.** 기본은 (a)를 권한다.

### 권고 2 — 참 시간평균은 `fieldAverage` 로. 다음 재실행부터.

OpenFOAM 공식 function object 가 이미 있다.
`Foam::functionObjects::fieldAverage`
(https://api.openfoam.com/2306/classFoam_1_1functionObjects_1_1fieldAverage.html)

> "Computes ensemble- and/or time-based field averages, with optional windowing, for a user-specified
> selection of volumetric and/or surface fields."

`base time`, `window`, `restartTime` 을 받고 `UMean` 을 만든다. **모든 시간 스텝에 걸친 참 평균**
이라 30 초 표본의 한계가 사라지고 저장 용량도 늘지 않는다. `sample` 이 `UMean` 을 판정면에
찍게 하면 채점 경로는 그대로다. 평균 시작 시각은 과도를 버린 뒤로 잡는다 — **300 초를 권한다**
(우리 실측상 150 초는 아직 출렁이고 300 초부터 P10 이 0.4 % 안에서 머문다).

### 권고 3 — 물리 시간

| 선택지 | 구성 | 케이스당 | 30 케이스 | 근거 | 대가 |
|---|---|---|---|---|---|
| **A. 600 초 유지 + 300~600 초 시간평균** | 300 s 발달 + **300 s 평균** | **5.6 h**(지금과 같다) | **7 일**(지금과 같다) | **우리 실측과 Janke 외(2020) 처방이 둘 다 충족된다**(4-5). 발달 300 s 는 우리 실측(150 s 에서 아직 15 % 움직임), 평균 300 s 는 Janke 의 18 회 통과(284 s) | **없다.** 계산 비용이 지금과 똑같다. 채점 방식만 바뀐다 |
| **B. 300 초로 줄인다 + 마지막 한 장** | 300 s 전부 발달 | 2.8 h | **3.5 일** | 우리 실측 P10 차이 0.4 % 가 van Hooff 외(2017)의 **0.5 %** 기준 안 | **평균할 구간이 없다.** 5절이 말하는 스냅샷 위험을 그대로 안는다. 온도 27.5 % 미완 |
| **C. 450 초** | 300 s 발달 + 150 s 평균 | 4.2 h | 5.25 일 | 발달은 실측대로, 평균은 절반 | 평균 구간이 **9.5 회 통과**로 Janke 의 18 회에 못 미친다. 저장 스냅샷도 6 장뿐 |
| **D. 1,200 초 이상** | 300 s 발달 + 900 s 평균 | 11.4 h | 14 일 | 온도 0.5 % 까지(4-4). 평균 구간 57 회 통과 | 지금 규격(속도만 판정)에서는 **속도 쪽으로 얻는 것이 거의 없다** |

**A 를 권한다.** 이유는 셋이다.

1. **비용이 0 이다.** 지금 돌리는 시간과 똑같고, `judge.py` 가 읽는 시각만 바뀐다.
   권고 1 이 그 구현이다.
2. **서로 다른 두 경로가 같은 자리를 가리킨다.** 우리 실측("300 초부터 P10 이 0.4 % 안")과
   Janke 외(2020)의 처방(관심영역 18 회 통과 = 284 초)이 거의 같은 수를 내놓는다.
   문헌 근거와 자체 측정이 겹치는 자리는 드물다.
3. **문헌이 가장 강하게 말하는 것을 지키게 된다.** Blocken(2015)의 "저장해서 평균하라",
   Janke 외(2020)의 "구간을 옮겨 재평균해 확인하라", Yao & Yao(2022)가 실제로 한 일,
   van Hooff 외(2017)의 이동평균 0.5 % — 전부 **시간평균**을 전제한 기준이다.
   마지막 한 장으로는 이 기준들을 애초에 적용할 수 없다.

**B 는 시간이 급할 때의 차선이다.** `FAN-CFD-METHOD.md` 8절의 스크리닝 단계(풍량 곡선 잡기)는
상대 순위만 보므로 300 초로 줄여도 된다. 그때는 **"스냅샷 판정이고 평균하지 않았다"를
본문에 명시**해야 한다. 최종 단계는 A 로 간다.

**D 는 지금 권하지 않는다.** 다만 `FAN-CFD-METHOD.md` 10절의 교체 지점(조명·증산·모터 발열이
들어와 온도가 순위에 올라가는 시점)에서는 **발달 구간부터 1,000 ~ 2,500 초가 필요해진다**
(4-4 표). 그때 다시 봐야 한다.

**어느 쪽이든 Janke 의 4 단계 사후 검증은 해야 한다** — 평균 구간을 [300, 600] 과
[450, 600](또는 다음 실행에서 [300, 450] 대 [450, 600])으로 나눠 재평균하고
P10 이 안 바뀌는지 본다. 이것도 계산 비용 0 이다.

### 권고 4 — 어느 쪽을 고르든 본문에 적어야 할 것

Chen & Srebric(2002)이 보고 항목으로 요구하는 것 가운데 우리가 아직 안 적은 것들이다.

- **물리 시간, Δt(적응이면 실측 평균과 범위), 총 시간 스텝 수.** 지금은 START-HERE 3절에
  "물리 시간 600 초"만 있고 Δt 실측이 없다.
- **준정상 판정의 근거.** COST 732 식으로 쓰면 이렇게 된다 —
  "캐노피 판정면 P10 의 이동평균이 마지막 N 초 동안 X % 안에 머물렀다."
  van Hooff 외(2017)의 **0.5 %** 를 기준으로 쓰고, 우리 300↔600 차이 0.4 % 가 그 안에 있다고
  적으면 문헌 근거가 붙은 문장이 된다.
- **무엇을 주장하지 않는지.** 온도를 순위에 쓰지 않는다는 것, 그리고 300 초를 쓴다면
  온도 분포를 보고하지 않는다는 것.
- **감시점을 어디에 두었는지.** RP-1133 은 저속 코어가 아니라 고속 영역에 두라고 한다.
  우리 판정면은 저속 코어다.

### 권고 5 — 싸고 답을 많이 주는 추가 작업 하나

대표 케이스 하나에 **감시점 시계열**을 붙인다. `probes` function object 로 팬 하류·캐노피 중앙·
방 중앙·벽 근처에 속도와 온도를 **매 시간 스텝** 기록한다. 저장량은 무시할 만하다.

그러면 네 가지가 한 번에 나온다.
1. **과도가 언제 끝나는가** — 이동평균이 평평해지는 시각. 평균 시작 시각을 여기서 정한다
   (Markov 외 2020 이 실측으로 한 일).
2. **가장 느린 진동 주기** — FFT. 평균 구간의 하한이 여기서 나온다(Yao & Yao 2022 가 한 일).
3. **진동 폭** — 지금 스냅샷 판정에 섞인 잡음의 크기.
4. **Gousseau 외(2013)의 e_conv** — 격자 쪽 GCI 와 나란히 놓을 수 있는 **시간 쪽 수렴 지표**.
   이 문헌군에서 그것까지 한 농업 CFD 논문은 확인한 범위에 없다.

---

## 7. 찾지 못한 것 / 열린 질문

### 7-1. 원문을 구하지 못한 것

| 문헌 | 왜 필요한가 | 상태 |
|---|---|---|
| **Villagrán, E.A.; Baeza Romero, E.J.; Bojacá, C.R. (2019)** 「Transient CFD analysis of the natural ventilation of three types of greenhouses used for agricultural production in a tropical mountain climate」 *Biosystems Engineering* 188:288–304 · doi 10.1016/j.biosystemseng.2019.10.026 | **제목부터 이번 조사의 정중앙.** 온실 과도해석의 대표 논문 | **못 구했다.** Unpaywall 은 WUR 랜딩 페이지만 가리키고 파일이 없다. Elsevier 403. **가장 아쉽다** |
| **Nielsen, P.V.; Allard, F.; Awbi, H.B.; Davidson, L.; Schälin, A. (2007)** REHVA Guidebook No.10 「Computational Fluid Dynamics in Ventilation Design」 | 실내 환기 CFD 의 유럽 표준 지침. 과도 규정이 있다면 여기다 | **못 구했다.** Aalborg VBN(403)·HAL(차단)·CERN CDS·Reading Centaur 모두 전문 비공개. 서평만 유료(doi 10.1080/14733315.2007.11683784). **인용하지 않는다** |
| **Nielsen, P.V. (2015)** 「Fifty years of CFD for room air distribution」 *Building and Environment* 91:78–90 · doi 10.1016/j.buildenv.2015.02.035 | 실내 기류 불안정성에 대한 Nielsen 본인의 서술 | **유료. 초록도 못 구함** |
| **Pulat, E.; Erşan, H.A. (2015)** 「Numerical simulation of turbulent airflow in a ventilated room: Inlet turbulence parameters and solution multiplicity」 *Energy and Buildings* 93:227–235 · doi 10.1016/j.enbuild.2015.01.067 | **IEA Annex 20 표준 시험실의 해 다중성** — 우리 구성에 가장 가까운 쌍안정 결과 | **유료.** Unpaywall·Crossref·OpenAlex·Semantic Scholar 어디에도 초록이 없고 Wayback 스냅샷도 없다. **제목 외에는 아무것도 확인 못 했으므로 본문 근거로 쓰지 않았다** |
| **Bouhoun Ali, H. 외 (2022)** 「A CFD transient model of leaf wetness duration on greenhouse cucumber leaves」 *Comput. Electron. Agric.* 201:107257 | 온실 과도해석, 캐노피 | **유료** |
| **Baek 외 (2026)** 「CFD numerical setting combinations for greenhouse natural ventilation across diurnal time points」 *Comput. Electron. Agric.* 247:111689 | 온실 CFD 설정 조합 비교 | **유료** |
| **Piscia 외 (2014)** 「CFD simulations of the night-time condensation inside a closed glasshouse」 *Biosyst. Eng.* 127 | 야간 과도 온실 | **유료** |
| **Heiselberg 외 (2004)** Indoor Air 14(1):43–54 | 같은 조건에서 두 안정 해 | **초록만 확인**(Wiley 차단, Europe PMC 초록) |
| **Hunt & Linden (2005)** JFM 527:27–55 | 쌍안정과 이력현상 | **초록만 확인** |
| **Le Quéré & Behnia (1998)** JFM 359:81–107 | 밀폐 공동의 비정상 → 혼돈 | **초록만 확인** |
| **Zhao, F.-Y.; Liu, D.; Tang, G.-F. (2008)** Int. J. Heat Fluid Flow 29(5):1295–1308 · doi 10.1016/j.ijheatfluidflow.2008.06.005 | 슬롯 환기 공간의 다중 유동 패턴 | **초록만 확인.** 게다가 **등온** 케이스라 부력 근거로는 못 쓴다 |
| **Stavridou & Prinos (2017)** Procedia Environ. Sci. 38:322–330 | 우리와 같은 솔버 계열(과도 RANS + RNG k-ε)의 국소 열원 방 | **초록만 확인** |
| **ERCOFTAC Best Practice Guidelines** (Casey & Wintergerste 2000) | 비정상 해석의 유럽 공학 표준 | **유료. 확인 못 함** |
| **AIJ 지침 (Tominaga 외 2008)** 의 비정상·평균 시간 관련 서술 | 있는지 없는지 확인 필요 | 저자 원고는 `FAN-CFD-MESH-REFERENCES.md` 6-2 에서 확인했으나 **이번 조사에서 관련 문장을 못 찾았다.** 실외 보행자 풍환경용 정상 RANS 문서로 보인다 |
| **ASHRAE Handbook—Fundamentals Ch. 16 「Ventilation and Infiltration」** | 공칭 시상수 τ_n = V/Q 의 공식 정의 | **못 구했다.** 13장만 확보했다. 4절의 τ_n 은 우리 실측 회귀와 Colombari 외(2024)의 ACR 정의로 정당화했다 |
| **Markov 외 (2020)** 의 Table 1(CFD 시간 표본 길이) | CFD 쪽 모사 시간의 정확한 값 | PDF 텍스트 층에서 표가 깨져 있다. **출판본 표를 다시 봐야 한다.** 2-2 표에 "재확인 필요"로 표시했다 |
| **Janke 외 (2020)** 의 출판본(Comput. Electron. Agric. 175:105546) | 프리프린트와 대조 | **WIAS Preprint 2644 전문은 읽었다.** 다만 프리프린트 §2.1 에 "**T = 700 s**"라고 적혀 있고 §3 에는 "the simulation of the whole time interval of **7 seconds** required 28000 time steps"(28,000 × 2.5 × 10⁻⁴ s = 7 s)라고 적혀 있다. **내부 모순이다.** §2.7 의 유도(0.8 s 영역 통과, 1 s 발달, 6 s 평균)가 전부 7 초와 맞으므로 **700 s 는 오기로 본다.** 출판본으로 확인이 필요하다 |
| **Manbeck 외 (2016)** 의 축사 환기량 | 2-1 표의 수치 | **원문 확인했으나 내부 모순이 있다.** 본문에 "**226.0 m³/s**, is the design hot weather ventilation rate for 450 [pigs]" 와 "The total AC of the three barn ventilation fans is **26.0 m³/s**" 가 함께 적혀 있다. **226.0 은 오기로 보이나 확정하지 못했다.** 우리 환산에는 분뇨조(908 m³, 팬 4.5 m³/s)만 썼다 |

### 7-2. 문헌에서 답을 못 찾은 질문

1. **"몇 회 교환을 지나야 하는가"의 규정.** 지침에는 없다. 관측 보고는 하나 있다
   (Colombari 외 2024, 10.8~20.2 회, 감시 변수 10⁻³ 기준). **규정과 관측을 구분해서 써야 한다.**
2. **LES 의 flow-through 관행을 내부 구동 실내 공간으로 옮기는 법.** 그쪽은 외부 풍속이라는
   단일 기준 속도가 있고 우리는 없다. 기준 속도를 팬 토출로 잡느냐 실내 중앙값으로 잡느냐에 따라
   **20 배**가 갈린다(4-1 표). 이 환산을 정당화하는 문헌을 찾지 못했다.
3. **분위수 지표(P10)의 시간 수렴을 다룬 논문.** 없다. 문헌의 감시량은 거의 다 점 풍속·점 온도이고
   더러 면 평균이다. **분포의 꼬리(P10)가 평균보다 늦게 수렴하는지 빨리 수렴하는지 모른다.**
   NASA/AIAA 의 "평균은 빨리, 변동량은 늦게" 규칙에서 P10 이 어느 쪽인지는 추론일 뿐이다.
   `FAN-CFD-MESH-REFERENCES.md` 8-2 의 4번(균일도 지표의 격자 수렴)과 같은 성격의 공백이다.
4. **기계환기 + 내부 순환팬 조합에서 쌍안정이 보고된 사례.** 못 찾았다. 확인한 쌍안정 문헌은
   전부 **자연환기**(바람 대 부력)이거나 **등온 대향 제트**다. 우리 구성에 대한 직접 증거가 없다.
   확인하려면 같은 케이스를 초기장만 바꿔 두 번 돌려 보는 수밖에 없다.
5. **표준 k-ε 이 실제 진동을 지워 버리는 정도.** Ramponi & Blocken(2012)은 난류 운동에너지를
   올리면 진동이 잦아든다는 것을 보였다. 우리가 표준 k-ε 을 쓰므로 **지금 결과가 조용해 보이는
   것이 흐름이 자리 잡아서인지 모델이 확산적이어서인지 구분할 방법이 없다.**
   `FAN-CFD-METHOD.md` 5-2 가 확인용으로 둔 다른 두 모델로 같은 케이스를 돌려 진동 폭을
   비교하면 답이 나온다. 이번 조사 범위 밖이다.
6. **Kibwika 외(2023)의 과도 구간이 180 초인가 10 분인가.** 같은 문단에 두 값이 적혀 있다.
   저자에게 묻기 전에는 모른다. 인용할 때는 **둘 다 적는다.**
7. **실내 농업 CFD 에서 순간 스냅샷과 시간평균의 차이를 잰 논문.** 없다.
   온실·식물공장 문헌은 거의 다 정상해석이고, 과도인 것도 시간평균을 쓰지 않는다.
   **우리가 권고 1 을 실행해 이 숫자를 내면 이 문헌군에서 앞서는 부분이 된다.**
8. **식물공장·수직농장의 과도해석 선례.** Lee 외(2023) 하나뿐이다. MDPI 계열 12 편과 축사
   오픈액세스 약 160 편을 추가로 훑었지만 진짜 과도는 7 편이었다(2-1 판단 1). 곧 **우리가
   OpenFOAM 으로 농업 시설 과도해석을 한다는 것 자체가 이 문헌군에서 드문 일**이고
   (Janke 외 2020 도 같은 말을 적었다), 그만큼 참고할 관행도 없다.
9. **Oh 외(2023)가 300 초 감쇠 곡선을 보고하면서 Δt 를 어디에도 적지 않았다.** 같은 연구실
   (전북대)의 Kibwika 외(2023)는 1 초라고 적었으니 같은 값일 가능성이 있지만, **추정이므로
   쓰지 않았다.** 한국 농업 CFD 에서 시간 관련 보고가 느슨한 것은 일반적인 듯하다.
10. **"발달 구간"과 "평균 구간"을 나눠 보고한 농업 논문.** Janke 외(2020) 하나뿐이다.
    나머지는 총 물리 시간만 적고, 그 안에서 어디부터 결과로 썼는지 밝히지 않는다.
    **우리가 4-5 의 구성(300 s 발달 + 300 s 평균)을 명시하면 이 문헌군에서 앞서는 부분이 된다.**
