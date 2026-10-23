import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import time, pandas as pd
from joblib import Parallel, delayed
from dqd import dynamic as Dy
if __name__ == "__main__":
    t = time.time()
    out = Parallel(n_jobs=2)(delayed(Dy.run)(d, s) for d in ["german", "australian", "default", "hmeq"] for s in range(2, 12))
    pd.DataFrame([r for o in out for r in o[0]]).to_csv("results/dynamic.csv.gz", index=False)
    pd.DataFrame([r for o in out for r in o[1]]).to_csv("results/dynamic_log.csv.gz", index=False)
    print("dynamic", round(time.time() - t), "s")
