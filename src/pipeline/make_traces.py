"""CFD 속도장을 따라 입자를 이류(advection)시켜 궤적을 만든다. (목적 O5-A)

왜 UE 밖에서 계산하는가
    UE 의 파이썬은 numpy 가 없고 인터프리터도 느립니다. 8만 점 격자에서
    수천 입자를 적분하면 에디터가 멈춥니다. 무거운 계산은 여기서 끝내고
    UE 는 결과 궤적을 '그리기만' 하게 합니다.

방법
    · 각 프레임의 속도장을 균일 격자에 담아 최근접 조회
    · 천장 취출구 근처에 입자를 뿌리고 RK2 로 적분
    · 방(D자) 밖으로 나가면 정지, 너무 느려지면 재시드

출력
    data/traces/trace_<frame>.csv
        pid, step, x, y, z, speed
        (좌표 m, UE 반입 시 x100)

실행
    py -m src.pipeline.make_traces            # 전 프레임
    py -m src.pipeline.make_traces 14         # 한 프레임만
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRAME_DIR = os.path.join(REPO, "data", "frames")
OUT_DIR = os.path.join(REPO, "data", "traces")

# 방 (UE 좌표계, m) — 평벽 y=0, 반타원 정점 (4.0, 5.7)
LX, LY, LZ = 8.0, 5.7, 2.7
CX = LX / 2.0

# 에어컨 4Way 카세트 중심 (UE 좌표)
AC = (4.0, 2.0, 2.7)
SLOT_R = 0.55           # 취출 슬롯이 퍼져 있는 반경

N_PARTICLES = 900
N_STEPS = 160           # 궤적 길이
DT = 0.08               # 적분 시간간격 (s) — 취출 3.5 m/s 에서 한 스텝 0.28 m
MIN_SPEED = 0.015       # 이보다 느리면 사실상 정체 → 궤적 종료
CELL = 0.12             # 조회용 격자 크기 (m)


def in_room(x, y, z):
    if z < 0.0 or z > LZ or y < 0.0:
        return False
    return ((x - CX) / CX) ** 2 + (y / LY) ** 2 <= 1.0


EPS = 0.03


def clamp_to_room(p: np.ndarray) -> np.ndarray:
    """방 밖으로 나간 입자를 경계 안쪽으로 되돌린다.

    벽에 닿았다고 죽이면 궤적이 두세 스텝에서 끊깁니다. 실제로 보고 싶은 건
    '바닥을 타고 퍼지는' 구간이므로, 경계에서 미끄러지게 둡니다.
    """
    q = p.copy()
    q[:, 2] = np.clip(q[:, 2], EPS, LZ - EPS)
    q[:, 1] = np.maximum(q[:, 1], EPS)
    # 타원 밖이면 중심 방향으로 끌어당겨 경계 위에 올린다
    e = ((q[:, 0] - CX) / CX) ** 2 + (q[:, 1] / LY) ** 2
    out = e > 1.0
    if out.any():
        k = 1.0 / np.sqrt(e[out])
        q[out, 0] = CX + (q[out, 0] - CX) * k * (1.0 - EPS)
        q[out, 1] = q[out, 1] * k * (1.0 - EPS)
    return q


class Field:
    """균일 격자 해시로 속도를 최근접 조회."""

    def __init__(self, pts: np.ndarray, vel: np.ndarray):
        self.vel = vel
        self.origin = pts.min(axis=0)
        self.dim = np.maximum(
            ((pts.max(axis=0) - self.origin) / CELL).astype(int) + 1, 1)
        idx = self._cell_index(pts)
        # 각 셀에 마지막으로 들어온 점의 인덱스를 저장 (충분히 촘촘하므로 근사로 족함)
        self.table = np.full(int(np.prod(self.dim)), -1, dtype=np.int64)
        self.table[idx] = np.arange(len(pts))
        # 빈 셀은 가장 가까운 채워진 셀로 채운다 (한 번의 전방/후방 전파)
        filled = self.table >= 0
        if not filled.all():
            order = np.arange(len(self.table))
            last = -1
            for i in order:
                if self.table[i] >= 0:
                    last = self.table[i]
                elif last >= 0:
                    self.table[i] = last
            last = -1
            for i in order[::-1]:
                if self.table[i] >= 0:
                    last = self.table[i]
                elif last >= 0:
                    self.table[i] = last

    def _cell_index(self, p: np.ndarray) -> np.ndarray:
        c = ((p - self.origin) / CELL).astype(int)
        c = np.clip(c, 0, self.dim - 1)
        return (c[:, 0] * self.dim[1] * self.dim[2]
                + c[:, 1] * self.dim[2] + c[:, 2])

    def sample(self, p: np.ndarray) -> np.ndarray:
        i = self.table[self._cell_index(p)]
        i = np.where(i < 0, 0, i)
        return self.vel[i]


def load_frame(idx: int):
    path = os.path.join(FRAME_DIR, "frame_%02d.csv" % idx)
    xs, vs = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            xs.append((float(r["x"]), float(r["y"]), float(r["z"])))
            vs.append((float(r["Ux"]), float(r["Uy"]), float(r["Uz"])))
    return np.asarray(xs, dtype=np.float64), np.asarray(vs, dtype=np.float64)


def seed(n: int, rng: np.random.Generator) -> np.ndarray:
    """취출 슬롯 링 위에 뿌린다 (중앙은 리턴이라 제외)."""
    th = rng.uniform(0.0, 2 * np.pi, n)
    rr = SLOT_R * np.sqrt(rng.uniform(0.35, 1.0, n))     # 도넛 형태
    return np.stack([AC[0] + rr * np.cos(th),
                     AC[1] + rr * np.sin(th),
                     np.full(n, AC[2] - 0.05)], axis=1)


def trace_frame(idx: int, rng: np.random.Generator):
    pts, vel = load_frame(idx)
    field = Field(pts, vel)
    p = seed(N_PARTICLES, rng)
    alive = np.ones(len(p), dtype=bool)

    rows = []
    for step in range(N_STEPS):
        v = field.sample(p)
        spd = np.linalg.norm(v, axis=1)
        # RK2 (midpoint)
        mid = p + v * (DT * 0.5)
        v2 = field.sample(mid)
        nxt = p + v2 * DT

        nxt = clamp_to_room(nxt)
        # 정체된 입자만 은퇴시킨다 (벽 접촉으로는 죽이지 않음)
        alive &= spd > MIN_SPEED
        p = np.where(alive[:, None], nxt, p)

        for pid in np.nonzero(alive)[0]:
            rows.append((int(pid), step,
                         round(float(p[pid, 0]), 4),
                         round(float(p[pid, 1]), 4),
                         round(float(p[pid, 2]), 4),
                         round(float(spd[pid]), 4)))
        if not alive.any():
            break
    return rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    frames = ([int(sys.argv[1])] if len(sys.argv) > 1
              else list(range(15)))
    for i in frames:
        rng = np.random.default_rng(1234 + i)       # 재현 가능하게 고정
        rows = trace_frame(i, rng)
        out = os.path.join(OUT_DIR, "trace_%02d.csv" % i)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["pid", "step", "x", "y", "z", "speed"])
            w.writerows(rows)
        npart = len({r[0] for r in rows})
        print("trace_%02d: %d rows, %d particles -> %s"
              % (i, len(rows), npart, out))


if __name__ == "__main__":
    main()
