import numpy as np
from src.field_model import temperature


def test_temperature_t0_is_start_kelvin(tiny_cfg):
    pts = np.array([[4.0, 2.5, 1.1], [0.5, 0.5, 1.1], [7.0, 0.5, 2.0]])
    T = temperature(pts, 0.0, tiny_cfg)
    # t=0 이면 어디나 시작온도(29C = 302.15K)
    assert np.allclose(T, 29.0 + 273.15, atol=1e-6)


def test_temperature_settles_toward_anchors(tiny_cfg):
    # 아주 긴 시간이면 에어컨 축 아래는 ~20C, 먼 벽 쪽은 ~22C 로 수렴
    under_ac = np.array([[4.0, 2.5, 1.5]])   # 에어컨 바로 아래
    far = np.array([[0.3, 0.3, 1.1]])        # 구석(먼 곳)
    T_ac = temperature(under_ac, 100000.0, tiny_cfg)[0] - 273.15
    T_far = temperature(far, 100000.0, tiny_cfg)[0] - 273.15
    assert abs(T_ac - 20.0) < 0.5
    assert abs(T_far - 22.0) < 0.5


def test_temperature_decreases_over_time(tiny_cfg):
    p = np.array([[4.0, 2.5, 1.5]])
    seq = [temperature(p, t, tiny_cfg)[0] for t in (0.0, 60.0, 300.0)]
    assert seq[0] > seq[1] > seq[2]   # 식어감


from src.field_model import velocity


def cfg_u_max(cfg):
    return cfg.flow.u_max


def test_velocity_zero_at_t0(tiny_cfg):
    pts = np.array([[4.0, 2.5, 1.5], [1.0, 1.0, 0.5]])
    U = velocity(pts, 0.0, tiny_cfg)   # 에어컨 켜지기 전 정지
    assert U.shape == (2, 3)
    assert np.allclose(U, 0.0, atol=1e-9)


def test_velocity_develops_and_bounded(tiny_cfg):
    pts = np.array([[4.0, 2.5, 1.5]])   # 에어컨 축 근처
    U = velocity(pts, 300.0, tiny_cfg)
    mag = np.linalg.norm(U, axis=1)[0]
    assert mag > 0.0                       # 시간 지나면 기류 발달
    assert mag <= cfg_u_max(tiny_cfg) * 1.5
    # 에어컨 아래는 하강 성분(음의 z)
    assert U[0, 2] < 0.0
