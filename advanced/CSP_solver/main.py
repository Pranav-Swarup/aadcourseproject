import sys
import os
import glob
import pulp

# --- Configuration ---
# Set to True to see the solver logs if it fails
DEBUG_SOLVER = False 

def read_instance(folder_path):
    """
    Reads the 3 files from the specified folder.
    Returns: (capacity, optimal_solution, item_weights)
    """
    folder_path = os.path.normpath(folder_path)

    # 1. Find the files using pattern matching
    c_files = glob.glob(os.path.join(folder_path, "*_c.txt"))
    s_files = glob.glob(os.path.join(folder_path, "*_s.txt"))
    w_files = glob.glob(os.path.join(folder_path, "*_w.txt"))

    # Robust check for file existence
    if not (c_files and s_files and w_files):
        print(f"Error: Missing required files in '{folder_path}'")
        print("Expected: *_c.txt, *_s.txt, *_w.txt")
        sys.exit(1)

    # 2. Read Capacity (_c.txt)
    with open(c_files[0], 'r') as f:
        try:
            content = f.read().strip()
            if not content: raise ValueError
            capacity = int(content)
        except ValueError:
            print(f"Error: Invalid capacity in {c_files[0]}")
            sys.exit(1)

    # 3. Read Optimal Solution (_s.txt)
    # Logic: The file contains bin indices (e.g. 0 0 1 2). 
    # The number of bins = max_index + 1.
    with open(s_files[0], 'r') as f:
        try:
            numbers = [int(x) for x in f.read().split()]
            if not numbers:
                optimal_sol = 0
            else:
                optimal_sol = max(numbers);
        except ValueError:
            print(f"Error: Invalid data in solution file {s_files[0]}")
            sys.exit(1)

    # 4. Read Weights (_w.txt)
    weights = []
    with open(w_files[0], 'r') as f:
        for line in f:
            # Handle potential whitespace or empty lines safely
            clean_line = line.strip()
            if clean_line:
                try:
                    weights.append(int(clean_line))
                except ValueError:
                    print(f"Warning: Skipped non-integer line in weights file: '{clean_line}'")

    return capacity, optimal_sol, weights

