# UE 리허설 가짜 CFD 생성기 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 반원 800×570×270cm 공간에 가짜 5분 냉각 데이터(15프레임 CSV)를 파이썬 계산식으로 생성하고, matplotlib로 눈검증하고, UE(Niagara) 반입 가이드를 남긴다.

**Architecture:** 모든 값은 `geometry.json`(단일 출처)에 두고 코드는 그것을 읽는다(실데이터 오면 값만 교체). `config.py`가 config를 로드, `geometry.py`가 반원 격자를 만들고, `field_model.py`가 시간별 온도(K)·기류(m/s)를 계산식으로 채우고, `generate_frames.py`가 프레임별 CSV+manifest를 쓰고, `preview.py`가 단면 PNG로 검증한다. CSV 스키마는 진짜 OpenFOAM export와 동일(mock→real 교체).

**Tech Stack:** Python 3.11 (`py` 런처 — 이 머신 `python` 깨짐), numpy, pandas, matplotlib(Agg), pytest.

---

## File Structure

```
smartfarm-ue-rehearsal/
  geometry.json              config 단일 출처 (치수·에어컨·격자·시간·온도·기류·컬러맵)
  src/
    __init__.py
    config.py                load_config(path) → 중첩 SimpleNamespace
    geometry.py              inside_mask(), make_grid(cfg) → (N,3) 점
    field_model.py           temperature(pts,t,cfg)→K, velocity(pts,t,cfg)→(N,3)
    generate_frames.py       generate(cfg,out_dir)→manifest, CLI main
    preview.py               make_preview(cfg,frames_dir,out_dir)
  tests/
    __init__.py
    conftest.py              tiny_cfg fixture (성긴 격자로 빠른 테스트)
    test_config.py
    test_geometry.py
    test_field_model.py
    test_generate_frames.py
    test_preview.py
  docs/
    specs/2026-09-03-ue-rehearsal-mock-cfd.md   (기존)
    plans/2026-09-03-ue-rehearsal-mock-cfd.md   (이 문서)
    ue-import-guide.md       (Task 6)
  README.md                  (Task 6)
  data/frames/  data/preview/   (gitignore, 산출물)
```

책임 분리: config(값) / geometry(어디에 점) / field_model(그 점의 물리량) / generate(직렬화) / preview(검증). 각 파일 하나의 책임.

---

## Task 0: 프로젝트 골격 + 의존성 + config

**Files:**
- Create: `geometry.json`, `src/__init__.py`, `tests/__init__.py`, `tests/conftest.py`, `src/config.py`, `tests/test_config.py`

- [ ] **Step 1: 의존성 설치**

Run:
```bash
py -m pip install numpy pandas matplotlib pytest
```
Expected: 4개 패키지 설치됨(이미 있으면 "already satisfied").

- [ ] **Step 2: `geometry.json` 작성 (config 단일 출처)**

Create `geometry.json`:
```json
{
  "room":  { "Lx": 8.0, "Ly": 5.7, "Lz": 2.7, "unit": "m",
             "note": "반원 바운딩박스 800x570x270cm. 직선벽 y=0, 곡면벽 y+ 반타원 근사" },
  "ac":    { "x": 4.0, "y": 2.5, "z": 2.7, "jet_radius": 0.8 },
  "grid":  { "spacing": 0.10 },
  "time":  { "frames": 15, "interval_s": 20.0 },
  "temperature_C": { "start": 29.0, "ac": 20.0, "side": 22.0, "side_z": 1.1,
                     "tau_near_s": 60.0, "tau_far_s": 150.0 },
  "flow":  { "u_max": 0.8, "tau_flow_s": 40.0 },
  "colormap_C": { "min": 20.0, "max": 29.0 }
}
```

- [ ] **Step 3: 빈 패키지 파일**

Create `src/__init__.py` (빈 파일), `tests/__init__.py` (빈 파일).

- [ ] **Step 4: 실패하는 테스트 작성**

Create `tests/test_config.py`:
```python
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
```

- [ ] **Step 5: 테스트 실패 확인**

Run: `py -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.config'`

- [ ] **Step 6: 최소 구현**

Create `src/config.py`:
```python
"""geometry.json(단일 출처)을 중첩 SimpleNamespace로 로드. 값은 전부 여기서만 온다."""
import json
import types


def _ns(d):
    return types.SimpleNamespace(
        **{k: (_ns(v) if isinstance(v, dict) else v) for k, v in d.items()}
    )


def load_config(path="geometry.json"):
    with open(path, encoding="utf-8") as f:
        return _ns(json.load(f))
```

