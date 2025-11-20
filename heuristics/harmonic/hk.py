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
    """
    Harmonic-k Algorithm (Adapted for the Analysis Engine).
    Returns: (bins_used, list_of_bin_objects)
    """
    # 1. Define Intervals
    # intervals[0] = 1/2, intervals[1] = 1/3, ...
    intervals = [1.0 / (i + 2.0) for i in range(k - 1)]
    
    # 2. Create Groups (List of Bin objects)
    # bin_groups[0] is for items > 1/2
    # bin_groups[k-1] is for small items
    bin_groups = [[] for _ in range(k)]
    
    print(f"\n[Hk] Starting Harmonic-{k}...")

    for item in items:
        # Classify the item
        group_idx = k - 1 
        for j in range(k - 1):
            if item > intervals[j]:
                group_idx = j
                break
        
        # Pack using First-Fit ONLY within that group
        target_bins = bin_groups[group_idx]
        placed = False
        
        for b in target_bins:
            if b.try_add(item):
                placed = True
                break
        
        if not placed:
            # Create new bin of this specific harmonic type
            new_bin = Bin(harmonic_type=group_idx + 1)
            new_bin.try_add(item)
            target_bins.append(new_bin)
    
    # 3. Flatten results for the report generator
    # We merge all groups into a single list of bins
    all_bins = []
    for group in bin_groups:
        all_bins.extend(group)
        
    print(f"[Hk] Finished: Used {len(all_bins)} bins.\n")
    return len(all_bins), all_bins