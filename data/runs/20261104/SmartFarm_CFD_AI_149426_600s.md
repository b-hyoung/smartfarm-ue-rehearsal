# 스마트팜 CFD · 다른 PC의 AI 작업 인계서

**사용법**　이 파일을 다른 컴퓨터의 AI에게 첨부하고 **“1번 케이스 해”**처럼 번호만 보낸다. AI가 해당 PC의 설치 상태 확인부터 격자 검증, 성능 측정, 본 계산 시작, 온도 기록 확인까지 맡는다. **4번은 원래 PC에서 실행 중이다.**

[이 인계서의 GitHub 페이지](https://github.com/b-hyoung/smartfarm-ue-rehearsal/blob/cfd/20261104/data/runs/20261104/SmartFarm_CFD_AI_149426_600s.md) · [원본 Markdown 다운로드](https://raw.githubusercontent.com/b-hyoung/smartfarm-ue-rehearsal/cfd/20261104/data/runs/20261104/SmartFarm_CFD_AI_149426_600s.md) · [프로젝트 저장소](https://github.com/b-hyoung/smartfarm-ue-rehearsal)

## 1. 배정받은 케이스

| 사용자가 보낸 말 | 케이스 | 냉방기 | 하단 팬 | 상단 팬 | 입력 복원 후 실행할 명령 |
|---|---|---|---:|---:|---|
| **1번 케이스 해** | `01_ac_only` | 켬 | 0 | 0 | `py -3 farm.py start 1` |
| **2번 케이스 해** | `02_ac_all` | 켬 | 7 | 7 | `py -3 farm.py start 2` |
| **3번 케이스 해** | `03_ac_lower` | 켬 | 7 | 0 | `py -3 farm.py start 3` |
| **4번 케이스 해** | `04_ac_upper` | 켬 | 0 | 7 | `py -3 farm.py start 4` · 원래 PC 담당 |

받는 AI는 사용자가 지정한 번호 한 개를 끝까지 처리한다. “1번 케이스 해”에는 1번의 설치·벤치마크·본 계산 시작이 포함된다. 번호가 아직 없으면 설치와 환경 확인을 먼저 하고 번호만 확인한다. 1번의 순환팬은 모두 정지하지만 냉방기 네 토출구는 계속 작동한다.

## 2. 네 PC가 공유할 실험 조건

| 항목 | 고정할 값 |
|---|---|
| 목적 | 개방형 2단 재배대에서 팬 가동 방식에 따른 캐노피 기류·온도 분포와 양단 동시 목표온도 도달시간 비교 |
| 방·재배대 | 반타원형 방. 설계 평면 폭 8.0 m, 최대 깊이 5.7 m, 높이 2.7 m. 각 재배판 2.40 × 0.80 m, 윗면은 바닥 기준 0.55 m와 1.35 m. 상판은 z=1.750~1.785 m에서 닫힘 |
| 상추 캐노피 | 단별로 밀식한 18 cm 연속 다공성 층. 하단 z=0.55~0.73 m, 상단 z=1.35~1.53 m. Darcy–Forchheimer 점성저항계수 25 m⁻², 관성저항계수 1.3 m⁻¹, 세 축 동일 |
| 냉방기 | 천장 4방향, 토출온도 18°C(291.15 K), 속력 3.5 m/s, 수평 기준 하향 30°. 수직 성분 −1.75 m/s. 모델 입력은 출구당 6.25 m³/min(CMM), 합계 25 CMM. 수평면 유효 슬롯 한 곳 약 0.650 × 0.091575 m |
| 순환팬 | 각 단 앞쪽 4대·뒤쪽 3대 교차 배치, 재배판 윗면에서 팬 중심까지 15 cm. 앞은 +y, 뒤는 −y로 수평 송풍. 명목 지름 92 mm. 가동 팬당 0.84 CMM(0.014 m³/s)을 약 0.03450 N 추력으로 환산한 운동량 소스. 팬에는 별도 토출온도 지정 없이 실내 공기 순환 |
| 초기장·열조건 | 초기 공기 28.85°C(302 K), 풍속 0 m/s, 압력 100,000 Pa. 방 벽·재배판·상판 모두 단열. 조명 발열, 작물 증산열, 복사 열전달 생략 |
| 격자 | **149,426셀**. 하단 캐노피 32,960셀, 상단 33,000셀. 14개 팬 영역 유지. 방 외곽 격자를 넓히고 네 냉기 제트는 토출구 가까운 구간을 추가 세분. `checkMesh` 및 기준 격자 파일 6개 SHA-256 대조 |
| 해석 | OpenFOAM v2512, `buoyantPimpleFoam`, 비정상 해석, RAS k–ε. 물리시간 **0~600초**, 초기 Δt=0.002초, 자동 시간 간격, 최대 Courant 수 1, Δt 상한 0.5초. CPU의 MPI 프로세스 수는 PC별 실측으로 선택 |
| 평가·저장 | 재배판 위 15 cm에서 단별 **공기 온도의 면적평균**을 물리시간 1초마다 기록. 평가면은 단당 1.9104 m². 15 cm 주 평가면과 18 cm 보조면에서 U·T 분포를 60초마다 저장. 재배판 위 10 cm 보조점 42곳의 U·T는 300·600초에 추출 |
| 온도 기록·판정 | **시뮬레이션 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600초**에 상·하단 평균온도를 각각 °C로 저장. 별도로 전체 1초 간격 기록에서 양단이 **동시에 21~23°C**에 처음 들어간 시각 확인. 600초까지 없으면 “10분 이내 미도달” |
| CPU 상태 | 시작 직후 첫 표본, 이후 실제 약 5분 간격으로 CPU 사용률·메모리·계산 진행 상태 기록. 지원되는 센서에서 CPU 패키지 온도 기록. 센서가 없는 환경은 공란 |

풍량·추력·유효 슬롯은 연구용 모델 입력값이다. 149,426셀의 기하 및 입력 검증과 600초 해석 결과의 격자 독립성은 별개다. 기존 GitHub 브랜치의 일반 `pc-case.ps1`은 403,210셀 설정이다. **이 작업에서는 아래에 내장한 149,426셀 실행기를 사용한다.**

## 3. AI가 수행할 설치

1. 운영체제·CPU 모델·물리 코어·논리 스레드·RAM·실제 여유 저장공간을 확인한다. 기존 Docker의 실행 작업을 확인한다. 장시간 계산 중 전원 연결과 절전 여부도 확인한다.
2. **Windows 10/11 x64**에서는 `py -3 --version`, `wsl --status`, `wsl --version`, `docker version`, `docker info`로 기존 설치부터 확인한다. Windows의 Python 실행기가 없으면 Python 3.10 이상을 설치한다. 예시는 `winget install -e --id Python.Python.3.12`이다. Docker가 없으면 Docker Desktop을 설치한다. 예시는 `winget install -e --id Docker.DockerDesktop`이다. WSL 2가 필요하면 관리자 PowerShell에서 `wsl --install` 또는 기존 설치의 `wsl --update`를 실행하고, 재시작이 필요한 경우 재시작 후 이 문서부터 이어간다. Docker Desktop을 시작해 Linux 컨테이너 및 WSL 2 엔진으로 연결한다. 관리자 승인·라이선스 확인 등 사용자 조작이 실제로 필요한 지점만 요청한다. [Docker Windows 설치](https://docs.docker.com/desktop/setup/install/windows-install/) · [Microsoft WSL 설치](https://learn.microsoft.com/en-us/windows/wsl/install) · [Python Windows 설치본](https://www.python.org/downloads/windows/)
3. **Linux**에서는 Python 3와 로컬 Docker Engine을 사용한다. 해당 배포판의 공식 저장소 방식으로 설치하고 Docker 데몬을 시작해 현재 계정으로 `docker info`가 되는지 확인한다. **macOS**에서는 해당 칩용 Docker Desktop과 Python 3를 사용한다. 이 실험의 검증 이미지 플랫폼은 `linux/amd64`다. ARM에서는 에뮬레이션 가능 여부와 실제 시간을 해당 PC에서 확인한다. [Docker Engine 설치](https://docs.docker.com/engine/install/) · [Docker Desktop Mac 설치](https://docs.docker.com/desktop/setup/install/mac-install/)
4. `docker context show`로 해당 PC의 로컬 엔진을 확인한다. 첫 실행 때 고정된 OpenFOAM 이미지와 의존 레이어를 내려받기 위한 인터넷 연결이 필요하다. OpenFOAM·MPI는 이미지 안에 들어 있다. Python은 표준 라이브러리만 사용한다.

## 4. 이 Markdown 한 파일에서 입력 복원

파일명을 `SmartFarm_CFD_AI_149426_600s.md`로 저장한다. AI는 파일 끝의 긴 부록을 채팅에 읽어 들일 필요 없이 아래 **bootstrap** 블록을 실행한다. 실행기, 네 케이스, 온도·속도 평가면과 팬·캐노피 사전이 들어 있다. 복원 위치는 해당 PC 사용자 홈의 `SmartFarmCFD_149426_600s`다.

**Windows PowerShell.** 파일이 바탕화면에 있으면 아래 그대로 실행한다. 다른 위치에 첨부되었으면 `$Doc`만 실제 경로로 지정한다.

```powershell
$Doc = Join-Path ([Environment]::GetFolderPath('Desktop')) 'SmartFarm_CFD_AI_149426_600s.md'
$Text = [IO.File]::ReadAllText($Doc)
$Code = [regex]::Match($Text, '(?ms)^```python bootstrap\r?\n(.*?)^```').Groups[1].Value
if (!$Code) { throw 'bootstrap block missing' }
$Code | py -3 - "$Doc"
if ($LASTEXITCODE) { throw 'package extraction failed' }
Set-Location (Join-Path ([Environment]::GetFolderPath('UserProfile')) 'SmartFarmCFD_149426_600s')
```

**Linux / macOS.** `DOC`에 실제 파일 경로 지정.

```bash
DOC="$HOME/Downloads/SmartFarm_CFD_AI_149426_600s.md"
sed -n '/^```python bootstrap$/,/^```$/p' "$DOC" | sed '1d;$d' | python3 - "$DOC"
cd "$HOME/SmartFarmCFD_149426_600s"
```

```python bootstrap
import base64, hashlib, io, lzma, re, sys, zipfile
from pathlib import Path
doc = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
block = re.search(r"(?ms)^```smartfarm-bundle\s*\n(.*?)^```", doc)
if block is None:
    raise SystemExit("Payload missing: download the raw Markdown file.")
packed = base64.b64decode("".join(block[1].split()), validate=True)
if hashlib.sha256(packed).hexdigest() != "0ba10f02c78a0fade2c537deceeac13b38465cf70583c70e0bcef7f71c7053b5":
    raise SystemExit("Package checksum mismatch.")
root = Path.home() / "SmartFarmCFD_149426_600s"
with zipfile.ZipFile(io.BytesIO(lzma.decompress(packed))) as archive:
    for name in archive.namelist():
        path = (root / name).resolve()
        path.relative_to(root.resolve())
        data = archive.read(name)
        if path.exists() and path.read_bytes() != data:
            raise SystemExit("Existing file differs: " + str(path))
    for name in archive.namelist():
        path = root / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(name))
print("Verified and extracted to", root)
```

## 5. 담당 번호 실행과 확인

**예시 — 사용자의 지시가 “1번 케이스 해”이면** 복원한 폴더에서 아래를 실행한다. 2번·3번은 숫자 한 자리만 바꾼다. Linux/macOS에서는 `py -3` 대신 `python3`를 사용한다.

```powershell
py -3 farm.py start 1
py -3 farm.py status 1
```

`start 1`이 Docker의 CPU 한도 확인 → 1번 격자 생성·검산 → 같은 1번 케이스의 프로세스 수 후보별 **냉방 1초 벤치마크** → 가장 빠른 후보 선택 → **0초부터 600초 본 계산**을 수행한다. 벤치마크는 한 번에 하나씩 진행한다. 본 계산은 백그라운드 컨테이너에서 실행된다. 같은 번호의 컨테이너가 이미 있으면 기존 상태를 표시한다.

- **다른 사양에 맞추기.** CPU 12개를 일괄 지정하지 않는다. 예를 들어 물리 8코어이고 Docker가 9 CPU로 제한됐으면 기본 후보는 8·9다. 개별 비교가 필요하면 `py -3 farm.py prepare 1`, `py -3 farm.py bench 1 8 9`, `py -3 farm.py run 1` 순서로 실행한다. `results/<케이스>/bench.json`에 각 후보의 실제 소요시간과 선정값이 기록된다.
- **마감 추정.** 그 PC에서 냉방 1초를 푸는 데 실제 `W`초가 걸리면 600초 본 계산은 대략 `W ÷ 6`시간이다. 원래 PC의 4번은 Ryzen 9 9900X·12프로세스에서 121초였고 환산값은 20시간 10분이었다. 담당 케이스와 장비마다 별도로 측정해 사용자에게 시작 시각, 예상 완료 시각 및 마감 가능성을 보고한다. 프로젝트 마감 기준은 한국시간 2026-11-25 18시다.
- **실행 검증.** `status`와 `results/<케이스>/cpu_health.csv`에서 첫 표본 이후 `simulation_s` 증가 여부와 `oom_kills`를 확인한다. CPU 사용률은 논리 CPU 한 개가 100%이므로 병렬 계산에서는 100%를 넘을 수 있다. CPU 센서 공란은 미측정이다. 냉방 300초까지 온도표에 데이터 행이 없는 것은 정상이다.
- **기존 작업·오류.** 컨테이너 이름은 `smartfarm-149426-v1-<케이스>`, 준비 격자와 계산 데이터는 각각 같은 접두어 뒤 `-mesh`, `-run` 볼륨에 보관한다. 도중 중단 시 `status`, `docker logs <컨테이너>`, `results/<케이스>/failure.log` 및 컨테이너 안 `/work/<케이스>/log.run`을 확인한다. 기존 체크포인트와 볼륨을 보존하고 중단 물리시각과 사유를 보고한다.

## 6. 제출 결과

| 위치 | 내용 |
|---|---|
| `results/<케이스>/canopy_300-600s.csv` | 300~600초, 30초 간격의 `simulation_s, lower_15cm_C, upper_15cm_C`. 완료 시 데이터 11행 |
| `results/<케이스>/cpu_health.csv` | 실제 UTC 시각, 진행 물리시간, CPU 사용률, 메모리, OOM 횟수, 지원 시 패키지 온도 |
| `results/<케이스>/postProcessing` | 완료 후 복사되는 단별 1초 간격 평균온도(K), 60초 간격 분포, 보조 측정점. 원시 켈빈 온도는 273.15를 빼서 °C로 환산 |
| `results/<케이스>/status.txt`와 `log.run` | `complete` 상태, 컨테이너 종료코드 0, 600초의 U·T, 온도표 11행 확인 후 완료 보고. 전체 3D 장은 계산 볼륨 `/work/<케이스>/60` … `600`에 보존 |

보고 시 담당 번호, 장비·프로세스 수, 1초 실측, 본 계산 상태, 상·하단 온도표 경로를 함께 제시한다. 목표온도 최초 도달시간은 **전체 1초 간격 기록**으로 판단한다. 300초부터 시작하는 11행 표는 정해진 시각의 단면 평균을 보고하는 용도다.

<details>
<summary>검산된 실행 입력 부록 · 원본 Markdown에서 프로그램이 자동 복원</summary>

```smartfarm-bundle
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
xGf7AgAAAAAEWVo=
```

</details>
