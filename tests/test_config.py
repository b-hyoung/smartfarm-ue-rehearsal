from src.config import load_config


def test_load_config_reads_values():
    cfg = load_config("geometry.json")
    assert cfg.room.Lx == 8.0
    assert cfg.room.Ly == 5.7
    assert cfg.room.Lz == 2.7
    assert cfg.ac.x == 4.0
    assert cfg.ac.jet_radius == 0.8
    assert cfg.grid.spacing == 0.10
    assert cfg.time.frames == 15
    assert cfg.time.interval_s == 20.0
    assert cfg.temperature_C.start == 29.0
    assert cfg.temperature_C.ac == 20.0
    assert cfg.temperature_C.side == 22.0
    assert cfg.flow.u_max == 0.8
    assert cfg.colormap_C.min == 20.0
