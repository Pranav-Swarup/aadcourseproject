# heuristics/ff/ff.py
"""
Algorithm: First-Fit (FF)
----------------------------------------
Online heuristic: each item is placed in
the first bin that has enough remaining space.
"""
from dataclasses import dataclass, field

CAPACITY = 1.0

@dataclass
class Bin:
    remaining: float = CAPACITY
    items: list = field(default_factory=list)

    def try_add(self, item):
        """Try adding an item to the bin if it fits."""
        if self.remaining >= item:
            self.items.append(item)
            self.remaining -= item
            return True
        return False

def run_ff(items, flag):
    """
    Perform First-Fit bin packing on the given item list.
    Returns: (bins_used, list_of_bins)
    """
    bins = []
    if flag==0:
        print("\n[FF] Starting First-Fit algorithm...")
    else:
        print("\n[FFD] Starting First-Fit Decreasing algorithm...")
    for idx, item in enumerate(items, 1):
        placed = False
        print(f"  Item {idx}: size={item:.3f}")
        for b_idx, b in enumerate(bins, 1):
            if b.try_add(item):
                print(f"    -> Placed in Bin {b_idx} (remaining={b.remaining:.3f})")
                placed = True
                break
        if not placed:
            new_bin = Bin()
            new_bin.try_add(item)
            bins.append(new_bin)
            print(f"    -> Created new Bin {len(bins)} (remaining={new_bin.remaining:.3f})")
    if flag==0:
        print(f"[FF] Finished: Used {len(bins)} bins.\n")
    else:
        print(f"[FFD] Finished: Used {len(bins)} bins.\n")
    return len(bins), bins
