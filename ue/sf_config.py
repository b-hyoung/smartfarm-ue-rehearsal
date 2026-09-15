"""UE 스크립트 공용 설정 — 하드코딩 금지 구역의 단일 출처.

⚠ 이 모듈은 `unreal` 을 import 하지 않는다 — 에디터 없이(오프라인)도
   import·검증이 가능해야 한다. UE 전용 값은 문자열/숫자로만 둔다.

경로는 전부 이 파일 위치(__file__)에서 파생 — 다른 PC 로 옮겨도 그대로 돈다.
물리·시각화 상수는 geometry.json(리포 루트, 단일 출처)의 "viz" 블록을 읽고,
블록이 없으면 기존 동작과 동일한 기본값을 쓴다.
"""
from __future__ import annotations

import json
import os

# ── 경로 (기계 독립) ──────────────────────────────────────────
UE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(UE_DIR)
DATA_DIR = os.path.join(REPO, "data")
OUT_DIR = os.path.join(REPO, "out")
SHOT_DIR = os.path.join(OUT_DIR, "ue_shots")      # (구) Desktop\smartfarm-cfd\out\ue_shots
ANIM_SHOT_DIR = os.path.join(OUT_DIR, "ue_anim")  # (구) Desktop\smartfarm-cfd\out\ue_anim
GEOMETRY_JSON = os.path.join(REPO, "geometry.json")

# ── UE 에셋 경로 ─────────────────────────────────────────────
MAT_DIR = "/Game/Materials"
VOLUMES_DIR = "/Game/Volumes"
SEQ_DIR = "/Game/Cinematics"
SVT_PATH = VOLUMES_DIR + "/sf_temp"

MAT = {
    "vertex_color":       MAT_DIR + "/M_SF_VertexColor",
    "slice_trans":        MAT_DIR + "/M_SF_SliceTrans",
    "flow_anim":          MAT_DIR + "/M_SF_FlowAnim",
    "curtain_trans":      MAT_DIR + "/M_SF_CurtainTrans",
    "curtain_flow":       MAT_DIR + "/M_SF_CurtainFlow",
    "curtain_flow_blend": MAT_DIR + "/M_SF_CurtainFlowBlend",
    "slice_blend":        MAT_DIR + "/M_SF_SliceBlend",
    "mpc_blend":          MAT_DIR + "/MPC_SF_Blend",
    "volume":             MAT_DIR + "/M_SF_Volume",
    "volume_fog":         MAT_DIR + "/M_SF_VolumeFog",
    "volume_fog2":        MAT_DIR + "/M_SF_VolumeFog2",
}


def _viz():
    try:
        with open(GEOMETRY_JSON, encoding="utf-8") as f:
            return json.load(f).get("viz", {})
    except OSError:
        return {}


_v = _viz()

# ── 색척도 두 벌 (역할이 다르다 — 통일하려면 여기 한 곳만 고친다) ──
# 메시(커튼·카펫) 램프: 20.4~28.9 — §10 에서 데이터 구간에 맞춰 조인 값
RAMP_TMIN = float(_v.get("ramp_t_min", 20.4))
RAMP_TMAX = float(_v.get("ramp_t_max", 28.9))
# VDB/웹 정규화: 18.5~29.0 — vane25 전체(제트 18.9℃ 포함)를 담는 값
VDB_TMIN = float(_v.get("vdb_t_min", 18.5))
VDB_TMAX = float(_v.get("vdb_t_max", 29.0))

# ── 볼륨 안개 전이함수 ───────────────────────────────────────
FOG = {
    "cold_thresh": float(_v.get("fog_cold_thresh", 0.5)),
    "cold_gain":   float(_v.get("fog_cold_gain", 2.5)),
    "base_glow":   float(_v.get("fog_base_glow", 0.35)),
    "cold_glow":   float(_v.get("fog_cold_glow", 2.2)),
    "base_dens":   float(_v.get("fog_base_dens", 0.05)),
    "cold_dens":   float(_v.get("fog_cold_dens", 0.5)),
}

# ── 방·에어컨 (geometry.json room/ac 와 동기) ─────────────────
def room_cm():
    """(Lx, Ly, Lz) cm."""
    try:
        with open(GEOMETRY_JSON, encoding="utf-8") as f:
            r = json.load(f)["room"]
        return r["Lx"] * 100.0, r["Ly"] * 100.0, r["Lz"] * 100.0
    except (OSError, KeyError):
        return 800.0, 570.0, 270.0


AC_CM = (400.0, 200.0, 270.0)   # 4Way 카세트 중심 (CFD 경계와 동일, cm)


def ensure_dirs():
    for d in (SHOT_DIR, ANIM_SHOT_DIR):
        os.makedirs(d, exist_ok=True)
