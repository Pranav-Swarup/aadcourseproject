# heuristics/bf/bf.py
"""
Algorithm: Best-Fit (BF)
----------------------------------------
Online heuristic: places each item into the
bin that will leave the *least* remaining space.
"""
from dataclasses import dataclass, field

CAPACITY = 1.0

@dataclass
class Bin:
    remaining: float = CAPACITY
    items: list = field(default_factory=list)
    def try_add(self, item):
        if self.remaining >= item:
            self.items.append(item)
            self.remaining -= item
            return True
        return False

def run_bf(items, flag):
    bins = []
    if flag==0:
        print("\n[BF] Starting Best-Fit algorithm...")
    else:
        print("\n[BFD] Starting Best-Fit Decreasing algorithm...")
    for idx, item in enumerate(items, 1):
        best_idx = -1
        best_after = None
        print(f"  Item {idx}: size={item:.3f}")
        for i, b in enumerate(bins):
            if b.remaining >= item:
                rem_after = b.remaining - item
                if best_after is None or rem_after < best_after:
                    best_after = rem_after
                    best_idx = i
        if best_idx == -1:
            nb = Bin()
            nb.try_add(item)
            bins.append(nb)
            print(f"    -> Created new Bin {len(bins)} (remaining={nb.remaining:.3f})")
        else:
            bins[best_idx].try_add(item)
            print(f"    -> Placed in Bin {best_idx+1} (remaining={bins[best_idx].remaining:.3f})")
    if flag==0:
        print(f"[BF] Finished: Used {len(bins)} bins.\n")
    else:
        print(f"[BFD] Finished: Used {len(bins)} bins.\n")
    return len(bins), bins
