# heuristics/harmonick/hk.py
from dataclasses import dataclass, field

CAPACITY = 1.0
K_DEFAULT = 6  # Standard harmonic partitioning depth

@dataclass
class Bin:
    """
    A class compatible with your existing analyse.py visualizer.
    """
    remaining: float = CAPACITY
    items: list = field(default_factory=list)
    # We add 'type' to track which harmonic group this bin belongs to
    harmonic_type: int = 0 

    def try_add(self, item):
        if self.remaining >= item - 1e-9: # Float tolerance
            self.items.append(item)
            self.remaining -= item
            return True
        return False

def run_hk(items, k=K_DEFAULT):
    # 1. Define Intervals
    intervals = [1.0 / (i + 2.0) for i in range(k - 1)]
    
    # bin_groups[0..k-2] store large items strictly
    # bin_groups[k-1] stores small items (and overflow)
    bin_groups = [[] for _ in range(k)]
    
    print(f"\n[Hk] Starting Harmonic-{k}...")

    for item in items:
        # Classify the item
        group_idx = k - 1 
        for j in range(k - 1):
            if item > intervals[j]:
                group_idx = j
                break
        
        placed = False
        
        # --- THE FIX STARTS HERE ---
        
        if group_idx == k - 1:
            # IT IS A SMALL ITEM (The "Sand")
            # Try to put it in ANY bin, starting from the largest item bins
            # to fill their gaps.
            for g_id in range(k):
                for b in bin_groups[g_id]:
                    if b.try_add(item):
                        placed = True
                        break # Break inner loop (bins)
                if placed:
                    break # Break outer loop (groups)
            
            # If still not placed, it goes into the dedicated small item bins
            if not placed:
                new_bin = Bin(harmonic_type=k) # Type k is small
                new_bin.try_add(item)
                bin_groups[k - 1].append(new_bin)

        else:
            # IT IS A LARGE ITEM (The "Rock")
            # These must strictly go into their specific class bins 
            # (standard Harmonic behavior to ensure density)
            target_bins = bin_groups[group_idx]
            
            for b in target_bins:
                if b.try_add(item):
                    placed = True
                    break
            
            if not placed:
                new_bin = Bin(harmonic_type=group_idx + 1)
                new_bin.try_add(item)
                target_bins.append(new_bin)

        # --- THE FIX ENDS HERE ---

    # Flatten results
    all_bins = []
    for group in bin_groups:
        all_bins.extend(group)
        
    print(f"[Hk] Finished: Used {len(all_bins)} bins.\n")
    return len(all_bins), all_bins
