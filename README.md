# smartfarm-ue-rehearsal

스마트팜 D자 방(8.0×5.7×2.7 m)의 냉방 15분을 **계산(CFD/수식) → CSV → 언리얼·웹**으로
보여주는 디지털트윈 리허설. 언리얼은 계산하지 않고 CSV 를 그리기만 한다.

> 전체 루프·임시값 교체 지점은 `docs/STRUCTURE.md`, 이력은 `docs/OBJECTIVES.md`.

## 지금 화면이 뭘 그리는지 — 데이터 출처 3종

`data/frames/manifest.json` 의 `source` 필드가 항상 정답이다.

| source | 정체 | 위치 |
|---|---|---|
| `acRoom-vane25 ...` | **진짜 CFD** (OpenFOAM 7h, 4방향 25° 측면취출) — 기준 | `data/archive/vane25` |
| `MOCK-live ...` | 임시 수식 예측 — 툴바 [SF 갱신]이 생성 (에어컨 이동용) | 작업본에만 |
| (구) 수직취출 | 첫 CFD, 취출각이 실물과 달라 은퇴 | `data/archive/vert` |

```bash
py -m src.pipeline.restore vane25      # [SF 갱신]으로 덮인 화면을 진짜 CFD 로 복원
```

## 예측을 만들 수 있는 놈 3종 — 화면에 연결된 건 하나뿐

| | 정체 | 화면 연결 | 위치 |
|---|---|---|---|
| **수식 모델** | 사람이 쓴 물리 흉내 공식. 상수는 vane25 에서 단순 피팅(신경망 아님) | ✅ [SF 갱신] | `src/models/` |
| **PINN** | 신경망+물리 학습. 센서 12점 복원 리허설 1회 (0.62℃ vs 수식 1.57℃) | ❌ | `src/ml/` |
| **PINO/대리모델** | CFD 통째 학습. 목데이터 학습 리허설만 | ❌ | `src/ml/` |

실측(R1)이 오면 PINN 이 보정 → PINO 교체가 계획 (`docs/STRUCTURE.md` 루프).

## 폴더 지도

```
geometry.json        모든 물리 상수의 단일 출처
src/                 파이썬 (py -m src.<패키지>.<이름>)
  config.py geometry.py   공용 (설정 로더·D자 격자)
  pipeline/            데이터 -> 화면 재료 (계산 없음, 변환만)
    make_*.py            frames -> 파생 CSV (slices/jets/traces/ribbons/arrows/probes)
    make_web.py          -> out/web/index.html (자급자족 웹 미리보기)
    make_video.py        -> out/smartfarm-flow.mp4 (구운 영상)
    restore.py           보존 데이터셋 -> 작업본 복원 (위 참조)
    preview.py verify.py 눈검증 PNG · 파이프 자가검증
  models/              수식 모델 (화면에 연결된 유일한 예측기)
    predict_mock.py      [SF 갱신]의 몸체 — 즉석 수식 예측 (교체 예정)
    vane_mock.py         수식 본체 + 상수 (시정수·UA 등, vane25 피팅값)
    power_model.py room_model.py field_model.py generate_frames.py
  ml/                  신경망 (전부 리허설, 미연결)
    pinn_check.py        실측 판정 (격자 최소제곱)
    pinn_rehearsal.py    DeepXDE PINN — 센서 12점 장 복원
    make_dataset.py train_surrogate.py   PINO 교재·학습
ue/                  언리얼 원격 스크립트 (py ue/ue_exec.py -f ue/<파일>)
  ue_exec.py           원격 실행기 — 프로젝트명(SF_Rehearsal)으로 에디터 선택
  sf_geom.py           메시·머티리얼 공용 (모든 sf_* 가 씀, 수정 시 reload 주의)
  sf_sequencer2.py     프레임 액터 + 보간 시퀀스 빌드 (배속은 data/_seq.json)
  sf_refresh.py        툴바 [SF 갱신] — predict_mock 실행 + 재빌드
  sf_play.py/sf_toolbar.py  툴바 버튼 (30/10배속·정지·갱신)
  sf_make_*.py         구조물 생성 (레벨/바닥/에어컨/조명/재배단)
  Content/Python/init_unreal.py  에디터 시작 시 툴바 등록 + 프레임 액터 숨김
data/
  frames/              작업본 (source 필드로 출처 확인) — CSV는 git 미추적
  jets/ slices/ ...    파생 CSV (frames 에서 재생성 가능)
  archive/vane25/      진짜 CFD 보존본 (git 추적) ★
  archive/vert/        구버전 CFD (로컬만)
  _*.json              스크립트 런타임 파라미터 (카메라·배속·프레임 등)
docs/                구조·검증·PINN·UE 함정 문서
web/template.html    웹 미리보기 템플릿 (make_web 이 데이터 인라인)
out/                 산출물 (git 미추적) — web/index.html, mp4, 캡처
```

