# UE 5.8 작업 노트 — 삽질해서 알아낸 것들

같은 곳에서 두 번 막히지 않으려고 적어 둡니다. 전부 실제로 겪고 확인한 것만.

## 1. 엔진 버전과 MCP

| | 5.7 | 5.8 |
|---|---|---|
| MCP 플러그인 | NarshaMCP (서드파티) | **ModelContextProtocol (Epic 공식, Experimental)** |

`ModelContextProtocol.uplugin` 설명 그대로:
> "Anthropic MCP (Model Context Protocol) **server** implementation for Unreal Engine."

**즉 UE 가 MCP 서버가 되는 것**이고, 노출되는 도구는 우리가 직접 만든다
(`UModelContextProtocolEditorToolLibrary` 를 상속한 C++/블루프린트 함수 라이브러리의
public UFUNCTION 이 자동으로 도구로 등록됨). **엔진이 미리 만들어 둔 나이아가라/에셋
저작 도구는 없다.** 이 프로젝트는 Blueprint-only 라 도구를 추가하려면 BP 로 만들어야 한다.

`MCPClientToolset` 은 반대 방향 — UE 가 외부 MCP 서버에 붙는 어댑터.

프로젝트는 `EngineAssociation: 5.8`, 플러그인 = ModelContextProtocol / Niagara / PythonScriptPlugin.

## 2. 에디터가 백그라운드면 아무것도 안 된다 ← 가장 크게 물린 함정

기본값 `bThrottleCPUWhenNotForeground=True` 때문에 에디터가 포그라운드가 아니면:

- **나이아가라가 틱하지 않는다** → 파티클이 0개. 스폰은 됐는데 화면에 아무것도 안 나온다.
- `HighResShot` / `take_high_res_screenshot` 이 저장되지 않는다 (다음 draw 때 저장되는데 draw 가 안 됨).
- 파라미터를 바꿔도 반영이 안 돼서 **"세터가 안 먹는다"고 오진하게 된다.** 실제로 한참 헤맸다.

고친 방법 — 사용자 단위 설정에 기록 후 **에디터 재시작**:

```
%LOCALAPPDATA%\UnrealEngine\5.8\Saved\Config\WindowsEditor\EditorSettings.ini

[/Script/UnrealEd.EditorPerformanceSettings]
bThrottleCPUWhenNotForeground=False
bMonitorEditorPerformance=False
```

프로젝트의 `Saved/Config/...` 에 써도 안 먹는다. `UEditorPerformanceSettings` 는
`config=EditorSettings` 라 **사용자 단위 ini** 로 가야 한다.

## 3. 화면 캡처는 SceneCapture2D 로

뷰포트 기반 캡처(`HighResShot`, `AutomationLibrary.take_high_res_screenshot`)는
포그라운드 의존 + 비동기라 자동화에 못 쓴다. `ue/sf_capture.py` 는 `SceneCapture2D` +
트랜지언트 렌더 타깃으로 직접 그려서 이 문제를 통째로 피한다. 프레임 굽기도 이쪽이 맞다.

```sh
sh ue/cap.sh "400,285,3000,-89,0" wide 60     # x,y,z,pitch,yaw / 이름 / fov
```

덤으로 에디터 아이콘(라이트, 카메라 기즈모)이 안 찍혀서 그림이 깨끗하다.

### 뷰포트 카메라는 그냥 포기했다
`set_level_viewport_camera_info` 는 활성 뷰포트가 없으면 **에러 없이 무시된다**.
`get_...` 은 멀쩡히 옛 값을 돌려줘서 성공한 줄 안다. SceneCapture 를 쓰면 신경 쓸 일이 없다.

## 4. 원격 실행 스크립트는 UE 프로세스 안에서 돈다

`ue_exec.py -f foo.py` 로 보낸 스크립트의 `os.environ` 은 **UE 의 환경변수**다.
호출한 쪽에서 `SF_CAM=... py ue/ue_exec.py` 해도 안 넘어간다.
→ 파라미터는 파일로 넘긴다 (`data/_cap.json`).

## 5. 나이아가라 (Python 으로 할 수 있는 것 / 없는 것)

### 할 수 있다
- `.fga` 임포트 → VectorField 에셋 (`unreal.VectorFieldStaticFactory` + `AssetImportTask`)
- `NiagaraActor` 스폰, `NiagaraComponent.set_asset()`
- User 파라미터 설정 (`set_variable_*`)

