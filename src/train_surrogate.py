"""대리모델 학습 리허설 — 「조건 → 1.1m 온도장」 (임시 교재 mock_v1).

목적은 정확도가 아니라 **구조**다: 교재(npz) → 학습 → 가중치 저장 → 추론.
진짜 CFD 케이스가 쌓이면 교재만 바꿔 재학습한다. 아키텍처도 그때
정식 PINO(neuraloperator, 물리 손실 포함)로 승격 — 지금은 가벼운
조건→필드 디코더(MLP+Conv)로 자리만 잡는다.

실행  py -m src.train_surrogate            (기본 300 에폭, ~2분/GPU)
출력  data/dataset/surrogate_v1.pt  (+ 검증 오차 출력)
"""
from __future__ import annotations

import json
import os

import numpy as np
import torch
import torch.nn as nn

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(REPO, "data", "dataset")
DEV = "cuda" if torch.cuda.is_available() else "cpu"
NY, NX = 72, 101


class FieldDecoder(nn.Module):
    """조건 3개 → (72,101) 온도장. PINO 자리의 임시 아키텍처."""

    def __init__(self, cond_dim=3, ch=48):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(cond_dim, 256), nn.GELU(),
            nn.Linear(256, ch * 9 * 13), nn.GELU())
        self.up = nn.Sequential(
            nn.ConvTranspose2d(ch, ch, 4, 2, 1), nn.GELU(),      # 18x26
            nn.ConvTranspose2d(ch, ch, 4, 2, 1), nn.GELU(),      # 36x52
            nn.ConvTranspose2d(ch, ch // 2, 4, 2, 1), nn.GELU(), # 72x104
            nn.Conv2d(ch // 2, 1, 3, padding=1))
        self.ch = ch

    def forward(self, x):
        h = self.fc(x).view(-1, self.ch, 9, 13)
        return self.up(h)[:, 0, :NY, :NX]


def main():
    d = np.load(os.path.join(DS, "mock_v1.npz"))
    X, Y, mask = d["X"].copy(), d["Y"].copy(), d["mask"]
    # 정규화 (추론 때 되돌리므로 저장)
    xm, xs = X.mean(0), X.std(0) + 1e-6
    ymu, ysd = np.nanmean(Y), np.nanstd(Y)
    Xn = (X - xm) / xs
    Yn = np.nan_to_num((Y - ymu) / ysd, nan=0.0)

    # 검증은 '본 적 없는 에어컨 위치'로 — 시각만 다른 샘플로 검증하면 반칙
    n_pos = int(json.load(open(os.path.join(DS, "meta.json"),
                               encoding="utf-8"))["n_positions"])
    per = len(X) // n_pos
    val_pos = np.arange(n_pos)[::10]                 # 10%
    vi = np.zeros(len(X), dtype=bool)
    for p in val_pos:
        vi[p * per:(p + 1) * per] = True

    tX = torch.tensor(Xn[~vi], dtype=torch.float32, device=DEV)
    tY = torch.tensor(Yn[~vi], dtype=torch.float32, device=DEV)
    vX = torch.tensor(Xn[vi], dtype=torch.float32, device=DEV)
    vYc = torch.tensor(np.nan_to_num(Y[vi], nan=0.0),
                       dtype=torch.float32, device=DEV)
    m = torch.tensor(mask, dtype=torch.bool, device=DEV)

    net = FieldDecoder().to(DEV)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 300)
    lossf = nn.MSELoss()
    for ep in range(300):
        net.train()
        idx = torch.randperm(len(tX), device=DEV)
        for b in idx.split(64):
            opt.zero_grad()
            out = net(tX[b])
            loss = lossf(out[:, m], tY[b][:, m])
            loss.backward()
            opt.step()
        sched.step()
        if (ep + 1) % 100 == 0:
            net.eval()
            with torch.no_grad():
                pred = net(vX) * ysd + ymu
                err = (pred[:, m] - vYc[:, m]).abs()
                print("ep %3d  검증 |오차| 평균 %.3f K · 최대 %.2f K"
                      % (ep + 1, err.mean().item(), err.max().item()))

    torch.save({"state": net.state_dict(), "xm": xm, "xs": xs,
                "ymu": float(ymu), "ysd": float(ysd)},
               os.path.join(DS, "surrogate_v1.pt"))
    print("saved -> data/dataset/surrogate_v1.pt (검증 = 미학습 위치 %d곳)"
          % len(val_pos))


if __name__ == "__main__":
    main()
