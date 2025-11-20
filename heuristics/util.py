# misc/util.py
"""
Utility functions used by all heuristic algorithms.
Includes:
 - FSU dataset loader (p01, p02, ...)
 - Performance metrics
 - Timing wrapper
 - Plotting helper
"""

import os
import math
import time
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# 📦 Dataset Loader
# ------------------------------------------------------------
def load_fsu_instance(folder_path: str):
    """
    Load a Bin Packing instance from the FSU dataset.
    Each folder (e.g. p01, p02) contains:
      *_c.txt  → capacity of each bin
      *_w.txt  → weights of items
      *_s.txt  → solution (ignored here)

    Returns:
      normalized_items  → list of item sizes scaled to capacity 1.0
      capacity          → original bin capacity
      raw_weights       → unscaled weights
    """
    files = os.listdir(folder_path)
    c_file = next((f for f in files if f.endswith("_c.txt")), None)
    w_file = next((f for f in files if f.endswith("_w.txt")), None)

    if not c_file or not w_file:
        raise FileNotFoundError(f"Missing required files in {folder_path}")

    with open(os.path.join(folder_path, c_file)) as f:
        capacity = float(f.read().strip())

    with open(os.path.join(folder_path, w_file)) as f:
        weights = [float(x) for x in f.read().split()]

    # Normalize weights to 0–1 range for algorithm compatibility
    items = [w / capacity for w in weights]

    print(f"[Loader] Loaded {len(items)} items from '{folder_path}' (capacity={capacity})")
    return items, capacity, weights

# ------------------------------------------------------------
# 🧮 Metrics
# ------------------------------------------------------------
def lower_bound(items, cap=1.0):
    """Return theoretical lower bound on number of bins."""
    return math.ceil(sum(items) / cap)

def pct_over_lb(bins_used, items, cap=1.0):
    """Return % bins used above lower bound."""
    lb = lower_bound(items, cap)
    return 0 if lb == 0 else round(((bins_used - lb) / lb) * 100, 2)

# ------------------------------------------------------------
# ⏱️ Timing Decorator
# ------------------------------------------------------------
def timer(fn, *args, **kwargs):
    """Run a function and return (output, time_taken)."""
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    t1 = time.perf_counter()
    return out, (t1 - t0)

# ------------------------------------------------------------
# 📊 Plotting
# ------------------------------------------------------------
def plot_results(df, title="Bin Packing Comparative Analysis"):
    """Plot number of bins, % over LB, and execution time for each algorithm."""
    plt.figure(figsize=(6, 4))
    plt.bar(df["algorithm"], df["bins_used"], color="skyblue", edgecolor="black")
    plt.title(f"{title} — Bins Used")
    plt.ylabel("Number of Bins")
    plt.show()

    plt.figure(figsize=(6, 4))
    plt.bar(df["algorithm"], df["pct_over_LB"], color="lightcoral", edgecolor="black")
    plt.title("% Over Lower Bound")
    plt.ylabel("Percentage")
    plt.show()

    plt.figure(figsize=(6, 4))
    plt.bar(df["algorithm"], df["time_sec"], color="lightgreen", edgecolor="black")
    plt.title("Execution Time (seconds)")
    plt.ylabel("Time (s)")
    plt.show()

# ------------------------------------------------------------
# 📂 Optimal Assignment Loader
# ------------------------------------------------------------
def load_optimal_assignment(folder_path: str):
    """Load optimal bin assignment from p0x_s.txt (if present)."""
    files = os.listdir(folder_path)
    s_file = next((f for f in files if f.endswith("_s.txt")), None)
    if not s_file:
        return None
    with open(os.path.join(folder_path, s_file)) as f:
        assignment = [int(x) for x in f.read().split()]
    return assignment
