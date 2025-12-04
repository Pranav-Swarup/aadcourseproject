# heuristics/ff/ff.py
"""
Algorithm: First-Fit (FF)
----------------------------------------
Two implementations:
1. Naive O(n²) approach
2. Segment Tree O(n log n) approach
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
    Naive First-Fit: O(n²) time complexity.
    
    For each item, iterate through all bins until finding one that fits.
    Worst case: n items, n bins, checking all bins = O(n²)

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

# ============================================================================
# SEGMENT TREE IMPLEMENTATION
# ============================================================================

class SegmentTree:
    """
    Range Maximum Query Segment Tree.
    
    Efficiently finds the first bin with capacity >= item_size in O(log n).
    """
    
    def __init__(self, size):
        """Initialize segment tree for 'size' bins."""
        self.size = size
        self.tree = [0.0] * (4 * size)  # 4n space for segment tree
        self.bins = []  # Reference to actual bins
    
    def build(self, bins):
        """Build tree from existing bin capacities."""
        self.bins = bins
        if bins:
            self._build(0, 0, len(bins) - 1)
    
    def _build(self, node, start, end):
        """Recursively build the segment tree."""
        if start == end:
            self.tree[node] = self.bins[start].remaining
        else:
            mid = (start + end) // 2
            left_child = 2 * node + 1
            right_child = 2 * node + 2
            
            self._build(left_child, start, mid)
            self._build(right_child, mid + 1, end)
            
            self.tree[node] = max(self.tree[left_child], self.tree[right_child])
    
    def query_first_fit(self, item_size):
        """
        Find the FIRST bin (leftmost) with remaining capacity >= item_size.
        Returns: bin_index or -1 if none found.
        
        Time: O(log n)
        """
        if not self.bins or self.tree[0] < item_size:
            return -1
        
        return self._query_first_fit(0, 0, len(self.bins) - 1, item_size)
    
    def _query_first_fit(self, node, start, end, item_size):
        """Recursively find first fitting bin."""
        # Base case: leaf node
        if start == end:
            return start if self.tree[node] >= item_size else -1
        
        mid = (start + end) // 2
        left_child = 2 * node + 1
        right_child = 2 * node + 2
        
        # Check left subtree first (First-Fit property)
        if self.tree[left_child] >= item_size:
            return self._query_first_fit(left_child, start, mid, item_size)
        
        # If left doesn't have space, check right
        return self._query_first_fit(right_child, mid + 1, end, item_size)
    
    def update(self, bin_index, new_capacity):
        """
        Update bin capacity after placing an item.
        Time: O(log n)
        """
        self._update(0, 0, len(self.bins) - 1, bin_index, new_capacity)
    
    def _update(self, node, start, end, idx, new_val):
        """Recursively update tree."""
        if start == end:
            self.tree[node] = new_val
        else:
            mid = (start + end) // 2
            left_child = 2 * node + 1
            right_child = 2 * node + 2
            
            if idx <= mid:
                self._update(left_child, start, mid, idx, new_val)
            else:
                self._update(right_child, mid + 1, end, idx, new_val)
            
            self.tree[node] = max(self.tree[left_child], self.tree[right_child])
    
    def add_bin(self, bin_obj):
        """Add a new bin (resize tree if needed)."""
        self.bins.append(bin_obj)
        # Rebuild tree (in practice, dynamic segment trees exist but add complexity)
        self.build(self.bins)


def run_ff_segment_tree(items, flag):
    """
    First-Fit using Segment Tree: O(n log n) time complexity.
    
    Segment tree enables O(log n) queries to find the first fitting bin.
    
    Time Complexity:
    - Each of n items: O(log n) query + O(log n) update = O(n log n) total
    - Adding new bins requires tree rebuild: O(n) per new bin
    - Overall: O(n log n) amortized when bins << items
    
    Space Complexity: O(n) for segment tree
    
    Returns: (bins_used, list_of_bins)
    """
    bins = []
    seg_tree = SegmentTree(0)
    
    if flag == 0:
        print("\n[FF-SegTree] Starting First-Fit with Segment Tree...")
    else:
        print("\n[FFD-SegTree] Starting First-Fit Decreasing with Segment Tree...")
    
    for idx, item in enumerate(items, 1):
        print(f"  Item {idx}: size={item:.3f}")
        
        # O(log n) query for first fitting bin
        bin_idx = seg_tree.query_first_fit(item)
        
        if bin_idx != -1:
            # Place in existing bin
            bins[bin_idx].try_add(item)
            print(f"    -> Placed in Bin {bin_idx + 1} (remaining={bins[bin_idx].remaining:.3f})")
            
            # O(log n) update
            seg_tree.update(bin_idx, bins[bin_idx].remaining)
        else:
            # Create new bin
            new_bin = Bin()
            new_bin.try_add(item)
            bins.append(new_bin)
            print(f"    -> Created new Bin {len(bins)} (remaining={new_bin.remaining:.3f})")
            
            # Add to segment tree (requires rebuild - O(n))
            seg_tree.add_bin(new_bin)
    
    if flag == 0:
        print(f"[FF-SegTree] Finished: Used {len(bins)} bins.\n")
    else:
        print(f"[FFD-SegTree] Finished: Used {len(bins)} bins.\n")
    
    return len(bins), bins