- [ ] **Step 7: 테스트 통과 확인**

Run: `py -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 8: conftest에 성긴 격자 fixture 추가 (이후 테스트 빠르게)**

Create `tests/conftest.py`:
```python
import pytest
from src.config import load_config


@pytest.fixture
def tiny_cfg():
    """실제 geometry.json을 로드하되 격자만 성기게(0.5m) + 프레임 3개로 줄여 테스트를 빠르게."""
    cfg = load_config("geometry.json")
    cfg.grid.spacing = 0.5
    cfg.time.frames = 3
    return cfg
```

- [ ] **Step 9: 커밋**

```bash
git add geometry.json src/ tests/
git commit -m "feat: config 로더 + geometry.json 단일 출처"
```

---

## Task 1: 반원 격자 (geometry.py)

**Files:**
- Create: `src/geometry.py`, `tests/test_geometry.py`

- [ ] **Step 1: 실패하는 테스트 작성**

Create `tests/test_geometry.py`:
```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `py -m pytest tests/test_geometry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.geometry'`

- [ ] **Step 3: 최소 구현**

Create `src/geometry.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `py -m pytest tests/test_geometry.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/geometry.py tests/test_geometry.py
git commit -m "feat: 반원(반타원) 격자 생성"
```

---

## Task 2: 온도 모델 (field_model.temperature)

**Files:**
- Create: `src/field_model.py`, `tests/test_field_model.py`

- [ ] **Step 1: 실패하는 테스트 작성**

Create `tests/test_field_model.py`:
```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `py -m pytest tests/test_field_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.field_model'`

- [ ] **Step 3: 최소 구현**

Create `src/field_model.py`:
```python
"""반원 공간의 시간별 온도(K)·기류(m/s)를 계산식으로 채운다(솔버 없음).

물리 정확이 아니라 '그럴듯함'이 목적 — UE 파이프 리허설용. 모든 상수는 cfg에서.
"""
import numpy as np

_EPS = 1e-6


def _horizontal_r(pts, cfg):
    dx = pts[:, 0] - cfg.ac.x
    dy = pts[:, 1] - cfg.ac.y
    return np.sqrt(dx * dx + dy * dy)


def temperature(pts, t, cfg):
    """(N,3) 점의 시각 t(s) 온도를 켈빈으로. t=0이면 start 균일, t→∞면 앵커 패턴."""
    tc = cfg.temperature_C
    r = _horizontal_r(pts, cfg)
    r_ref = cfg.room.Lx / 2.0
    s = np.clip(r / r_ref, 0.0, 1.0)               # 0=에어컨축, 1=먼 곳
    T_inf = tc.ac + (tc.side - tc.ac) * s           # 20C(축) → 22C(벽)
    tau = tc.tau_near_s + (tc.tau_far_s - tc.tau_near_s) * s
    T_C = T_inf + (tc.start - T_inf) * np.exp(-t / tau)
    return T_C + 273.15
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `py -m pytest tests/test_field_model.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/field_model.py tests/test_field_model.py
git commit -m "feat: 온도 모델(과도 냉각, 앵커 20/22C)"
```

---

## Task 3: 기류 모델 (field_model.velocity)

**Files:**
- Modify: `src/field_model.py` (velocity 추가)
- Modify: `tests/test_field_model.py` (velocity 테스트 추가)

- [ ] **Step 1: 실패하는 테스트 추가**

Append to `tests/test_field_model.py`:
```python
from src.field_model import velocity


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


def cfg_u_max(cfg):
    return cfg.flow.u_max
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `py -m pytest tests/test_field_model.py -v`
Expected: FAIL — `ImportError: cannot import name 'velocity'`

- [ ] **Step 3: velocity 구현 추가**