def solve_dyckhoff(bin_capacity, item_sizes):
    """
    Runs Dyckhoff's One-Cut Model (Model II) using PuLP/CBC.
    Returns the calculated minimum number of bins.
    """
    # --- Pre-processing: Group Demands ---
    demands = {}
    for size in item_sizes:
        if size > bin_capacity:
            print(f"Error: Item {size} exceeds Capacity {bin_capacity}")
            return -1
        demands[size] = demands.get(size, 0) + 1
    
    unique_orders = sorted(demands.keys())
    if not unique_orders: return 0
    min_order = unique_orders[0]

    # --- Step 1: Generate Residual Set (Nodes) ---
    # Start with the stock length
    residuals = set([bin_capacity])
    
    # Recursive generation of all possible lengths
    changed = True
    while changed:
        changed = False
        current_residuals = list(residuals)
        for res in current_residuals:
            for order in unique_orders:
                remainder = res - order
                # Condition: The remainder must be useful.
                # Useful means >= min_order. 
                # (Smaller pieces are strictly waste and don't need to be nodes).
                if remainder >= min_order:
                    if remainder not in residuals:
                        residuals.add(remainder)
                        changed = True

    # Sort descending for clarity
    all_lengths = sorted(list(residuals), reverse=True)
    
    # --- Step 2: Define Cuts (Edges) ---
    # A cut is (Source, Target Order, Residue)
    cuts = []
    for k in all_lengths:
        for l in unique_orders:
            # Can we cut Order 'l' from Source 'k'?
            if k >= l:
                leftover = k - l
                
                # We add the cut if:
                # 1. Leftover is 0 (Exact fit)
                # 2. Leftover is a valid node (can be used again)
                # 3. Leftover is waste (too small to use)
                
                # Optimization: We only explicitly track flow to nodes that exist.
                # If leftover is waste/0, we mark it as such.
                if leftover in residuals or leftover < min_order:
                    cuts.append((k, l, leftover))

    # --- Step 3: Build LP Model ---
    prob = pulp.LpProblem("Dyckhoff_BPP", pulp.LpMinimize)
    
    # Variables: y[i] is the integer count of Cut i
    y = pulp.LpVariable.dicts("Cut", range(len(cuts)), lowBound=0, cat='Integer')

    # Objective: Minimize Stock Rolls Used
    # These are cuts where the source is the full bin capacity
    stock_cuts = [i for i, cut in enumerate(cuts) if cut[0] == bin_capacity]
    prob += pulp.lpSum([y[i] for i in stock_cuts]), "Minimize_Bins"

    # --- Step 4: Flow Conservation Constraints ---
    # We must balance flow for every length that acts as an intermediate node.
    # Exclude the Bin Capacity (it's a Source, not an intermediate).
    nodes_to_balance = [l for l in all_lengths if l != bin_capacity]

    for length in nodes_to_balance:
        # Inflow 1: Cuts where this length was the RESIDUE
        # e.g., Cut 10 -> 4 + [6]. This creates a 6.
        inflow_residue = [y[i] for i, cut in enumerate(cuts) if cut[2] == length]
        
        # Inflow 2: Cuts where this length was the ORDER
        # e.g., Cut 10 -> [6] + 4. This creates a 6.
        inflow_order = [y[i] for i, cut in enumerate(cuts) if cut[1] == length]
        
        # Outflow: Cuts where this length was the SOURCE
        # e.g., Cut [6] -> 3 + 3. This consumes a 6.
        outflow = [y[i] for i, cut in enumerate(cuts) if cut[0] == length]
        
        # Demand: External requirement for this length
        d_qty = demands.get(length, 0)
        
        # Balance Equation:
        # Created (Residue + Order) >= Consumed (Outflow) + Final Demand
        prob += (pulp.lpSum(inflow_residue + inflow_order) >= pulp.lpSum(outflow) + d_qty), f"Balance_{length}"

    # Special Case: Demand for exact Bin Capacity size
    if bin_capacity in demands:
        # These items MUST come directly from stock cuts that produce 0 residue (or waste)
        # i.e., Cut Capacity -> Capacity + 0
        perfect_fits = [y[i] for i, cut in enumerate(cuts) if cut[0] == bin_capacity and cut[1] == bin_capacity]
        prob += (pulp.lpSum(perfect_fits) >= demands[bin_capacity]), "Demand_Full_Capacity"

    # --- Step 5: Solve ---
    msg_flag = 1 if DEBUG_SOLVER else 0
    prob.solve(pulp.PULP_CBC_CMD(msg=msg_flag))
    
    status = pulp.LpStatus[prob.status]
    if status == 'Optimal':
        return int(pulp.value(prob.objective))
    else:
        print(f"Solver failed with status: {status}")
        return -1

# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solve_bin_packing.py <folder_path>")
        sys.exit(1)

    target_folder = sys.argv[1]
    
    if os.path.isdir(target_folder):
        print(f"--- Processing: {target_folder} ---")
        
        cap, opt_sol, items = read_instance(target_folder)
        
        print(f"Items: {len(items)} | Capacity: {cap}")
        
        calc_sol = solve_dyckhoff(cap, items)
        
        print("\n" + "="*40)
        print(f"{'METRIC':<25} | {'VALUE':<10}")
        print("-" * 40)
        print(f"{'Optimal (from _s.txt)':<25} | {opt_sol:<10}")
        print(f"{'Calculated (Dyckhoff)':<25} | {calc_sol:<10}")
        print("="*40)
        
        if calc_sol == opt_sol:
            print(">> SUCCESS: Result matches optimal.")
        elif calc_sol == -1:
            print(">> FAIL: Solver Error.")
        else:
            diff = abs(calc_sol - opt_sol)
            print(f">> MISMATCH: Difference of {diff} bins.")
    else:
        print(f"Error: Folder '{target_folder}' does not exist.")