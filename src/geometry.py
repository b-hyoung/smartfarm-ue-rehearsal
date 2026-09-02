"""반원(반타원 근사) 공간의 규칙 격자. 직선벽 y=0, 곡면벽은 y+ 방향 반타원."""
import numpy as np


def inside_mask(x, y, cfg):
    """(x,y)가 D자형 풋프린트 안이면 True. a=Lx/2, b=Ly, 중심 x=Lx/2, y>=0."""
    a = cfg.room.Lx / 2.0
    b = cfg.room.Ly
    cx = cfg.room.Lx / 2.0
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return (y >= 0) & (((x - cx) / a) ** 2 + (y / b) ** 2 <= 1.0)


def make_grid(cfg):
    """spacing 간격 규칙 격자를 바운딩박스에 깔고 반타원 안쪽 점만 (N,3)으로 반환."""
    s = cfg.grid.spacing
    xs = np.arange(s / 2, cfg.room.Lx, s)
    ys = np.arange(s / 2, cfg.room.Ly, s)
    zs = np.arange(s / 2, cfg.room.Lz, s)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    return pts[inside_mask(pts[:, 0], pts[:, 1], cfg)]
