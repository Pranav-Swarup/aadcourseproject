import math
import time
import sys
from typing import List, Tuple, Dict

class MTPBinPacking:
    """
    Correct Implementation of Martello-Toth Procedure (MTP)
    Strategy: Bin-oriented Branch and Bound with Reduction Procedures
    """
    
    def __init__(self, items: List[int], capacity: int):
        self.n = len(items)
        self.capacity = capacity
        self.original_items = items[:]
        # MTP requires items sorted descending
        self.items = sorted(items, reverse=True)
        self.item_map = self._create_item_map(items)
        self.best_solution = None
        self.best_bins = float('inf')
        self.backtracks = 0
        self.max_backtracks = -1
        self.start_time = 0
        self.time_limit = 60 # seconds
        self.nodes_explored = 0
        
    def _create_item_map(self, original_items: List[int]) -> Dict[int, int]:
        """Map sorted items back to original indices"""
        item_map = {}
        used = [False] * len(original_items)
        for i, sorted_val in enumerate(self.items):
            for j, orig_val in enumerate(original_items):
                if not used[j] and orig_val == sorted_val:
                    item_map[i] = j
                    used[j] = True
                    break
        return item_map
    
    def compute_L1(self, items: List[int] = None) -> int:
        """Compute L1 lower bound (volume bound)"""
        if items is None:
            items = self.items
        if len(items) == 0:
            return 0
        total = sum(items)
        return math.ceil(total / self.capacity)
    
    def compute_L2(self, items: List[int] = None) -> int:
        """Compute L2 lower bound (Martello-Toth bound)"""
        if items is None:
            items = self.items
        if not items:
            return 0
        
        C = self.capacity
        
        # Start with L1 bound
        max_lb = math.ceil(sum(items) / C)
        
        # If all items <= C/2, use special case
        if items[0] <= C // 2:
            return max(max_lb, self._compute_L2_small_items(items))
        
        # Try different K values
        # Optimization: only check K values that are item sizes <= C/2
        unique_weights = sorted(list(set([w for w in items if w <= C // 2])), reverse=True)
        k_values = [0] + unique_weights
        
        for K in k_values:
            if K > C // 2:
                continue
            
            # Classify items
            # N1: > C - K
            # N2: C - K >= w > C/2
            # N3: C/2 >= w >= K
            
            n1 = 0
            n2 = 0
            n2_sum = 0
            n3_sum = 0
            
            # Since items are sorted, we can optimize loops, but simple pass is safer
            for w in items:
                if w > C - K:
                    n1 += 1
                elif w > C // 2:
                    n2 += 1
                    n2_sum += w
                elif w >= K:
                    n3_sum += w
            
            # Calculate residual capacity in N2 bins
            R_N2 = (n2 * C) - n2_sum
            
            # Calculate L(K)
            excess = max(0, n3_sum - R_N2)
            L_K = n1 + n2 + math.ceil(excess / C)
            
            if L_K > max_lb:
                max_lb = L_K
        
        return max_lb
    
    def _compute_L2_small_items(self, items: List[int]) -> int:
        """Compute L2 when all items are <= C/2"""
        n = len(items)
        C = self.capacity
        max_lb = 0
        
        if n == 0:
            return 0
        
        # This implementation follows the logic from Martello & Toth code
        ratio = C // items[0]
        i = 1
        
        while i < n:
            next_i = i
            while next_i < n:
                ir = C // items[next_i]
                if ir > ratio:
                    break
                next_i += 1
            
            nlb = math.ceil((next_i) / ratio) # next_i is count because 0-indexed
            max_lb = max(max_lb, nlb)
            
            if next_i >= n:
                break
            
            ir = C // items[next_i]
            if math.ceil(n / ir) <= max_lb:
                break
            
            i = next_i
            ratio = ir
        
        return max_lb
    
    def first_fit_decreasing(self, items: List[int] = None) -> Tuple[int, List[int]]:
        """Heuristic: First Fit Decreasing"""
        if items is None:
            items = self.items
        
        bins = []
        residual = []
        assignment = [-1] * len(items)
        
        for i, w in enumerate(items):
            placed = False
            for j, r in enumerate(residual):
                if r >= w:
                    bins[j].append(i)
                    residual[j] -= w
                    assignment[i] = j
                    placed = True
                    break
            
            if not placed:
                bins.append([i])
                residual.append(self.capacity - w)
                assignment[i] = len(bins) - 1
        
        return len(bins), assignment
    
    def best_fit_decreasing(self, items: List[int] = None) -> Tuple[int, List[int]]:
        """Heuristic: Best Fit Decreasing"""
        if items is None:
            items = self.items
        
        bins = []
        residual = []
        assignment = [-1] * len(items)
        
        for i, w in enumerate(items):
            best_bin = -1
            best_residual = self.capacity + 1
            
            for j, r in enumerate(residual):
                if r >= w and r < best_residual:
                    best_bin = j
                    best_residual = r
            
            if best_bin >= 0:
                bins[best_bin].append(i)
                residual[best_bin] -= w
                assignment[i] = best_bin
            else:
                bins.append([i])
                residual.append(self.capacity - w)
                assignment[i] = len(bins) - 1
        
        return len(bins), assignment

    def run_reduction(self, items: List[int]) -> Tuple[int, List[List[int]], List[int]]:
        """
        Implementation of MTP Reduction Procedure (Section 3.2 of PDF).
        Returns: (num_fixed_bins, fixed_bins_list, remaining_items_list)
        """
        print("Running Reduction Procedure...")
        current_items = items[:]
        fixed_bins = []
        
        # We need to map current_items back to original indices effectively later, 
        # but for solving, we just need the weights.
        
        # Iterate until no reduction possible
        while True:
            reduction_made = False
            if not current_items:
                break
                
            # Sort current items descending
            current_items.sort(reverse=True)
            n_curr = len(current_items)
            
            # The reduction iterates through items. We try to fix the largest item 'i'.
            # Since we modify the list, we restart loop if reduction happens.
            
            # Try to match largest item
            largest = current_items[0]
            
            # Find candidate for 2-item match (Dominance Check 2 in PDF)
            # "If i fits with i', and {i, i'} fills the bin so well that no triplet could be better"
            # Condition: largest + other = C (Perfect Fit) is a strong dominance.
            
            best_match_idx = -1
            
            # Search for perfect pair sum
            for k in range(1, n_curr):
                if largest + current_items[k] == self.capacity:
                    best_match_idx = k
                    break
            
            if best_match_idx != -1:
                # Found perfect pair {largest, match}
                bin_content = [largest, current_items[best_match_idx]]
                fixed_bins.append(bin_content)
                
                # Remove items
                # Remove larger index first to avoid shifting issues
                current_items.pop(best_match_idx)
                current_items.pop(0)
                reduction_made = True
            
            if reduction_made:
                continue
                
            # If no perfect pair, check if item is > C/2 and NO other item fits (Singleton)
            # This is "Check 1" in PDF
            smallest = current_items[-1]
            if largest + smallest > self.capacity:
                # Largest item cannot fit with ANYTHING. Must go alone.
                fixed_bins.append([largest])
                current_items.pop(0)
                reduction_made = True
            
            if not reduction_made:
                # If we couldn't reduce the largest item, we stop the reduction loop 
                # because MTP reduction typically iterates on the largest available.
                break
                
        return len(fixed_bins), fixed_bins, current_items

    def solve(self) -> Tuple[int, List[int]]:
        """Main solving procedure"""
        self.start_time = time.time()
        print(f"\nComputing bounds...")
        
        # 1. Reduction Phase
        # We run reduction on the weights. We need to handle the assignment reconstruction later.
        # This is a simplified reduction that finds perfect pairs/singletons.
        
        # Create a copy of items to track which were used in reduction
        reduced_weights = self.items[:]
        
        # Note: To correctly map back to original indices, we would need a more complex structure.
        # For this implementation, we will use the Reduced set for L2 and Branching, 
        # and then map back greedily or by value matching for the final output.
        
        num_fixed, fixed_bins_content, remaining_weights = self.run_reduction(reduced_weights)
        
        print(f"Reduction fixed {num_fixed} bins.")
        
        # 2. Compute Bounds on Remaining Items
        lb_rem = self.compute_L2(remaining_weights)
        lb = num_fixed + lb_rem
        
        # Get heuristic upper bounds (on full set for simplicity of implementation)
        ub_ffd, sol_ffd = self.first_fit_decreasing()
        ub_bfd, sol_bfd = self.best_fit_decreasing()
        ub = min(ub_ffd, ub_bfd)
        
        print(f"Lower Bound (L2): {lb} (Fixed: {num_fixed} + Rem: {lb_rem})")
        print(f"Upper Bound: {ub}")
        
        if lb == ub:
            print("Heuristic solution is proven optimal!")
            self.best_bins = ub
            self.best_solution = sol_ffd if ub_ffd <= ub_bfd else sol_bfd
            return ub, self.best_solution
        
        # 3. Branch and Bound
        # We solve for the remaining items
        self.best_bins = ub
        
        # Prepare data for B&B
        # We only work with remaining_weights
        rem_n = len(remaining_weights)
        used = [False] * rem_n
        assignment = [-1] * rem_n
        
        print(f"\nStarting branch-and-bound search on {rem_n} remaining items...")
        
        # Target loop
        # We start from the LB calculated on remaining items
        start_target = max(0, lb - num_fixed)
        end_target = ub - num_fixed
        
        found_optimal = False
        final_rem_assignment = []
        
        for target in range(start_target, end_target):
            print(f"\nSearching for solution with {target} bins (Total {target + num_fixed})...")
            
            self.backtracks = 0
            self.nodes_explored = 0
            
            # Pass start_index=0 to enforce order within bins
            if self._bin_oriented_search(0, self.capacity, 0, used, assignment, target, remaining_weights, 0):
                print(f"Found solution with {target} bins!")
                self.best_bins = target + num_fixed
                final_rem_assignment = assignment[:]
                found_optimal = True
                break
            else:
                print(f"No solution with {target} bins (backtracks: {self.backtracks})")
        
        # Reconstruct full solution
        # This part maps the results back to the original item format for visualization
        final_assignment = [-1] * self.n
        
        # 1. Map fixed bins
        # This is tricky because we have identical values. We use the 'item_map' and a 'used' tracker.
        global_used = [False] * self.n
        
        # Assign fixed bins
        current_bin_idx = 0
        for b_content in fixed_bins_content:
            for weight in b_content:
                # Find the first unused item with this weight in self.items
                for i in range(self.n):
                    if not global_used[i] and self.items[i] == weight:
                        final_assignment[i] = current_bin_idx
                        global_used[i] = True
                        break
            current_bin_idx += 1
            
        # Assign B&B result bins
        if found_optimal:
            for i, bin_rel_idx in enumerate(final_rem_assignment):
                weight = remaining_weights[i]
                actual_bin = current_bin_idx + bin_rel_idx
                
                # Find unused item with this weight
                for k in range(self.n):
                    if not global_used[k] and self.items[k] == weight:
                        final_assignment[k] = actual_bin
                        global_used[k] = True
                        break
        else:
            # Fallback to heuristic if B&B didn't improve (should not happen if we go up to UB)
            print("Using heuristic solution as fallback.")
            return ub, (sol_ffd if ub_ffd <= ub_bfd else sol_bfd)

        return self.best_bins, final_assignment
    
    def _bin_oriented_search(self, bin_idx: int, residual: int, items_packed: int, 
                           used: List[bool], assignment: List[int], target: int, 
                           items: List[int], start_index: int) -> bool:
        """
        Bin-by-Bin Branch and Bound Strategy.
        Args:
            start_index: Optimization to enforce item ordering within a bin (Symmetry Breaking)
        """
        n = len(items)
        
        # 1. Solution Found Check
        if items_packed == n:
            return True

        # 2. Limit Check
        if bin_idx >= target:
            return False

        # 3. Pruning (Optimality Cut)
        if residual == self.capacity:
            # Gather remaining items
            remaining_list = [items[i] for i in range(n) if not used[i]]
            lb_rem = self.compute_L2(remaining_list)
            
            if bin_idx + lb_rem > target:
                self.backtracks += 1
                return False

        # 4. Time Limit Check
        if self.nodes_explored % 5000 == 0:
            if time.time() - self.start_time > self.time_limit:
                return False
        self.nodes_explored += 1

        # 5. Branching: Try to put items in current bin
        # Optimization: Try to fill PERFECTLY first
        # If we can fill the bin with remaining items exactly, do it and don't backtrack.
        # This is a form of Dominance.
        
        item_placed = False
        must_fill = (residual == self.capacity)
        
        # Iterate starting from start_index (Symmetry Breaking: items in bin are sorted)
        for i in range(start_index, n):
            if not used[i] and items[i] <= residual:
                
                # Symmetry Breaking: Don't try same size item twice in the same state
                if i > start_index and items[i] == items[i-1] and not used[i-1]:
                    continue
                
                # Apply move
                used[i] = True
                assignment[i] = bin_idx
                
                # Recurse: Stay in SAME bin, pass i+1 to enforce order
                if self._bin_oriented_search(bin_idx, residual - items[i], 
                                           items_packed + 1, used, assignment, target, items, i + 1):
                    return True
                
                # Backtrack
                used[i] = False
                assignment[i] = -1
                item_placed = True
                
                # OPTIMIZATION: If we started a new bin, we MUST put the largest available item in it.
                # If that fails, we don't need to try smaller items as the "first" item, 
                # because that would be covered by a permutation of bins.
                if must_fill:
                    return False

        # 6. Branching: Close Current Bin
        if not must_fill:
             # Move to NEXT bin (bin_idx + 1) with FULL capacity
             # Reset start_index to 0 for the new bin
            if self._bin_oriented_search(bin_idx + 1, self.capacity, 
                                       items_packed, used, assignment, target, items, 0):
                return True

        return False

def visualize_packing(items: List[int], assignment: List[int], 
                     capacity: int, item_map: Dict[int, int]):
    """Create visual representation of bin packing"""
    if not assignment:
        return

    num_bins = max(assignment) + 1
    bins = [[] for _ in range(num_bins)]
    
    for i, bin_idx in enumerate(assignment):
        if bin_idx != -1: # check for unassigned items
            original_idx = item_map[i]
            bins[bin_idx].append((original_idx, items[i]))
    
    print("\n" + "="*60)
    print("OPTIMAL BIN PACKING SOLUTION")
    print("="*60)
    
    for bin_idx, bin_items in enumerate(bins):
        total = sum(w for _, w in bin_items)
        utilization = (total / capacity) * 100
        
        print(f"\nBin {bin_idx + 1}: (Used: {total}/{capacity}, "
              f"Utilization: {utilization:.1f}%)")
        print("  " + "─" * 50)
        
        # Visual bar
        bar_length = 40
        filled = int((total / capacity) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  │{bar}│")
        
        # Items in bin
        print("  Items:")
        for orig_idx, weight in sorted(bin_items):
            print(f"    • Item {orig_idx + 1}: weight = {weight}")
    
    print("\n" + "="*60)
    print(f"Total bins used: {num_bins}")
    if num_bins > 0:
        print(f"Average utilization: {sum(items) / (num_bins * capacity) * 100:.1f}%")
    print("="*60)

def main():
    print("Martello-Toth Bin Packing Solver")
    print("="*60)
    
    # Read input
    filename = input("Enter input filename (or press Enter for manual input): ").strip()
    
    if filename:
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            n = int(lines[0].strip())
            capacity = int(lines[1].strip())
            optimal = int(lines[2].strip()) if len(lines) > 2 else None
            items = [int(lines[i].strip()) for i in range(3, 3 + n)]
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        n = int(input("Number of items: "))
        capacity = int(input("Bin capacity: "))
        optimal = None
        items = []
        print(f"Enter {n} item weights:")
        for i in range(n):
            items.append(int(input(f"  Item {i+1}: ")))
    
    print(f"\nProblem: {n} items, capacity = {capacity}")
    if optimal:
        print(f"Known optimal: {optimal} bins")
    
    # Solve
    solver = MTPBinPacking(items, capacity)
    num_bins, assignment = solver.solve()
    
    print(f"\n{'='*60}")
    print(f"RESULT: Optimal solution uses {num_bins} bins")
    if optimal and num_bins == optimal:
        print("✓ Matches known optimal!")
    elif optimal:
        print(f"⚠ Known optimal is {optimal} bins")
    print(f"{'='*60}")
    
    # Visualize
    visualize_packing(solver.items, assignment, capacity, solver.item_map)

if __name__ == "__main__":
    main()
