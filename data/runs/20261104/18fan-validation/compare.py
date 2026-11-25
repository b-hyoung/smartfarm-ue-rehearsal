"""Postprocess completed surfaces using the same 60 x 20 nearest-sample grid."""
import argparse
import csv
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("results",type=Path)
    root=parser.parse_args().results
    x,y=np.meshgrid(np.arange(60)*.04-1.18,np.arange(20)*.04+1.62)
    grid=np.c_[x.ravel(),y.ravel()]
    with (root/"schedule.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=20: raise ValueError("Expected two tiers x ten intervals")
    results=[]
    for row in rows:
        t,tier=row["end_s"],row["tier"]
        raw=np.loadtxt(root/"postProcessing"/"canopyMaps"/t/f"U_{tier}15cm.raw")
        distances,indices=cKDTree(raw[:,:2]).query(grid)
        if distances.max()>=.031 or not np.isfinite(raw).all():
            raise ValueError(f"Incomplete surface: {t} {tier}")
        speed=np.linalg.norm(raw[indices,3:6],axis=1)
        actual=100*np.mean((speed>=.3)&(speed<=1))
        model=float(row["target_pct"])
        results.append([t,tier,actual,model,actual-model])
    with (root/"comparison.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["end_s","tier","CFD_pct","model_pct","CFD_minus_model_pp"])
        writer.writerows(results)
    overall=np.mean([r[2] for r in results])
    print(f"Overall CFD: {overall:.4f}% | model: 53.0375% | difference: {overall-53.0375:+.4f} pp")

if __name__=="__main__":
    main()
