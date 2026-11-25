# 18대 팬 · 600초 CFD 재검증
PINO + 측면 팬 응답 근사로 선정한 한 개의 운전표를 독립 CFD로 검증한다. CFD 결과는 실행 후 생성된다.

## Windows PowerShell
Python 3.8 이상, Git, Docker Desktop의 Linux 엔진 필요. 새 작업 폴더에서 실행한다.

```powershell
git clone --depth 1 --filter=blob:none --sparse --single-branch --branch cfd/20261104 https://github.com/b-hyoung/smartfarm-ue-rehearsal.git smartfarm-18fan
cd smartfarm-18fan
git sparse-checkout set data/runs/20261104/18fan-validation
cd data/runs/20261104/18fan-validation
py -3 validate18.py check
docker info --format '{{.OSType}} {{.NCPU}}'
py -3 validate18.py start --ranks 4
```

4는 예시 MPI 프로세스 수다. Docker 할당 CPU가 4개 미만이면 줄인다. Linux에서는 py -3 대신 python3을 사용한다. check는 원본 압축 해시, 구간·층 순서, 팬별 명령 및 구간별 입력 사전 생성을 검사한다. 격자 생성과 솔버 실행은 start에서 수행한다.

start는 컨테이너를 백그라운드로 실행하고 로그 조회 명령을 출력한다. 기본 출력 폴더는 사용자 홈의 SmartFarm18-validation이다. 다른 이름은 --output PATH로 지정한다. 같은 이름의 실행 폴더를 덮어쓰지 않는다. results/status.txt와 results/log.0-60 등 구간별 로그에서 진행 상태를 확인한다. 전체 계산장은 출력된 Docker 볼륨에 남는다.

## 입력 및 평가
- 기존 2번 조건의 초기장·단열 경계·냉방·캐노피·149,426셀 격자를 사용한다. 원본 격자 해시 확인 후 측면 팬 영역 4개를 추가하고 18개 영역이 비어 있지 않은지 확인한다.
- 층별 앞쪽 1~4번(+y), 뒤쪽 5~7번(−y), 왼쪽(+x), 오른쪽(−x). 측면 토출 중심은 x=±1.2 m, y=2.0 m, z=0.70/1.50 m. 측면 팬 수치모델은 지름 92 mm, 토출면에서 안쪽 25 mm에 운동량을 가하는 가정이다.
- 0–60초부터 540–600초까지 속도·온도장을 이어서 계산한다. CSV 풍량은 m³/min, 0은 정지다. 추력은 기존 0.84 CMM 추력을 기준으로 풍량비의 제곱에 비례시킨다. CSV 마지막 열은 예측값이다.
- 재배판 위 15 cm의 두 평가면에서 60초 간격 10시점, 층별 60×20 격자의 최근접 표본으로 0.3–1.0 m/s 도달률을 비교한다. 예측 전체 53.0375%(위층 50.94%, 아래층 55.13%). 온도는 CFD 각 층의 면적평균 기록과 T 지도로 확인한다.

완료 후 아래 명령으로 results/comparison.csv에 시점·층별 CFD 도달률, 예측값, 차이(%p)를 기록한다.
```powershell
py -3 -m pip install numpy scipy
py -3 compare.py "$HOME/SmartFarm18-validation/results"
```
