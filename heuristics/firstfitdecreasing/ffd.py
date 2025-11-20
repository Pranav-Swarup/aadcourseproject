# heuristics/ffd/ffd.py
"""
Algorithm: First-Fit Decreasing (FFD)
----------------------------------------
Offline heuristic: sort items in descending order,
then apply First-Fit algorithm.
"""
from heuristics.firstfit.ff import run_ff

def run_ffd(items):
    print("\n[FFD] Sorting items in decreasing order before applying First-Fit...")
    sorted_items = sorted(items, reverse=True)
    bins_used, bins = run_ff(sorted_items, 1)
    return bins_used, bins
