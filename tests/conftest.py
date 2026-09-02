import pytest
from src.config import load_config


@pytest.fixture
def tiny_cfg():
    """실제 geometry.json을 로드하되 격자만 성기게(0.5m) + 프레임 3개로 줄여 테스트를 빠르게."""
    cfg = load_config("geometry.json")
    cfg.grid.spacing = 0.5
    cfg.time.frames = 3
    return cfg
