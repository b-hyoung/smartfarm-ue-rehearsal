"""PINN 리허설 — 센서 12점 + 물리로 온도장 복원 + 미지 입력 역산 (DeepXDE).

근거 (내 창작이 아니라 검증된 방식을 가져옴):
    · 방법: Wei & Ooka, "Indoor airflow field reconstruction using PINN",
      Building and Environment 2023 (희소 센서 → 실내 장 복원)
    · 구현: DeepXDE 공식 역문제 데모 (dde.Variable + PointSetBC)
      https://deepxde.readthedocs.io/en/latest/demos/pinn_inverse/
    · 원전: Raissi et al., J. Comput. Phys. 2019

무엇을 하나
    입력: 가짜 실측 = data/_real-vane25/probes.csv 의 센서 12점(A~D × 3높이)만.
    물리: 단순화 열수지 — u_t = a Δu + k (u_eq − u)
          (유효확산 a, 벌크 혼합/냉각률 k, 평형온도 u_eq 를 미지수로 역산.
           유동(이류)은 안 푼다 — PINN 실패모드 문헌 따라 쉬운 방정식부터.)
    채점: 백업된 단면 정답지(z=1.1m slice + y=2.0m vslice × 15시각)와 비교.
          진짜 실측 때는 못 하는 검증이라 리허설 단계에서만 가능.

교체 지점
    · 실측 도착 → --measured 경로만 교체 (스키마 t_s,point,ue_x,ue_y,z,T_C)
    · 이 리허설이 격자 최소제곱(pinn_check.inverse_fit)보다 낫다고 판단되면
      그 자리에 이 방식을 넣는다. 채점 결과는 data/pinn_rehearsal.json.

⚠ skopt 스텁: 이 PC 앱 제어 정책이 갓 설치된 skopt→sklearn DLL 을 차단한다.
  deepxde 는 준난수 샘플링(LHS/Sobol)에만 skopt 를 쓰므로, pseudo 샘플링만
  쓰는 한 빈 모듈로 충분하다. (pandas 차단과 같은 계열 — hanes 참조)

실행  py -m src.pinn_rehearsal            (GPU 몇 분)
      py -m src.pinn_rehearsal --iters 3000   (빠른 확인)
"""
from __future__ import annotations

import sys
import types

sys.modules.setdefault("skopt", types.ModuleType("skopt"))
import os                                                     # noqa: E402

os.environ.setdefault("DDE_BACKEND", "pytorch")
import argparse                                               # noqa: E402
import csv                                                    # noqa: E402
import json                                                   # noqa: E402

import deepxde as dde                                         # noqa: E402
import numpy as np                                            # noqa: E402
import torch                                                  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.path.join(REPO, "data", "_real-vane25")
OUT_JSON = os.path.join(REPO, "data", "pinn_rehearsal.json")

# 정규화 — PINN 은 O(1) 스케일이 아니면 잘 안 배운다 (실패모드 문헌)
T0, TS = 28.85, 16.35        # 초기·급기 ℃ (vane25 경계조건)
DT = T0 - TS
L, TC = 8.0, 900.0           # 길이(m)·시간(s) 스케일
ROOM = (8.0, 5.7, 2.7)
Y_VSLICE, Z_SLICE = 2.0, 1.1


def to_u(T_C):
    return (T0 - T_C) / DT           # 0=초기 → 1=급기까지 냉각


def to_T(u):
    return T0 - DT * u


def norm_X(pts_m, t_s):
    X = np.column_stack([pts_m / L, np.full(len(pts_m), t_s / TC)])
    return X.astype(np.float32)


def in_droom(x, y):
    a, b = ROOM[0] / 2.0, ROOM[1]
    return (y >= 0) & (((x - a) / a) ** 2 + (y / b) ** 2 <= 1.0)


def load_probes(path, every_s=7.0):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    ts = sorted({float(r["t_s"]) for r in rows})
    step = max(1, int(round(every_s / max(ts[1] - ts[0], 0.1))))
    keep = set(ts[::step])
    pts, uu = [], []
    for r in rows:
        if float(r["t_s"]) in keep:
            pts.append([float(r["ue_x"]), float(r["ue_y"]), float(r["z"]),
                        float(r["t_s"])])
            uu.append(to_u(float(r["T_C"])))
    P = np.array(pts, dtype=np.float32)
    X = np.column_stack([P[:, :3] / L, P[:, 3:4] / TC]).astype(np.float32)
    return X, np.array(uu, dtype=np.float32)[:, None]


def droom_anchors(n, rng):
    """D자 내부 (x,y,z,t) 콜로케이션 — 기각 샘플링."""
    out = []
    while len(out) < n:
        m = (n - len(out)) * 2
        x = rng.uniform(0, ROOM[0], m)
        y = rng.uniform(0, ROOM[1], m)
        ok = in_droom(x, y)
        z = rng.uniform(0, ROOM[2], m)
        t = rng.uniform(0, TC, m)
        out += list(np.column_stack([x[ok], y[ok], z[ok], t[ok]])[: n - len(out)])
    A = np.array(out, dtype=np.float32)
    return np.column_stack([A[:, :3] / L, A[:, 3:4] / TC]).astype(np.float32)


