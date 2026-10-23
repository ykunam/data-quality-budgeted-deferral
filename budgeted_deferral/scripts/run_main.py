"""E1 (main, noisy/incomplete logs) and E2 (original optimistic oracle-target protocol)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import sys, time, pandas as pd
from joblib import Parallel, delayed
from dqd import static as S, core as C
DATASETS = ["german", "australian", "default", "hmeq"]
SEEDS = range(2, 22)
CONDS = ["clean"] + C.FAMILY_A + C.FAMILY_B
def job(ds, seed, protocol):
    P = S.prepare(ds, seed)
    return S.run(ds, seed, CONDS, protocol=protocol, l2d=(protocol == "logs"), P=P, tag=protocol)
if __name__ == "__main__":
    protocol = sys.argv[1]
    t = time.time()
    out = Parallel(n_jobs=2)(delayed(job)(d, s, protocol) for d in DATASETS for s in SEEDS)
    df = pd.DataFrame([r for o in out for r in o])
    df.to_csv(f"results/static_{protocol}.csv.gz", index=False)
    print(protocol, len(df), round(time.time() - t), "s")