## 자주 쓰는 명령

```bash
# 데이터 (리포 루트에서, python 대신 py)
py -m src.pipeline.restore vane25              # 진짜 CFD 복원 (웹 재생성 포함)
py -m src.pipeline.make_web                    # 웹 미리보기만 재생성

# 언리얼 (에디터 켠 상태, SF_Rehearsal 프로젝트만 잡는다)
py ue/ue_exec.py -f ue/sf_sequencer2.py    # 시퀀스 재빌드 (data/_seq.json 의 배속)
sh ue/cap.sh "x,y,z,pitch,yaw" 이름 [fov]  # SceneCapture 스크린샷
sh ue/frame.sh 7                           # 특정 프레임만 레벨에 세우기

# 에디터 툴바 버튼 (자동 등록)
[SF 30배속] [SF 10배속] [SF 정지]     # 재생 전환
[SF 갱신]                              # 에어컨 옮긴 위치로 임시 수식 예측 (화면이 MOCK-live 로 바뀜)

# CFD (WSL 도커 — hanes/openfoam-docker-new-pc.md)
docker run --rm --user 1000:1000 -e HOME=/tmp \
  -v /home/hunvr/smartfarm-cfd:/data opencfd/openfoam-default:2512 \
  bash /data/cases/<케이스>/RUN.sh
```

## 폴더 재배치 이력 (2026-09-15)

"지금 화면이 수식이냐 PINN이냐" 혼선을 계기로 구조를 갈아엎었다. 원칙:

- **역할이 폴더다**: `pipeline/`(변환만, 예측 없음) · `models/`(수식 — 화면에
  연결된 유일한 예측기) · `ml/`(신경망 — 전부 리허설, 미연결).
  파일이 어느 폴더에 있는지가 곧 "이 값을 믿어도 되나"의 답이다.
- **보존 데이터는 `data/archive/`**: `_real-vane25`, `_real-vert` 같은 언더스코어
  이름을 폐지하고 `archive/vane25`, `archive/vert` 로 통합. 복원은
  `py -m src.pipeline.restore <이름>` 한 줄.
- **공용(config·geometry)은 src 루트 유지** — import 경로 변경 최소화.
- **ue/ 는 평면 유지(의도)**: sh 래퍼·툴바 커맨드·sf_* 상호 import 가 평면
  구조를 전제해서, 옮기면 깨지는 범위 대비 이득이 없다. 접두사(sf_make_/sf_)로 구분.
- 옛 경로(`src/make_web.py` 등)가 적힌 문서는 `docs/plans/`·`docs/specs/`(역사
  기록)뿐이다 — 당시 기록이라 일부러 안 고쳤다. 현행 문서는 전부 새 경로.

## 함정 모음 (한 번씩 다 밟은 것)

- 에디터 백그라운드 스로틀링, SceneCapture 는 볼륨 못 찍음 → `docs/UE-NOTES.md`
- pvpython 시간별 반출, 시퀀서 키 틱 해상도, pandas DLL 차단 → `Desktop/hanes/`
- UEFN 과 UE 를 같이 켜면 원격 명령이 섞였던 사고 → ue_exec 가 프로젝트명으로 선택함