Append to `src/field_model.py`:
```python
def velocity(pts, t, cfg):
    """(N,3) 기류(m/s). 에어컨 하강제트→바닥 방사확산→벽쪽 상승. t로 램프업."""
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    dx = x - cfg.ac.x
    dy = y - cfg.ac.y
    r = np.sqrt(dx * dx + dy * dy)
    core = np.exp(-((r / cfg.ac.jet_radius) ** 2))     # 에어컨 축 근처일수록 1
    zf = z / cfg.room.Lz                                # 0=바닥, 1=천장
    umax = cfg.flow.u_max

    w = -umax * core * zf                               # 축 아래 하강(음의 z), 위에서 강
    radial = umax * core * (1.0 - zf) * 0.7             # 바닥 근처 방사 확산
    ux = radial * dx / np.maximum(r, _EPS)
    uy = radial * dy / np.maximum(r, _EPS)

    r_ref = cfg.room.Lx / 2.0
    wall = np.clip(r / r_ref, 0.0, 1.0)
    w = w + umax * 0.3 * wall * (1.0 - zf)              # 벽 쪽 완만한 상승(재순환)

    U = np.stack([ux, uy, w], axis=1)
    ramp = 1.0 - np.exp(-t / cfg.flow.tau_flow_s)       # 에어컨 켜지며 발달
    return U * ramp
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `py -m pytest tests/test_field_model.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/field_model.py tests/test_field_model.py
git commit -m "feat: 기류 모델(하강제트+방사+상승, 시간 램프)"
```

---

## Task 4: 프레임 생성기 (generate_frames.py)

**Files:**
- Create: `src/generate_frames.py`, `tests/test_generate_frames.py`

- [ ] **Step 1: 실패하는 테스트 작성**

Create `tests/test_generate_frames.py`:
```python
import json
import pandas as pd
from src.generate_frames import generate, HEADER
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `py -m pytest tests/test_generate_frames.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.generate_frames'`

- [ ] **Step 3: 최소 구현**

Create `src/generate_frames.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `py -m pytest tests/test_generate_frames.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/generate_frames.py tests/test_generate_frames.py
git commit -m "feat: 프레임별 CSV+manifest 생성기(스키마=진짜 CFD)"
```

---

## Task 5: 눈검증 미리보기 (preview.py)

**Files:**
- Create: `src/preview.py`, `tests/test_preview.py`

- [ ] **Step 1: 실패하는 테스트 작성**

Create `tests/test_preview.py`:
```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `py -m pytest tests/test_preview.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.preview'`

- [ ] **Step 3: 최소 구현**

Create `src/preview.py`:
```python
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
        fig.colorbar(sc, ax=ax, label="T (°C)")
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
        print(f"  → {p_}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `py -m pytest tests/test_preview.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: 전체 테스트 확인**

Run: `py -m pytest -v`
Expected: 모든 테스트 PASS (config 1, geometry 2, field 5, generate 2, preview 1 = 11)

- [ ] **Step 6: 커밋**

```bash
git add src/preview.py tests/test_preview.py
git commit -m "feat: 단면 미리보기(온도 컬러맵+기류 화살표)"
```

---

## Task 6: 문서 — UE 반입 가이드 + README

**Files:**
- Create: `docs/ue-import-guide.md`, `README.md`

- [ ] **Step 1: UE 반입 가이드 작성**

Create `docs/ue-import-guide.md`:
```markdown
# CSV → 언리얼(Niagara) 반입 가이드

`data/frames/frame_00.csv … frame_14.csv` 를 언리얼에서 "온도색 기류"로 그리는 절차.
CSV는 순수 SI(m, K) — 아래 변환은 UE 쪽에서 적용한다.

## 변환 규칙
- 위치: `x,y,z (m) × 100 = cm` (UE 기본 단위)
- 온도: `T_C = T_K − 273.15`
- 좌표 매핑: CFD(X=직선벽 따라, Y=방 안쪽, Z=위) → UE(X, Y, Z-up).
  UE는 왼손 좌표라 필요하면 Y 부호를 뒤집는다(임포트 후 방향이 좌우 반전이면 Y*-1).
- 컬러맵: 고정 범위 **20~29 ℃**(프레임 간 색 비교 가능), 파랑(차가움)→빨강(더움).

## Niagara 절차 (개요)
1. 각 `frame_XX.csv`를 데이터로 읽는다(Data Table 임포트 또는 CSV 파싱).
2. 행마다 파티클 스폰: 위치=(x,y,z)×100, 속도=(Ux,Uy,Uz), 색=컬러맵(T_C).
3. 점이 많으면(수만) **다운샘플**(예: 3칸마다 1점)하거나 텍스처로 베이크.
   - 구체 방식은 UE 버전 확인 후 결정.
4. 타임라인: 프레임 0→14 를 원하는 재생속도로 진행 → 냉각·기류 발달 애니메이션.

## mock → real 교체
진짜 프로젝트 머신의 OpenFOAM 5분 transient 를 타임스텝별로 같은 스키마
(`x,y,z,T,Ux,Uy,Uz,p,source`) CSV 로 export 해 `data/frames/` 를 교체하면
UE 쪽은 한 줄도 안 고친다. `source` 만 `mock→simulated` 로 바뀐다.
```

