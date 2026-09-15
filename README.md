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

PINN(`src/pinn_*.py`)은 화면에 안 나간다 — vane25 를 정답지로 "센서 12점 복원"을
채점한 검증 실험 (`docs/PINN-REHEARSAL.md`).

```bash
py -m src.restore vane25      # [SF 갱신]으로 덮인 화면을 진짜 CFD 로 복원
```

## 폴더 지도

```
geometry.json        모든 물리 상수의 단일 출처
src/                 파이썬 파이프라인 (py -m src.<이름>)
  make_*.py            frames -> 파생 CSV (slices/jets/traces/ribbons/arrows/probes)
  make_web.py          -> out/web/index.html (자급자족 웹 미리보기)
  make_video.py        -> out/smartfarm-flow.mp4 (구운 영상)
  restore.py           보존 데이터셋 -> 작업본 복원 (위 참조)
  predict_mock.py      [SF 갱신]의 몸체 — 임시 수식 예측 (교체 예정)
  vane_mock.py         목데이터 생성 (수식 모델 상수 포함)
  pinn_check.py / pinn_rehearsal.py   실측 판정 / PINN 리허설
  make_dataset.py / train_surrogate.py  PINO 교재·학습 (리허설)
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
py -m src.restore vane25              # 진짜 CFD 복원 (웹 재생성 포함)
py -m src.make_web                    # 웹 미리보기만 재생성

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

## 함정 모음 (한 번씩 다 밟은 것)

- 에디터 백그라운드 스로틀링, SceneCapture 는 볼륨 못 찍음 → `docs/UE-NOTES.md`
- pvpython 시간별 반출, 시퀀서 키 틱 해상도, pandas DLL 차단 → `Desktop/hanes/`
- UEFN 과 UE 를 같이 켜면 원격 명령이 섞였던 사고 → ue_exec 가 프로젝트명으로 선택함
