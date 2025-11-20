# heuristics/bfd/bfd.py
"""
Algorithm: Best-Fit Decreasing (BFD)
----------------------------------------
Offline heuristic: sort items in descending order,
then apply Best-Fit algorithm.
"""
from heuristics.bestfit.bf import run_bf

def run_bfd(items):
    print("\n[BFD] Sorting items in decreasing order before applying Best-Fit...")
    sorted_items = sorted(items, reverse=True)
    bins_used, bins = run_bf(sorted_items, 1)
    return bins_used, bins
