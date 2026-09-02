from src.generate_frames import generate
from src.preview import make_preview


def test_preview_creates_png(tiny_cfg, tmp_path):
    frames = tmp_path / "frames"
    generate(tiny_cfg, str(frames))
    out = tmp_path / "preview"
    paths = make_preview(tiny_cfg, str(frames), str(out))
    assert len(paths) >= 1
    for p_ in paths:
        assert p_.exists()
        assert p_.stat().st_size > 0
