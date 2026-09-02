"""UE 넣기 전 눈검증: z=side_z 수평 단면의 온도 컬러맵 + 기류 화살표 PNG."""
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # 디스플레이 없이 파일로만
import matplotlib.pyplot as plt


def make_preview(cfg, frames_dir, out_dir, frame_indices=None):
    """지정 프레임들의 z≈side_z 단면을 PNG로. 생성된 Path 리스트 반환."""
    os.makedirs(out_dir, exist_ok=True)
    if frame_indices is None:
        n = cfg.time.frames
        frame_indices = sorted({0, n // 2, n - 1})   # 처음/중간/끝
    zsl = cfg.temperature_C.side_z
    paths = []

    for f in frame_indices:
        df = pd.read_csv(os.path.join(frames_dir, f"frame_{f:02d}.csv"))
        band = df[np.abs(df["z"] - zsl) < cfg.grid.spacing]
        fig, ax = plt.subplots(figsize=(7, 5))
        sc = ax.scatter(band["x"], band["y"], c=band["T"] - 273.15,
                        cmap="coolwarm", vmin=cfg.colormap_C.min,
                        vmax=cfg.colormap_C.max, s=10)
        ax.quiver(band["x"], band["y"], band["Ux"], band["Uy"],
                  scale=8, width=0.002, alpha=0.6)
        ax.set_aspect("equal")
        ax.set_title(f"z={zsl}m  frame {f}  t={f * cfg.time.interval_s:.0f}s")
        ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
        fig.colorbar(sc, ax=ax, label="T (C)")
        out = Path(out_dir) / f"slice_z_frame_{f:02d}.png"
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)
        paths.append(out)
    return paths


def main():
    from src.config import load_config
    cfg = load_config("geometry.json")
    paths = make_preview(cfg, os.path.join("data", "frames"),
                         os.path.join("data", "preview"))
    for p_ in paths:
        print(f"  -> {p_}")


if __name__ == "__main__":
    main()
