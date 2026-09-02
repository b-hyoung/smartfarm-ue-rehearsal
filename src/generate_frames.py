"""프레임별 CSV(진짜 CFD와 동일 스키마) + manifest.json 생성. CLI: py -m src.generate_frames"""
import json
import os
import numpy as np
import pandas as pd

from src.config import load_config
from src.geometry import make_grid
from src.field_model import temperature, velocity

HEADER = ["x", "y", "z", "T", "Ux", "Uy", "Uz", "p", "source"]


def generate(cfg, out_dir):
    """15프레임(cfg.time) CSV + manifest 를 out_dir 에 쓰고 manifest dict 반환."""
    os.makedirs(out_dir, exist_ok=True)
    pts = make_grid(cfg)
    p = np.zeros(len(pts))
    manifest = {"interval_s": cfg.time.interval_s, "n_points": len(pts), "frames": []}

    for f in range(cfg.time.frames):
        t = f * cfg.time.interval_s
        T = temperature(pts, t, cfg)          # K
        U = velocity(pts, t, cfg)             # (N,3) m/s
        df = pd.DataFrame({
            "x": pts[:, 0], "y": pts[:, 1], "z": pts[:, 2],
            "T": T, "Ux": U[:, 0], "Uy": U[:, 1], "Uz": U[:, 2],
            "p": p, "source": "mock",
        })
        df.to_csv(os.path.join(out_dir, f"frame_{f:02d}.csv"),
                  index=False, float_format="%.4f")
        manifest["frames"].append({
            "frame": f, "t_s": t,
            "T_C_min": float(T.min() - 273.15), "T_C_max": float(T.max() - 273.15),
            "U_mag_max": float(np.linalg.norm(U, axis=1).max()),
        })

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return manifest


def main():
    cfg = load_config("geometry.json")
    m = generate(cfg, os.path.join("data", "frames"))
    print(f"{len(m['frames'])}프레임 · {m['n_points']}점/프레임 → data/frames/")
    for fr in m["frames"]:
        print(f"  frame {fr['frame']:02d}  t={fr['t_s']:>5.0f}s  "
              f"T {fr['T_C_min']:.1f}~{fr['T_C_max']:.1f}C  |U|max {fr['U_mag_max']:.2f}")


if __name__ == "__main__":
    main()
