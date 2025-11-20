# heuristics/comp.py
"""
Comparative Analysis Script
----------------------------------------
Runs FF, BF, FFD, and BFD on all datasets
(p01, p02, ...) located in ../datasets/
and compares their performance.
"""
import os
import pandas as pd
from heuristics.util import load_fsu_instance, pct_over_lb, timer, plot_results
from heuristics.firstfit.ff import run_ff
from heuristics.bestfit.bf import run_bf
from heuristics.firstfitdecreasing.ffd import run_ffd
from heuristics.bestfitdecreasing.bfd import run_bfd
from heuristics.harmonic.hk import run_hk

ALGOS = {
    "FF": run_ff,
    "BF": run_bf,
    "FFD": run_ffd,
    "BFD": run_bfd,
    "Hk": run_hk,
}

def run_all(dataset_root=os.path.join(os.path.dirname(__file__), "..", "datasets")):
    results = []

    print("========== BIN PACKING COMPARATIVE ANALYSIS ==========\n")

    for folder in sorted(os.listdir(dataset_root)):
        path = os.path.join(dataset_root, folder)
        if not os.path.isdir(path):
            continue

        items, capacity, weights = load_fsu_instance(path)

        for name, fn in ALGOS.items():
            print(f"Running {name} on {folder}...")
            (bins_used, _), t = timer(fn, items)
            results.append({
                "dataset": folder,
                "algorithm": name,
                "bins_used": bins_used,
                "pct_over_LB": pct_over_lb(bins_used, items),
                "time_sec": round(t, 6)
            })

    df = pd.DataFrame(results)
    print("\n========== SUMMARY ==========")
    print(df)

    df.to_csv("comparison_results.csv", index=False)
    print("\n✅ Results saved to comparison_results.csv")

    plot_results(df, title="FSU Datasets")
    return df

if __name__ == "__main__":
    run_all()
