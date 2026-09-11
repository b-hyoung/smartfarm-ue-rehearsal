"""PINO 학습용 데이터셋 생성 — 「조건 → 온도장」 쌍.

지금은 수식 모델(vane_mock)로 무한정 뽑아 **파이프라인 리허설용** 교재를 만든다.
진짜 CFD 케이스가 쌓이면 같은 규격으로 채워 넣는다 (교체 지점 = 이 파일).

규격 (data/dataset/mock_v1.npz):
    X    (N, 3)        조건 벡터 [ac_x(m), ac_y(m), t(s)]
    Y    (N, 72, 101)  1.1 m 수평 온도장 (℃), 방 밖은 NaN
    Yv   (N, 34, 101)  에어컨 통과 수직 온도장 (℃)
    mask (72, 101)     D자 방 안쪽 True
  + meta.json          격자·단위·좌표 규약 (R5 와의 계약 문서)

실행  py -m src.make_dataset          (기본: 위치 50곳 × 15시각 = 750쌍)
      py -m src.make_dataset 200      (위치 수 지정)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from src.config import load_config
from src.geometry import inside_mask
from src.vane_mock import TIMES, temperature

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "dataset")
KELVIN = 273.15
NX, NY, NZ = 101, 72, 34
Z_H = 1.1


def main():
    n_pos = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    cfg = load_config(os.path.join(REPO, "geometry.json"))
    rng = np.random.default_rng(42)          # 재현 가능해야 교재다

    xs = np.linspace(0.0, cfg.room.Lx, NX)
    ys = np.linspace(0.0, cfg.room.Ly, NY)
    zs = np.linspace(0.05, cfg.room.Lz - 0.05, NZ)
    HX, HY = np.meshgrid(xs, ys, indexing="xy")          # (NY, NX)
    mask = inside_mask(HX.ravel(), HY.ravel(), cfg).reshape(NY, NX)
    hpts = np.stack([HX.ravel(), HY.ravel(),
                     np.full(HX.size, Z_H)], axis=1)

    # 에어컨 위치 샘플: 방 안쪽(경계 0.8 m 여유)에서 균등 추출
    acs = []
    while len(acs) < n_pos:
        c = rng.uniform([0.8, 0.8], [cfg.room.Lx - 0.8, cfg.room.Ly - 0.8])
        if inside_mask(np.array([c[0]]), np.array([c[1]]), cfg)[0]:
            acs.append(c)
    acs = np.array(acs)

    X, Y, Yv = [], [], []
    for i, ac in enumerate(acs):
        VX, VZ = np.meshgrid(xs, zs, indexing="xy")      # (NZ, NX)
        vpts = np.stack([VX.ravel(), np.full(VX.size, ac[1]),
                         VZ.ravel()], axis=1)
        for t in TIMES:
            Th = temperature(hpts, t, cfg, ac) - KELVIN
            Th = Th.reshape(NY, NX)
            Th[~mask] = np.nan
            Tv = (temperature(vpts, t, cfg, ac) - KELVIN).reshape(NZ, NX)
            X.append([ac[0], ac[1], t])
            Y.append(Th.astype(np.float32))
            Yv.append(Tv.astype(np.float32))
        if (i + 1) % 10 == 0:
            print("  위치 %d/%d" % (i + 1, n_pos))

    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(os.path.join(OUT, "mock_v1.npz"),
                        X=np.array(X, dtype=np.float32),
                        Y=np.stack(Y), Yv=np.stack(Yv), mask=mask)
    meta = {
        "source": "MOCK (src/vane_mock.py) — PINO 파이프라인 리허설용. "
                  "진짜 CFD 케이스가 쌓이면 같은 규격으로 교체",
        "X": "조건 [ac_x(m), ac_y(m), t(s)] — 이후 확장: 베인각, 풍량, 조명%",
        "Y": "1.1m 수평 온도장 ℃, (NY=72, NX=101), 방 밖 NaN",
        "Yv": "AC 통과 수직 온도장 ℃, (NZ=34, NX=101)",
        "grid": {"x_m": [0.0, cfg.room.Lx], "y_m": [0.0, cfg.room.Ly],
                 "z_m": [0.05, cfg.room.Lz - 0.05], "z_h": Z_H},
        "coord": "UE 좌표(m). CFD x-4 시프트 규약은 frames 와 동일",
        "n_samples": len(X), "n_positions": n_pos, "times_s": TIMES,
        "rng_seed": 42,
    }
    with open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    sz = os.path.getsize(os.path.join(OUT, "mock_v1.npz")) / 1e6
    print("done: %d쌍 (위치 %d × 시각 %d) -> data/dataset/mock_v1.npz (%.1f MB)"
          % (len(X), n_pos, len(TIMES), sz))


if __name__ == "__main__":
    main()
