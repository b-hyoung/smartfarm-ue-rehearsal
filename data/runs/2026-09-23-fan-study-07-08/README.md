# 7·8 번 결과 · 2026-09-23

`docs/FAN-RESULTS.md` 4-1 절에 배정된 7·8 번을 다른 PC(WSL2 + Docker Engine, 32 코어)에서
돌린 결과다. 값 해석과 판단은 `docs/FAN-RESULTS.md` 2-1 절에 있다.

## 무엇이 들어 있나

| | 07_F5 | 08_F6 |
|---|---|---|
| 조건 | 9.6 CMM 4 대 | 12.0 CMM 4 대 |
| 상태 | 600 초 완주 (`DONE`) | 진행 중 — 채점 시점 534 / 600 초 |
| 분할 · CPU 상한 | 18 분할, 19 코어 | 18 분할, 19 코어 |
| 벽시계 | 9 시간 59 분 | (진행 중) |

각 폴더:

| 파일 | 내용 |
|---|---|
| `case.json` | 이 케이스의 조건 |
| `postProcessing.tar.gz` | 판정면 원본 샘플(.raw) + 유량 검산 |
| `log.allrun`, `log.blockMesh`, `log.topoSet`, `log.decomposePar` | 격자·분할 기록 |

용량 대부분을 차지하는 `processor*`(원본 격자·필드)와 전체 solver 로그(`log.run`)는
빼고 옮겼다 — `docs/FAN-RESULTS.md` 5 절 관례대로 `postProcessing/`만 있으면 채점이 된다.

## 08_F6 갱신 예정

08_F6 은 이 커밋 시점에 아직 돌고 있었다. 완주 후 같은 폴더에 다시 패키징해 덮어쓰고
`docs/FAN-RESULTS.md` 2-1 절의 잠정값(*)도 확정값으로 바꿀 것.