- [ ] **Step 2: README 작성**

Create `README.md`:
```markdown
# smartfarm-ue-rehearsal

반원 800×570×270cm 공간의 **가짜 5분 냉각 데이터**를 만들어, 진짜 CFD 데이터가
오기 전에 언리얼(Niagara) "온도색 기류" 시각화 파이프를 리허설한다.

- 설계(spec): `docs/specs/2026-09-03-ue-rehearsal-mock-cfd.md`
- 계획(plan): `docs/plans/2026-09-03-ue-rehearsal-mock-cfd.md`
- UE 반입: `docs/ue-import-guide.md`
- 모든 값: `geometry.json` (실데이터 오면 값만 교체, 코드 불변)

## 실행 (이 머신은 `python` 깨져 `py` 사용)
```bash
py -m pip install numpy pandas matplotlib pytest
py -m pytest -v                    # 테스트
py -m src.generate_frames         # data/frames/ 에 15프레임 CSV + manifest
py -m src.preview                 # data/preview/ 에 단면 PNG
```

## 산출물
- `data/frames/frame_00..14.csv` — 스키마 `x,y,z,T,Ux,Uy,Uz,p,source` (진짜 CFD와 동일)
- `data/frames/manifest.json` — 프레임별 시각·온도·기류 범위
- `data/preview/slice_z_frame_*.png` — 눈검증
```

- [ ] **Step 3: 커밋**

```bash
git add docs/ue-import-guide.md README.md
git commit -m "docs: UE 반입 가이드 + README"
```

---

## Task 7: 엔드투엔드 실행 + 눈검증

**Files:** (없음 — 실제 실행)

- [ ] **Step 1: 생성기 실행**

Run: `py -m src.generate_frames`
Expected: `15프레임 · <N>점/프레임 → data/frames/` 와 프레임별 요약. frame 00은 T 29.0~29.0C, |U|max 0.00; 뒤 프레임일수록 T 하한이 20C대로 내려가고 |U|max 증가.

- [ ] **Step 2: 미리보기 실행**

Run: `py -m src.preview`
Expected: `data/preview/slice_z_frame_00.png`, `_07.png`, `_14.png` 생성.

- [ ] **Step 3: 눈검증 (사람 확인)**

frame_00 → 온통 29℃(빨강)·화살표 없음. frame_14 → 에어컨 아래가 파랑(20℃대)로 식고 기류 화살표가 하강·확산. 이게 보이면 리허설 데이터 OK. (SendUserFile로 PNG를 사용자에게 보내 확인받는다.)

- [ ] **Step 4: manifest 확인**

Run: `py -c "import json;m=json.load(open('data/frames/manifest.json',encoding='utf-8'));print(m['n_points'],'점');print(m['frames'][0]['T_C_max'], m['frames'][-1]['T_C_min'])"`
Expected: 점 수 출력, frame0 T_C_max≈29.0, frame14 T_C_min≈20.x

- [ ] **Step 5: 커밋 (manifest 요약이 있으면)**

```bash
git add -A
git commit -m "chore: 엔드투엔드 리허설 실행 확인" --allow-empty
```

---

## Self-Review 결과

- **Spec coverage:** §2 공간→Task1, §3 시간→geometry.json/Task0, §4 CSV계약→Task4(HEADER 테스트), §5.1 온도→Task2, §5.2 기류→Task3, §5.4 config주도→Task0(geometry.json)+전 모듈이 cfg 읽음, §6 UE가이드→Task6, §7 검증→Task5·7, §8 mock→real→Task6 가이드+HEADER 고정, §9 폴더→파일구조. 누락 없음.
- **Placeholder scan:** 모든 코드 스텝에 실제 코드 있음. TBD/TODO 없음.
- **Type consistency:** `HEADER`(generate_frames) = test와 동일. `temperature`/`velocity` 시그니처 `(pts,t,cfg)` 일관. `make_grid(cfg)`/`inside_mask(x,y,cfg)`/`load_config(path)` 호출부 일치. cfg 경로명(`cfg.temperature_C.*`, `cfg.ac.*`, `cfg.flow.*`, `cfg.room.*`, `cfg.grid.spacing`, `cfg.time.*`) geometry.json 키와 일치.
```