def build_and_train(iters):
    dde.config.set_random_seed(0)
    obs_X, obs_u = load_probes(os.path.join(REAL, "probes.csv"))
    rng = np.random.default_rng(0)
    anchors = droom_anchors(8192, rng)

    # 미지 입력 3개 — PINN 이 데이터+물리로 같이 최적화 (dde.Variable)
    A = dde.Variable(0.05)     # 유효확산 (정규화)
    K = dde.Variable(2.0)      # 벌크 냉각률 (정규화)
    UEQ = dde.Variable(0.5)    # 평형온도 (정규화)

    def pde(X, u):
        u_t = dde.grad.jacobian(u, X, i=0, j=3)
        lap = (dde.grad.hessian(u, X, i=0, j=0)
               + dde.grad.hessian(u, X, i=1, j=1)
               + dde.grad.hessian(u, X, i=2, j=2))
        return u_t - torch.abs(A) * lap - torch.abs(K) * (UEQ - u)

    geom = dde.geometry.Cuboid([0, 0, 0],
                               [ROOM[0] / L, ROOM[1] / L, ROOM[2] / L])
    geomtime = dde.geometry.GeometryXTime(geom, dde.geometry.TimeDomain(0, 1))
    ic = dde.icbc.IC(geomtime, lambda X: 0.0,
                     lambda X, on_initial: on_initial)      # t=0 균일 28.85℃
    obs = dde.icbc.PointSetBC(obs_X, obs_u, component=0)
    data = dde.data.TimePDE(geomtime, pde, [ic, obs],
                            num_domain=0, num_initial=512, anchors=anchors,
                            train_distribution="pseudo")    # skopt 안 밟게

    net = dde.nn.FNN([4] + [64] * 4 + [1], "tanh", "Glorot normal")
    model = dde.Model(data, net)
    model.compile("adam", lr=1e-3, external_trainable_variables=[A, K, UEQ],
                  loss_weights=[1.0, 20.0, 20.0])
    cb = dde.callbacks.VariableValue([A, K, UEQ], period=max(iters // 5, 1))
    model.train(iterations=iters, callbacks=[cb], display_every=iters // 5)

    a = abs(float(A.detach().cpu())) if hasattr(A, "detach") else abs(float(A))
    k = abs(float(K.detach().cpu())) if hasattr(K, "detach") else abs(float(K))
    ueq = float(UEQ.detach().cpu()) if hasattr(UEQ, "detach") else float(UEQ)
    fit = {"alpha_m2s": a * L * L / TC, "tau_s": TC / max(k, 1e-6),
           "T_eq_C": to_T(ueq)}
    return model, fit


def load_slice(kind, i):
    p = os.path.join(REAL, "slices", "%s_%02d.csv" % (kind, i))
    rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    if kind == "slice":                       # z=1.1m 수평, x·y cm
        pts = np.array([[float(r["x"]) / 100.0, float(r["y"]) / 100.0, Z_SLICE]
                        for r in rows])
    else:                                     # y=2.0m 수직, x·z cm
        pts = np.array([[float(r["x"]) / 100.0, Y_VSLICE, float(r["z"]) / 100.0]
                        for r in rows])
    T = np.array([float(r["T"]) for r in rows])
    return pts, T


def score(model):
    """단면 정답지 채점 — PINN(센서 12점) vs mock 수식(기본값) RMS ℃."""
    from src import vane_mock as VM
    from src.config import load_config
    cfg = load_config(os.path.join(REPO, "geometry.json"))
    man = json.load(open(os.path.join(REAL, "frames", "manifest.json"),
                         encoding="utf-8"))
    times = [f["time_s"] for f in man["frames"]]
    res = {}
    for kind in ("slice", "vslice"):
        se_p = se_m = n = 0.0
        per = []
        for i, t in enumerate(times):
            pts, T_true = load_slice(kind, i)
            u = model.predict(norm_X(pts, t))[:, 0]
            e_p = to_T(u) - T_true
            e_m = (VM.temperature(pts, t, cfg) - VM.KELVIN) - T_true
            se_p += float(np.sum(e_p ** 2))
            se_m += float(np.sum(e_m ** 2))
            n += len(T_true)
            per.append({"t_s": t,
                        "rms_pinn": round(float(np.sqrt(np.mean(e_p ** 2))), 3),
                        "rms_mock": round(float(np.sqrt(np.mean(e_m ** 2))), 3)})
        res[kind] = {"rms_pinn": round((se_p / n) ** 0.5, 3),
                     "rms_mock": round((se_m / n) ** 0.5, 3), "per_frame": per}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=15000)
    args = ap.parse_args()

    model, fit = build_and_train(args.iters)
    res = score(model)

    print("\nPINN_REHEARSAL — 센서 12점만 보고 복원, 단면 정답지 채점")
    print("  역산: 유효확산 %.2e m²/s · 냉각 시정수 %.0f s · 평형 %.2f ℃"
          % (fit["alpha_m2s"], fit["tau_s"], fit["T_eq_C"]))
    for kind, r in res.items():
        tag = "1.1m 수평" if kind == "slice" else "2.0m 수직"
        print("  %s: PINN %.3f℃ vs mock수식 %.3f℃" %
              (tag, r["rms_pinn"], r["rms_mock"]))

    out = {"iters": args.iters, "fit": {k: round(v, 6) for k, v in fit.items()},
           "score": res,
           "versions": {"deepxde": dde.__version__, "torch": torch.__version__},
           "note": ("리허설 — 가짜 실측(vane25 CFD 센서 12점). "
                    "물리는 단순화(이류 없음). 실측 오면 입력만 교체.")}
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print("  -> data/pinn_rehearsal.json")


if __name__ == "__main__":
    main()
