# SmartFarm CFD → Unreal 리허설 — 이어가기 핸드오프 (새 PC용)

> 목적: 이 문서 하나 + 이 repo만 새 PC에 옮기면 중단 없이 이어갈 수 있게.
> 최종 목표: **언리얼에서 기류를 온도색으로 렌더**(기류는 측정이 비싸 CFD로 대체 / 온도는 싼 센서로 검증). 진짜 CFD 데이터가 오기 전, **같은 형식의 가짜 5분 냉각 데이터로 UE 파이프를 리허설**한다.

작성일 2026-09-03. 브랜치 `feat/mock-generator`.

---

## 0. 한 줄 상태
가짜 5분 냉각 CSV 생성기는 **완성**. UE 반입은 **프레임 1장을 뷰포트에 점으로 띄우는 스크립트까지 작성**, 실제 실행/눈검증은 **아직 안 끝남**. 다음은 실행 확인 → 15프레임 애니메이션 → 진짜 데이터 교체.

---

## 1. 지금까지 한 것 (DONE)
- **가짜 CFD 생성기** (`src/`): 반원 800×570×270cm 공간에 시간별 온도·기류를 계산식으로 채워 **15프레임 CSV** 생성. TDD 11 테스트 통과.
- **산출물**: `data/frames/frame_00~14.csv` (프레임당 ~96,714점). 스키마 = **진짜 CFD export와 동일**:
  `x,y,z(m), T(K), Ux,Uy,Uz(m/s), p(Pa), source`
  - frame_00 = 29℃ 균일·바람0(시작) → frame_14 = 에어컨 아래 20℃·|U|max 0.78(280s).
- **눈검증 PNG**: `data/preview/slice_z_frame_*.png` (반원·냉각·기류 확인됨).
- **UE 테스트 자산** (`ue/`): `SF_Rehearsal.uproject`(UE5.7, Blueprint-only) + `sf_viz.py`(프레임 1장을 뷰포트에 온도색 점+기류선으로 draw).

---

## 2. 새 PC 준비물 (Prerequisites)
- **Python 3.11** + `numpy pandas matplotlib pytest` (이 repo는 `py` 런처 전제 — `python`이 깨진 머신 기준. 정상 머신이면 `python`도 OK).
- **Unreal Engine 5.7** + 플러그인: **Niagara**, **PythonScriptPlugin**(필수). 선택: UnrealClaude, NarshaMCP(자동화용).
- 이 repo 전체 복사/클론.

---

## 3. ⚠️ 새 PC에서 바꿔야 할 절대경로
- `ue/sf_viz.py`의 `CSV_PATH` → 새 PC의 `data/frames/frame_XX.csv` 절대경로.
- `.uproject`는 어디 두든 상관없음(엔진이 5.7이면). `EngineAssociation`이 안 맞으면 우클릭 "Switch Engine Version" 또는 5.7의 `UnrealEditor.exe`로 직접 열기.
- **`geometry.json`·`src/`·generate/preview는 전부 상대경로** → repo 안에서 그대로 돌아감(경로 수정 불필요).

---

## 4. 데이터 재생성 (repo 루트에서)
```bash
py -m pip install numpy pandas matplotlib pytest
py -m pytest -q                 # 11 passed 확인
py -m src.models.generate_frames       # data/frames/ 에 15프레임 CSV + manifest
py -m src.pipeline.preview               # data/preview/ 에 단면 PNG
```
모든 파라미터(치수·에어컨 위치·온도·τ·격자·프레임수·컬러맵)는 **`geometry.json` 한 곳**. 값만 바꾸면 코드 안 고치고 시나리오 변경.

---

## 5. UE로 가져오기 (현재 방식 = 디버그 점)
1. `ue/SF_Rehearsal.uproject`를 UE 5.7로 열기 (PythonScriptPlugin 켜져 있어야 함).
2. `ue/sf_viz.py`의 `CSV_PATH`를 새 PC 경로로 수정.
3. 에디터 **Output Log** 입력줄 드롭다운 **Cmd→Python**, 실행:
   ```
   exec(open(r"<경로>/ue/sf_viz.py").read())
   ```
   (또는 Cmd 모드에서 `py "<경로>/ue/sf_viz.py"`, 또는 Tools→Execute Python Script)
