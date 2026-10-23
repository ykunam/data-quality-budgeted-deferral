"""E6: how much review data does a learned router need?  Default and HMEQ with the gain-fitting
partition subsampled to the size of the small benchmarks."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import time, pandas as pd
from joblib import Parallel, delayed
from dqd import static as S, core as C
KEEP = ["confidence", "chow_risk", "sh_quality", "2h_prob", "2h_quality", "2h_rich_gorder", "l2d_ce", "l2d_ova"]
def job(ds, seed, frac):
    P = S.prepare(ds, seed, gain_frac=frac)
    rows = S.run(ds, seed, C.FAMILY_A + C.FAMILY_B, caps=[0.2], P=P, tag=f"{frac}", keep=KEEP)
    for r in rows: r["gain_frac"] = frac; r["n_gain"] = len(P["idx"][2])
    return rows
if __name__ == "__main__":
    t = time.time()
    out = Parallel(n_jobs=2)(delayed(job)(d, s, f) for d in ["default", "hmeq"] for s in range(2, 22)
                             for f in ([0.033, 0.1, 0.3, 1.0] if d == "default" else [0.1, 0.3, 1.0]))
    df = pd.DataFrame([r for o in out for r in o]); df.to_csv("results/e6_volume.csv.gz", index=False)
    print("e6", len(df), round(time.time() - t), "s")
