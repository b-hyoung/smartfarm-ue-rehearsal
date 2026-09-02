import numpy as np
from src.geometry import inside_mask, make_grid


def test_inside_mask_shape(tiny_cfg):
    # 곡면 벽 중앙 근처(4.0, 5.0)는 안, 방 밖(4.0, 6.0)은 밖, 모서리(0.1,3.0)는 밖(반타원 밖)
    x = np.array([4.0, 4.0, 0.1])
    y = np.array([5.0, 6.0, 3.0])
    m = inside_mask(x, y, tiny_cfg)
    assert m.tolist() == [True, False, False]


def test_make_grid_inside_and_bounded(tiny_cfg):
    pts = make_grid(tiny_cfg)
    assert pts.shape[1] == 3
    assert len(pts) > 0
    # 모든 점이 방 안(반타원) + z 범위 안
    assert inside_mask(pts[:, 0], pts[:, 1], tiny_cfg).all()
    assert (pts[:, 2] > 0).all() and (pts[:, 2] < tiny_cfg.room.Lz).all()
    assert (pts[:, 1] >= 0).all()