4. 기대: 반원 공간에 점 ~3,000개 — 에어컨 축(x≈4m,y≈2.5m) 아래 진한 파랑, 가장자리 옅은 파랑 + 방사 기류선.
   - 색 대비 크게 보려면 `CSV_PATH`를 `frame_05.csv`(21.8~25.6℃).
   - 지우기: `sf_viz.py`의 `CLEAR=True`로 재실행.

### UE 반입 변환 규칙 (계약)
- 위치 m→cm: **×100**. 온도 K→℃: **T−273.15**. 컬러맵 고정 **20~29℃**(파랑=차가움→빨강=더움).
- 좌표: CFD(X=직선벽 따라, Y=방 안쪽, Z=위) → UE(X,Y,Z-up). 좌우 반전되면 Y*−1.
- 자세히: `docs/ue-import-guide.md`.

---

## 6. 다음 할 일 (TODO — 우선순위)
1. **[미완] 단일 프레임 눈검증** — §5로 프레임 1장이 뷰포트에 실제로 뜨는지 확인. Output Log에 `SF_VIZ: 3000/96714 points` 뜨면 성공.
2. **15프레임 애니메이션** — 5분 냉각을 재생. 접근: (a) 타임라인/틱마다 flush 후 다음 프레임 redraw(간단), (b) 제대로면 Niagara/Sparse Volume Texture 시퀀스.
3. **디버그 점 → 제대로 된 Niagara** — 파티클(위치=격자, 색=T, 속도=U로 흐름). 점 많으면 다운샘플(3칸마다) 또는 텍스처 베이크.
4. **mock→real 교체** — 프로젝트 머신의 실제 5분 transient CFD를 **같은 스키마 CSV**로 export(foamToVTK→CSV) → `data/frames/` 교체. **UE 쪽은 안 고침**. `source`만 `mock→simulated`.
5. **검증 원칙 유지** — 기류(U)는 못 재서 CFD로 대체 → 직접 validation 불가. **온도(T)는 싼 센서로 validation** → 온도가 맞으면 기류장 신뢰(프록시). 지금 할 수 있는 건 verification(격자 독립성·에너지 수지·물리 타당성)뿐.
6. **[별도 스펙 ②] R1~R6 재정리** — `C:\Users\ACE\Desktop\smartFarm` 골격 폴더를 R1~R6로 재정리 (아직 안 함). 그 폴더는 이 리허설과 별개(사각형 옛 골격).

---

## 7. repo 안 참고 파일
- `docs/specs/2026-09-03-ue-rehearsal-mock-cfd.md` — 설계(왜/무엇)
- `docs/plans/2026-09-03-ue-rehearsal-mock-cfd.md` — 구현계획(TDD 8태스크)
- `docs/ue-import-guide.md` — CSV→UE 변환 규칙
- `geometry.json` — 모든 파라미터 단일 출처
- `src/` — config·geometry·field_model·generate_frames·preview
- `ue/SF_Rehearsal.uproject`, `ue/sf_viz.py` — UE 테스트 자산

---

## 8. (선택) 자동화 MCP 메모
- 이번 PC에선: UnrealClaude(:3000)=문서컨텍스트, NarshaMCP(:30011)=에디터자동화(`ue_*`, 단 **이 세션에 클라이언트 MCP 미배선**이라 서브에이전트가 도구0개로 거부됨), `uefn`=`execute_python`(UEFN용).
- 새 PC에서 MCP가 클라이언트에 제대로 배선되면(예: `execute_python`), `sf_viz.py`를 사람이 안 돌리고 **자동 실행**시킬 수 있음. 안 되면 §5의 수동 실행이 확실한 폴백.
