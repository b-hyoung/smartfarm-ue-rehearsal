"""팬 조건 RANS-PINN — 「팬 네 대 풍량 → 캐노피 기류장」 + 최소 전력 탐색.

방법은 새로 만든 것이 아니라 아래 논문의 정식화를 그대로 따른다.

  [1] Ghosh, Chakraborty, Brikis, Dey (Siemens Technology),
      "RANS-PINN based Simulation Surrogates for Predicting Turbulent Flows",
      ICML 2023 Workshop SynS & ML, arXiv:2306.06034
  [2] 같은 계열 확장, "Using Parametric PINNs for Predicting Internal and External
      Turbulent Flows", arXiv:2410.18917
      - 매개변수형 PINN: 좌표에 운전 조건(논문은 레이놀즈 수)을 입력으로 더한다
      - 변수마다 따로 둔 신경망: u, v, (w), p, k, ε
      - 물리 손실: 연속식 + RANS 운동량 + 표준 k-ε 두 식
        C1 = 1.44, C2 = 1.92, σk = 1.0, σε = 1.3, νt = Cμ k²/ε (Cμ = 0.09)
      - 2 단계 학습: 데이터 손실만으로 예열(warm start) → 물리 손실을 더해 학습
      - ε 는 로그 손실 / Adam, 학습률 0.001 에서 지수 감쇠(0.95)
  [3] Raissi, Perdikaris, Karniadakis, J. Comput. Phys. 378 (2019) — PINN 원전
  [4] Raissi, Yazdani, Karniadakis, Science 367 (2020) "Hidden fluid mechanics"
      — 관측되지 않은 변수(여기서는 p, k, ε)를 지배방정식만으로 함께 추론
  [5] 다공체 항: OpenFOAM explicitPorositySource DarcyForchheimer — 우리 CFD 가 쓴 그 식.
      PINN 에 Darcy–Forchheimer 항을 넣은 예: "Darcy–Brinkman–Forchheimer physics-informed
      neural networks…", Physics of Fluids 37(9) 093626 (2025).
      계수 d = 25 1/m², f = 1.3 1/m 는 Zhang 외 (2025) Agronomy 15:2326 (fan_params.json canopy)

우리 문제에 맞춘 것 (논문과 다른 점 — 전부 여기에 적는다)
  · 매개변수 = 레이놀즈 수 하나 대신 팬 네 대 풍량 q (아래 송풍, 아래 흡입, 위 송풍, 위 흡입) CMM
  · 3 차원 (w 추가). 우리 CFD 가 푼 식과 같게 하려고 운동량에 두 항을 더했다:
      캐노피 다공체 저항  −(ν d + ½ f |U|) U   (캐노피 상자 안에서만)
      부력 (Boussinesq)   + g β (T − T_ref) ẑ,  β = 1/T_ref (이상기체)
    T 는 데이터로만 맞추고 에너지 식은 풀지 않는다. k 의 부력 생성항은 뺐다.
  · 데이터는 속도·온도뿐이다(판정면 4 장 시간평균). CFD 가 k, ε, p 를 저장하지 않아
    이 셋은 [4] 처럼 물리 손실만으로 추론된다. 그래서 k, ε 는 로그 값을 출력해 양수를 보장한다.
  · 물리 손실 점은 캐노피 부피(베드 위)에서, 조건은 학습 케이스와 그 사이 임의 조건을 섞어 뽑는다.
  · 손실 가중치: 각 물리 손실을 예열 직후 크기로 나눠 1 근처에서 시작하게 한다([1] 의 잔차 기반 가중).

탐색
  팬마다 「끔 또는 6.5~12 CMM」(오리엔탈모터 EMR2090VMH-A 최저속 6.5, 학습 데이터 상한 12)을
  0.5 간격으로 전부 넣어, 두 단 모두 적정 면적(0.3~1.0 m/s) ≥ 75 % 이고 P10 ≥ 0.28 m/s 인 조합 중
  팬 전력이 가장 작은 것을 찾는다. 전력은 EMR2090VMH-A 공식 수치를 선형 보간한다.

실행
  py -m src.ml.fan_pinn --holdout 06_F4,13_S5            빼 둔 케이스로 일반화 검증
  py -m src.ml.fan_pinn --holdout 06_F4,13_S5 --physics none   비교용 (데이터만)
  py -m src.ml.fan_pinn                                   13 케이스 전부 학습 → 최소 전력 탐색
출력  data/fan_pinn/*.json (커밋)   out/fan_pinn/*.pt (가중치, 커밋 안 함)
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import itertools
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DS = os.path.join(REPO, "data", "fan-dataset")
OUT_DIR = os.path.join(REPO, "data", "fan_pinn")
OUT_PT = os.path.join(REPO, "out", "fan_pinn")
DEV = "cuda" if torch.cuda.is_available() else "cpu"

FANS = ["cmm_T0_S", "cmm_T0_R", "cmm_T1_S", "cmm_T1_R"]
PLANES = ["tier0_canopy_mid", "tier0_canopy_top", "tier1_canopy_mid", "tier1_canopy_top"]
JUDGE = ["tier0_canopy_mid", "tier1_canopy_mid"]
BAND, P10_MIN, BAND_MIN = (0.3, 1.0), 0.28, 0.75
Q_MAX = 12.0

# 우리 CFD 설정 (cfd/template/acRoom-vane25, data/fan_params.json)
MU, RHO = 1.8e-5, 1.17                     # thermophysicalProperties: mu 1.8e-5, perfectGas ≈ 300 K
NU = MU / RHO
T_REF = 25.0                               # ℃, Boussinesq 기준 (β = 1/(T_REF + 273.15))
G = 9.81
D_POR, F_POR = 25.0, 1.3                   # DarcyForchheimer d (1/m²), f (1/m)
CANOPY = [(0.55, 0.80), (1.35, 1.60)]      # 캐노피 다공체 z 범위 (베드 위 x ±1.2, y 1.6~2.4)
BOXES = [((-1.2, 1.2), (1.6, 2.4), (0.60, 0.85)), ((-1.2, 1.2), (1.6, 2.4), (1.40, 1.65))]
# 표준 k-ε 상수 [1]
C_MU, C1, C2, SIG_K, SIG_E = 0.09, 1.44, 1.92, 1.0, 1.3

# 오리엔탈모터 EMR2090VMH-A — inaom.co.kr 제품 사양(6.5 · 20.1)과 시리즈 표(9.8 · 15.1)
EMR = [(6.5, 8.9), (9.8, 19.0), (15.1, 50.0), (20.1, 113.0)]
LEVELS = [0.0] + [6.5 + 0.5 * i for i in range(12)]          # 끔, 6.5 ~ 12.0


def fan_watt(q):
    """대당 전력 W. 끔 0 W, 6.5~20.1 CMM 은 공식 수치 사이 선형 보간."""
    q = np.asarray(q, dtype=float)
    xs, ys = zip(*EMR)
    return np.where(q <= 0, 0.0, np.interp(q, xs, ys))


# ---------------------------------------------------------------- 데이터

def load_cases():
    with io.open(os.path.join(DS, "current_subset.csv"), encoding="utf-8") as f:
        return [(r["run_id"], [float(r[k]) for k in FANS]) for r in csv.DictReader(f)]


def mean_field(rid):
    """판정면 4장의 점별 시간평균 (judge.py 와 같은 방식: 벡터를 평균한 뒤 크기)."""
    acc = collections.defaultdict(list)
    with io.open(os.path.join(DS, "fields", rid + ".csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["plane"] in PLANES and r["in_bed"] == "1" and r["in_window"] == "1":
                acc[(r["plane"], r["x_m"], r["y_m"], r["z_m"])].append(
                    (float(r["Ux"]), float(r["Uy"]), float(r["Uz"]), float(r["T_K"] or "nan")))
    out = {p: [] for p in PLANES}
    for (pl, x, y, z), v in acc.items():
        m = np.nanmean(np.array(v), axis=0)
        out[pl].append([float(x), float(y), float(z), m[0], m[1], m[2], m[3] - 273.15])
    return {p: np.array(v) for p, v in out.items()}


KEPS = os.path.join(DS, "keps")
TURB_W = 1.0                               # 난류량 데이터 손실 가중 (0.01 은 k 를 못 붙잡았다)


def mean_keps(rid):
    """data/fan-dataset/keps/<rid>.csv (src/extract_keps.py) 의 점별 시간평균 k, ε, p_rgh.
    없으면 None. p_rgh 는 기준값이 임의라 케이스 평균을 뺀다."""
    path = os.path.join(KEPS, rid + ".csv")
    if not os.path.exists(path):
        return None
    acc = collections.defaultdict(list)
    with io.open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["plane"], round(float(r["x_m"]), 4), round(float(r["y_m"]), 4), round(float(r["z_m"]), 4))
            acc[key].append((float(r["k"]), float(r["epsilon"]), float(r["p_rgh"])))
    out = {k: np.mean(np.array(v), axis=0) for k, v in acc.items()}
    pm = np.mean([v[2] for v in out.values()])
    return {k: (v[0], v[1], v[2] - pm) for k, v in out.items()}


# ---------------------------------------------------------------- 모델 [1][2]: 변수마다 따로 둔 신경망

def mlp(width=128, depth=5):
    layers, d = [], 7
    for _ in range(depth):
        layers += [nn.Linear(d, width), nn.SiLU()]
        d = width
    layers.append(nn.Linear(d, 1))
    return nn.Sequential(*layers)


class RansPINN(nn.Module):
    VARS = ["u", "v", "w", "p", "logk", "loge", "T"]

    def __init__(self):
        super().__init__()
        self.nets = nn.ModuleDict({k: mlp() for k in self.VARS})

    def forward(self, xyz, q):
        x = xyz[:, 0:1] / 1.2
        y = (xyz[:, 1:2] - 2.0) / 0.4
        z = (xyz[:, 2:3] - 1.1) / 0.5
        h = torch.cat([x, y, z, q / Q_MAX], 1)
        o = {k: n(h) for k, n in self.nets.items()}
        o["k"] = torch.exp(o["logk"] - 5.0)                       # 초기값 ≈ 0.007 m²/s²
        o["e"] = torch.exp(o["loge"] - 5.0)                       # 초기값 ≈ 0.007 m²/s³
        o["T"] = T_REF + 2.0 * o["T"]
        return o


def grad(f, x):
    return torch.autograd.grad(f, x, torch.ones_like(f), create_graph=True)[0]


def residuals(m, xyz, q):
    """정상 RANS + 표준 k-ε 잔차 [1] + 다공체·부력 [5]. 모두 SI 단위."""
    o = m(xyz, q)
    U = [o["u"], o["v"], o["w"]]
    k, e, p, T = o["k"], o["e"], o["p"], o["T"]
    nut = C_MU * k * k / (e + 1e-9)
    gU = [grad(Ui, xyz) for Ui in U]                              # gU[i][:, j] = ∂Ui/∂xj
    gp = grad(p, xyz)
    gk, ge = grad(k, xyz), grad(e, xyz)
    gnut = grad(nut, xyz)
    cont = gU[0][:, 0:1] + gU[1][:, 1:2] + gU[2][:, 2:3]
    # 생성항 Pk = νt · 2 S:S
    S2 = 0.0
    for i in range(3):
        for j in range(3):
            sij = 0.5 * (gU[i][:, j:j + 1] + gU[j][:, i:i + 1])
            S2 = S2 + 2.0 * sij * sij
    Pk = nut * S2
    umag = torch.sqrt(U[0] ** 2 + U[1] ** 2 + U[2] ** 2 + 1e-12)
    zc = xyz[:, 2:3]
    in_can = ((zc >= CANOPY[0][0]) & (zc <= CANOPY[0][1])) | ((zc >= CANOPY[1][0]) & (zc <= CANOPY[1][1]))
    por = in_can.float() * (NU * D_POR + 0.5 * F_POR * umag)
    beta = 1.0 / (T_REF + 273.15)
    mom = []
    for i in range(3):
        adv = sum(U[j] * gU[i][:, j:j + 1] for j in range(3))
        # ∇·[(ν+νt)(∇U + ∇Uᵀ)]_i = (ν+νt) ∇²Ui + ∂j νt (∂j Ui + ∂i Uj)   (∇·U = 0 이용)
        lap = sum(grad(gU[i][:, j:j + 1], xyz)[:, j:j + 1] for j in range(3))
        cross = sum(gnut[:, j:j + 1] * (gU[i][:, j:j + 1] + gU[j][:, i:i + 1]) for j in range(3))
        r = adv + gp[:, i:i + 1] / RHO - (NU + nut) * lap - cross + por * U[i]
        if i == 2:
            r = r - G * beta * (T - T_REF)
        mom.append(r)
    def transport(phi, gphi, sig):
        adv = sum(U[j] * gphi[:, j:j + 1] for j in range(3))
        D = NU + nut / sig
        dif = sum(grad(D * gphi[:, j:j + 1], xyz)[:, j:j + 1] for j in range(3))
        return adv - dif
    rk = transport(k, gk, SIG_K) - Pk + e
    re_ = transport(e, ge, SIG_E) - (C1 * Pk - C2 * e) * e / (k + 1e-9)
    return {"cont": cont, "mom": torch.cat(mom, 1), "k": rk, "e": re_ / (e + 1e-6)}


def sample_q(n, train_q, rng):
    """물리 손실용 조건: 절반은 학습 케이스, 절반은 그 사이 임의 조건(팬마다 30 % 끔)."""
    k = n // 2
    a = train_q[rng.integers(0, len(train_q), k)]
    b = rng.uniform(3.6, Q_MAX, (n - k, 4)) * (rng.random((n - k, 4)) > 0.3)
    return np.vstack([a, b])


def sample_xyz(n, rng):
    out = []
    for i in range(n):
        (x0, x1), (y0, y1), (z0, z1) = BOXES[i % 2]
        out.append([rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(z0, z1)])
    return np.array(out)


def train_one(data, seed, warm, iters, physics, n_col, log=False):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    T = lambda a: torch.tensor(np.vstack(a), dtype=torch.float32, device=DEV)
    xyz, q = T([d[0] for d in data]), T([d[1] for d in data])
    u, t = T([d[2] for d in data]), T([d[3] for d in data])
    tok = ~torch.isnan(t)
    tb = T([d[5] for d in data])
    cid = torch.tensor(np.concatenate([d[6] for d in data]), dtype=torch.long, device=DEV)
    kok = ~torch.isnan(tb[:, 0])
    has_turb = bool(kok.any())
    if has_turb:
        kd, ed, pd_ = tb[kok, 0:1], tb[kok, 1:2], tb[kok, 2:3]
        sk, sp = (kd ** 2).mean().item(), (pd_ ** 2).mean().item()
        cidk = cid[kok]
        ncase = int(cid.max().item()) + 1
    train_q = np.array(sorted({tuple(d[4]) for d in data}))
    m = RansPINN().to(DEV)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    # [1]: 학습률 0.001 에서 지수 감쇠 0.95 (여기서는 전체 반복에 걸쳐 0.95 를 약 60 번)
    total = warm + iters                                          # none 도 같은 반복 수(공정 비교)
    sch = torch.optim.lr_scheduler.ExponentialLR(opt, 0.95 ** (60.0 / max(total, 1)))
    w = None
    for it in range(total):
        o = m(xyz, q)
        pu = torch.cat([o["u"], o["v"], o["w"]], 1)
        l_u = ((pu - u) ** 2).mean()
        l_t = ((o["T"] - t)[tok] ** 2).mean() * 0.01
        loss = l_u + l_t
        lt = {}
        if has_turb:                                              # 난류량 데이터 [1]
            pk = o["k"][kok]
            pe = o["e"][kok]
            pp = o["p"][kok]
            # 압력은 케이스마다 기준이 임의 → 예측도 케이스 평균을 빼고 비교
            sums = torch.zeros(ncase, 1, device=DEV).index_add_(0, cidk, pp)
            cnt = torch.zeros(ncase, 1, device=DEV).index_add_(0, cidk, torch.ones_like(pp))
            pp = pp - (sums / cnt.clamp(min=1))[cidk]
            lt = {"kd": ((pk - kd) ** 2).mean() / sk,
                  "ed": ((torch.log(pe) - torch.log(ed)) ** 2).mean(),
                  "pd": ((pp - pd_) ** 2).mean() / sp}
            loss = loss + TURB_W * sum(lt.values())                 # [1]: 데이터 손실끼리 같은 무게
        lp = {}
        if it >= warm and physics == "rans":                      # 2 단계: 물리 손실 추가
            c = torch.tensor(sample_xyz(n_col, rng), dtype=torch.float32, device=DEV,
                             requires_grad=True)
            cq = torch.tensor(sample_q(n_col, train_q, rng), dtype=torch.float32, device=DEV)
            r = residuals(m, c, cq)
            lp = {k: (v ** 2).mean() for k, v in r.items()}
            if w is None:                                         # 잔차 기반 가중 [1]: 단계 시작 크기로 나눔
                w = {k: 1.0 / max(v.item(), 1e-8) for k, v in lp.items()}
                w["data"] = 1.0 / max(loss.item(), 1e-8)
            loss = w["data"] * loss + sum(w[k] * lp[k] for k in lp)
        opt.zero_grad()
        loss.backward()
        opt.step()
        sch.step()
        if log and (it % 1000 == 0 or it == total - 1 or it == warm):
            print("   it %5d  data %.5f  T %.4f  %s" % (it, l_u.item(), l_t.item(),
                  "  ".join("%s %.2e" % (k, v.item()) for k, v in list(lt.items()) + list(lp.items()))),
                  flush=True)
    return m.eval()


# ---------------------------------------------------------------- 판정

@torch.no_grad()
def predict_stats(models, grid, qs, batch=256):
    """qs (N,4) 마다 두 판정면의 적정 면적·P10 — 앙상블 평균과 편차, 평균 기온."""
    g = [torch.tensor(grid[p], dtype=torch.float32, device=DEV) for p in JUDGE]
    n_pt = [len(x) for x in g]
    gg = torch.cat(g)
    res = np.zeros((len(models), len(qs), 2, 2))
    tmean = np.zeros((len(models), len(qs), 2))
    for mi, m in enumerate(models):
        for s in range(0, len(qs), batch):
            qb = torch.tensor(qs[s:s + batch], dtype=torch.float32, device=DEV)
            nb = len(qb)
            o = m(gg.repeat(nb, 1), qb.repeat_interleave(len(gg), 0))
            mag = torch.sqrt(o["u"] ** 2 + o["v"] ** 2 + o["w"] ** 2).view(nb, -1)
            tt = o["T"].view(nb, -1)
            ofs = 0
            for ti, n in enumerate(n_pt):
                mm = mag[:, ofs:ofs + n]
                res[mi, s:s + nb, ti, 0] = ((mm >= BAND[0]) & (mm <= BAND[1])).float().mean(1).cpu()
                res[mi, s:s + nb, ti, 1] = torch.quantile(mm, 0.10, dim=1).cpu()
                tmean[mi, s:s + nb, ti] = tt[:, ofs:ofs + n].mean(1).cpu()
                ofs += n
    return res.mean(0), res.std(0), tmean.mean(0)


def build(cases, fields, keps=None):
    """점마다 (좌표, 조건, 속도, 온도, 조건, [k, ε, p'] 또는 NaN, 케이스 번호)."""
    data = []
    for ci, (rid, q) in enumerate(cases):
        kp = (keps or {}).get(rid)
        for p in PLANES:
            a = fields[rid][p]
            tb = np.full((len(a), 3), np.nan)
            if kp:
                for i, (x, y, z) in enumerate(a[:, 0:3]):
                    v = kp.get((p, round(x, 4), round(y, 4), round(z, 4)))
                    if v is not None:
                        tb[i] = v
            data.append((a[:, 0:3], np.tile(q, (len(a), 1)), a[:, 3:6], a[:, 6:7], q, tb,
                         np.full(len(a), ci)))
    return data


def truth_stats(fields, rid):
    out = {}
    for ti, p in enumerate(JUDGE):
        a = fields[rid][p]
        mag = np.linalg.norm(a[:, 3:6], axis=1)
        out["t%d" % ti] = {"band": float(np.mean((mag >= BAND[0]) & (mag <= BAND[1]))),
                           "P10": float(np.percentile(mag, 10)), "T": float(np.nanmean(a[:, 6]))}
    return out


def ok(res):
    return bool(np.all(res[:, 0] >= BAND_MIN) and np.all(res[:, 1] >= P10_MIN))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", default="", help="쉼표로 구분한 run_id — 학습에서 빼고 검증")
    ap.add_argument("--physics", default="rans", choices=["rans", "none"])
    ap.add_argument("--warm", type=int, default=2000, help="데이터만으로 예열하는 반복 [1]")
    ap.add_argument("--iters", type=int, default=6000, help="물리 손실을 더한 반복")
    ap.add_argument("--col", type=int, default=2048, help="반복마다 물리 손실 점 수")
    ap.add_argument("--ens", type=int, default=5)
    ap.add_argument("--no-turb-data", action="store_true", help="k·ε·p 데이터를 쓰지 않음 (비교용)")
    ap.add_argument("--turb-w", type=float, default=1.0, help="난류량 데이터 손실 가중")
    ap.add_argument("--load", default="", help="학습하지 않고 out/fan_pinn/<이름>_*.pt 를 불러 탐색만")
    a = ap.parse_args()
    global TURB_W
    TURB_W = a.turb_w

    cases = load_cases()
    fields = {rid: mean_field(rid) for rid, _ in cases}
    keps = {} if a.no_turb_data else {rid: v for rid, _ in cases if (v := mean_keps(rid))}
    hold = [h for h in a.holdout.split(",") if h]
    train = [c for c in cases if c[0] not in hold]
    grid = {p: fields["05_F3"][p][:, 0:3] for p in JUDGE}         # 판정점 배치 (전 케이스 공통)
    print("학습 %d 케이스, 검증 %s, 물리 %s, 예열 %d + %d, 앙상블 %d, 난류 데이터 %s, %s" % (
        len(train), hold or "없음", a.physics, a.warm, a.iters, a.ens,
        sorted(k for k in keps if k not in hold) or "없음", DEV), flush=True)

    t0 = time.time()
    models = []
    if a.load:
        import glob
        for fp in sorted(glob.glob(os.path.join(OUT_PT, a.load + "_[0-9]*.pt"))):
            m = RansPINN().to(DEV)
            m.load_state_dict(torch.load(fp, map_location=DEV))
            models.append(m.eval())
        print(" 불러옴 %d 개: %s" % (len(models), a.load), flush=True)
    for s in range(0 if a.load else a.ens):
        print(" 모델 %d/%d" % (s + 1, a.ens), flush=True)
        models.append(train_one(build(train, fields, keps), s, a.warm, a.iters, a.physics, a.col, log=(s == 0)))
    sec = time.time() - t0
    print(" 학습 %.0f 초" % sec, flush=True)

    qs = np.array([q for _, q in cases])
    mu, sd, tm = predict_stats(models, grid, qs)
    check = []
    for i, (rid, q) in enumerate(cases):
        tr = truth_stats(fields, rid)
        row = {"run_id": rid, "q": q, "held_out": rid in hold}
        for ti in range(2):
            k = "t%d" % ti
            row[k] = {"band_true": round(tr[k]["band"], 4), "band_pred": round(mu[i, ti, 0], 4),
                      "band_sd": round(sd[i, ti, 0], 4), "P10_true": round(tr[k]["P10"], 4),
                      "P10_pred": round(mu[i, ti, 1], 4), "P10_sd": round(sd[i, ti, 1], 4),
                      "T_true": round(tr[k]["T"], 2), "T_pred": round(tm[i, ti], 2)}
        check.append(row)
        print("  %s %-6s 면적 %.2f/%.2f→%.2f/%.2f  P10 %.2f/%.2f→%.2f/%.2f" % (
            "검증" if rid in hold else "학습", rid, tr["t0"]["band"], tr["t1"]["band"],
            mu[i, 0, 0], mu[i, 1, 0], tr["t0"]["P10"], tr["t1"]["P10"], mu[i, 0, 1], mu[i, 1, 1]))

    result = {"made": time.strftime("%Y-%m-%d %H:%M"), "method": "RANS-PINN (arXiv:2306.06034, 2410.18917)"
              if a.physics == "rans" else "데이터만 (비교용)", "physics": a.physics,
              "train": [c[0] for c in train], "holdout": hold,
              "turb_data": sorted(k for k in keps if k not in hold), "warm": a.warm, "iters": a.iters,
              "ens": a.ens, "train_sec": round(sec), "turb_w": a.turb_w,
              "criteria": {"band": BAND, "band_min": BAND_MIN, "P10_min": P10_MIN},
              "fan": {"model": "Oriental Motor EMR2090VMH-A", "points_cmm_w": EMR, "levels": LEVELS},
              "check": check}

    if not hold:
        combos = np.array(list(itertools.product(LEVELS, repeat=4)))
        print(" 탐색 %d 조합" % len(combos), flush=True)
        mu, sd, tm = predict_stats(models, grid, combos)
        watt = fan_watt(combos).sum(1)
        train_pat = {tuple(np.array(q) > 0) for _, q in train}
        # 조합마다 「가장 크게 모자란 정도」: 적정 면적은 75 % 대비, P10 은 0.28 대비 비율
        short = np.maximum.reduce([np.clip((BAND_MIN - mu[:, ti, 0]) / BAND_MIN, 0, None) for ti in range(2)]
                                  + [np.clip((P10_MIN - mu[:, ti, 1]) / P10_MIN, 0, None) for ti in range(2)])

        def entry(i):
            q = combos[i]
            return {"q": q.tolist(), "watt": round(float(watt[i]), 1),
                    "band": [round(mu[i, 0, 0], 3), round(mu[i, 1, 0], 3)],
                    "band_sd": [round(sd[i, 0, 0], 3), round(sd[i, 1, 0], 3)],
                    "P10": [round(mu[i, 0, 1], 3), round(mu[i, 1, 1], 3)],
                    "P10_sd": [round(sd[i, 0, 1], 3), round(sd[i, 1, 1], 3)],
                    "T": [round(tm[i, 0], 2), round(tm[i, 1], 2)],
                    "shortfall": round(float(short[i]), 3),
                    "robust": ok(mu[i] - sd[i]), "pattern_in_train": tuple(q > 0) in train_pat}

        feas = [i for i in range(len(combos)) if short[i] == 0]
        feas.sort(key=lambda i: (watt[i], -mu[i, :, 0].min()))
        # 전력-부족분 파레토: 전력 오름차순으로 보며 지금까지보다 덜 모자란 조합만 남긴다
        pareto, best = [], np.inf
        for i in np.lexsort((short, watt)):
            if short[i] < best - 1e-9:
                pareto.append(i)
                best = short[i]
        near = list(np.argsort(short)[:20])
        result.update({"n_combos": int(len(combos)), "n_feasible": len(feas),
                       "candidates": [entry(i) for i in feas[:60]],
                       "pareto": [entry(i) for i in pareto],
                       "nearest": [entry(i) for i in near]})
        print(" 조건 통과 %d 조합" % len(feas))
        print(" 전력-부족분 파레토 (전력이 늘 때 부족분이 줄어드는 조합만):")
        for i in pareto:
            c = entry(i)
            print("  %5.1f W  q=%s  면적 %s P10 %s  부족 %.0f%%%s" % (
                c["watt"], c["q"], c["band"], c["P10"], c["shortfall"] * 100,
                "" if c["pattern_in_train"] else "  [학습 패턴 밖]"))

    # 난류량 진단 — k 가 0 으로 가는 자명해인지 (논문과 달리 k, ε 데이터가 없어서)
    if a.physics == "rans":
        rng = np.random.default_rng(123)
        xyz = torch.tensor(sample_xyz(4000, rng), dtype=torch.float32, device=DEV)
        diag = {}
        for q in ([6.0, 6.0, 6.0, 6.0], [6.0, 0.0, 6.0, 0.0], [12.0, 12.0, 12.0, 12.0]):
            ks, nus = [], []
            for m in models:
                with torch.no_grad():
                    o = m(xyz, torch.tensor([q] * len(xyz), dtype=torch.float32, device=DEV))
                k = o["k"].cpu().numpy().ravel(); e = o["e"].cpu().numpy().ravel()
                ks.append(np.median(k)); nus.append(np.median(C_MU * k * k / e))
            diag[str(q)] = {"k_median": float(np.mean(ks)), "nut_median": float(np.mean(nus)),
                            "nut_over_nu": float(np.mean(nus) / NU)}
            print("  난류 q=%s  k 중앙 %.2e m²/s²  νt 중앙 %.2e m²/s  (νt/ν %.1f)" % (
                q, np.mean(ks), np.mean(nus), np.mean(nus) / NU))
        result["turbulence_diag"] = diag

    tag = ("full" if not hold else "hold_" + "_".join(hold)) + "_" + a.physics + ("_keps" if keps else "")
    os.makedirs(OUT_PT, exist_ok=True)
    for s, m in enumerate(models):
        torch.save(m.state_dict(), os.path.join(OUT_PT, "%s_%d.pt" % (tag, s)))

    os.makedirs(OUT_DIR, exist_ok=True)
    sfx = a.physics + ("_keps" if keps else "")
    name = ("result_%s.json" % sfx) if not hold else ("holdout_%s_%s.json" % ("_".join(hold), sfx))
    with io.open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(" -> data/fan_pinn/%s" % name)


if __name__ == "__main__":
    main()
