import json
import pandas as pd
from src.models.generate_frames import generate, HEADER
from src.geometry import make_grid


def test_generate_writes_frames_and_manifest(tiny_cfg, tmp_path):
    out = tmp_path / "frames"
    manifest = generate(tiny_cfg, str(out))
    n_pts = len(make_grid(tiny_cfg))

    # tiny_cfg는 프레임 3개
    files = sorted(out.glob("frame_*.csv"))
    assert [f.name for f in files] == ["frame_00.csv", "frame_01.csv", "frame_02.csv"]
    assert (out / "manifest.json").exists()

    # 스키마 정확 + 행수 = 격자점 수 + source=mock
    df = pd.read_csv(files[0])
    assert list(df.columns) == HEADER
    assert len(df) == n_pts
    assert (df["source"] == "mock").all()

    # manifest 내용
    m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert len(m["frames"]) == 3
    assert m["frames"][0]["t_s"] == 0.0
    assert m["frames"][1]["t_s"] == tiny_cfg.time.interval_s
    assert m["n_points"] == n_pts


def test_header_is_exact_contract():
    # 진짜 CFD export와 반드시 동일해야 함
    assert HEADER == ["x", "y", "z", "T", "Ux", "Uy", "Uz", "p", "source"]