### 못 한다
- **나이아가라 시스템/이미터 저작.** `NiagaraSystemFactoryNew` 는 `emitters_to_add`,
  `system_to_copy` 같은 프로퍼티를 노출하지 않는다 (확인함). 그래서 엔진에 이미 있는
  `/Niagara/VectorFields/VectorFieldVisualizationSystem` 을 그대로 쓰는 중.
  더 예쁜 연출(온도 컬러 그라디언트, 리본 트레일)은 에디터에서 한 번 저작해야 한다.

### 함정
1. **`set_variable_*` 는 이름이 틀려도 예외를 안 낸다.** 오버라이드 스토어에 그냥 기록만 한다.
   존재하지 않는 "Field", "Vector Field" 같은 이름에도 전부 "성공"한다.
   → **성공 여부의 근거로 쓰지 말 것. 눈으로 확인해야 한다.**
2. **위치 계열 User 파라미터는 LWC `FNiagaraPosition`.**
   `set_variable_vec3("FieldLocation", ...)` 는 조용히 무시된다 → `set_variable_position`.
   스케일(`FieldScale`)은 Vector 라 `set_variable_vec3` 가 맞다.
3. **한 번 활성화된 컴포넌트는 파라미터를 바꿔도 다시 안 푼다.**
   `activate(True)` / `deactivate()` 로도 안 된다. **액터를 지우고 새로 스폰**해야 한다.
   (`sf_niagara.py` 가 매번 그렇게 한다.)
4. `VectorFieldVisualizationSystem` 의 실제 User 파라미터 — uasset 문자열 테이블에서 확인:
   `VectorField`, `FieldLocation`, `FieldRotation`, `FieldScale`, `FieldCoordinates`,
   `FieldIntensity`, `FieldApplyFalloff`, `FieldFalloffDistance`, `FieldUseExponentialFalloff`
   (`NiagaraSystem` 에 `exposed_parameters` 프로퍼티는 없어서 파이썬으로는 못 읽는다.)
5. 이 시스템이 그리는 박스의 기본 한 변은 **563 cm**. 방 8.0 × 5.7 × 2.7 m 에 맞추려면
   `FieldScale = (800/563, 570/563, 270/563)`.

## 6. 머티리얼

`MaterialInstanceConstantFactoryNew` 에 `initial_parent` 프로퍼티가 **없다** (5.8).
→ 빈 인스턴스를 만든 뒤 `MaterialEditingLibrary.set_material_instance_parent()` 로 붙인다.

`/Engine/BasicShapes/BasicShapeMaterial` 의 벡터 파라미터는 **`Color` 하나뿐**이다.
`Roughness` / `Metallic` 은 없어서 설정해도 무시된다 (질감까지 주려면 자체 머티리얼 필요).

## 7. 레벨이 빈 채로 뜬다

5.8 로 올린 뒤 에디터가 `/Temp/Untitled_1` 로 떠서 "액터가 다 날아갔다"고 오해하기 쉽다.
`ue/Config/DefaultEngine.ini` 에 시작 맵을 고정해 뒀다.

```ini
[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Game/Maps/SF_Room.SF_Room
GameDefaultMap=/Game/Maps/SF_Room.SF_Room
```

## 8. 콘솔 출력 인코딩

원격 실행 결과의 한글이 cp949 로 깨져 나온다. **`grep "정렬 완료"` 같은 게 조용히 실패해서
"스크립트가 안 돌았다"고 오진하기 쉽다.** 로그 확인은 `ue/Saved/Logs/SF_Rehearsal.log`
(UTF-8) 를 보는 편이 안전하다.

## 9. 액터 숨기기 — `hidden_in_game` 은 에디터 뷰포트에 안 먹는다

`actor.set_actor_hidden_in_game(True)` 는 **SceneCapture/PIE 에만** 적용된다.
에디터 뷰포트에서는 그대로 보인다. 그래서 "캡처는 깨끗한데 화면엔 남아 있는" 상황이 된다.

- 에디터 뷰포트에서만 감추기: `actor.set_is_temporarily_hidden_in_editor(True)`
- 둘 다: 위 두 개를 같이, 또는 그냥 액터를 지운다

`SF_Niagara_Flow` 는 결국 삭제했다. 되살리려면 `py ue/ue_exec.py -f ue/sf_niagara.py`.
`.fga` 파이프라인(`src/pipeline/make_fga.py`, `/Game/VectorFields/*`)은 그대로 남겨 뒀다 —
나중에 제대로 된 Niagara 시스템을 저작하면 그때 바로 물릴 수 있다.
