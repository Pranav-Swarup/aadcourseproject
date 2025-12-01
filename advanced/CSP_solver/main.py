import sys
import os
import glob
import pulp

def read_instance(folder_path):
    """
    Reads the 3 files from the specified folder.
    Returns: (capacity, optimal_solution, item_weights)
    """
    # 1. Find the files using pattern matching
    c_files = glob.glob(os.path.join(folder_path, "*_c.txt"))
    s_files = glob.glob(os.path.join(folder_path, "*_s.txt"))
    w_files = glob.glob(os.path.join(folder_path, "*_w.txt"))

    # Error handling if files are missing
    if not (c_files and s_files and w_files):
        print(f"Error: Missing files in {folder_path}")
        print("Expected one of each: *_c.txt, *_s.txt, *_w.txt")
        sys.exit(1)

    # 2. Read Capacity (_c.txt)
    with open(c_files[0], 'r') as f:
        capacity = int(f.read().strip())

    # 3. Read Optimal Solution (_s.txt) - count number of lines
    with open(s_files[0], 'r') as f:
        optimal_sol = sum(1 for line in f if line.strip())

    # 4. Read Weights (_w.txt)
    weights = []
    with open(w_files[0], 'r') as f:
        for line in f:
            line = line.strip()
            if line: # Skip empty lines
                weights.append(int(line))

    return capacity, optimal_sol, weights

def solve_dyckhoff(bin_capacity, item_sizes):
    """
    Runs Dyckhoff's One-Cut Model (Model II) using PuLP.
    Returns the calculated minimum number of bins.
    """
    # --- Pre-processing ---
    demands = {}
    for size in item_sizes:
        demands[size] = demands.get(size, 0) + 1
    
    unique_orders = sorted(demands.keys())
    if not unique_orders: return 0
    min_order = unique_orders[0]

    # --- Step 1: Generate Residuals ---
    residuals = set([bin_capacity])
    changed = True
    while changed:
        changed = False
        current_residuals = list(residuals)
        for res in current_residuals:
            for order in unique_orders:
                remainder = res - order
                if remainder >= min_order:
                    if remainder not in residuals:
                        residuals.add(remainder)
                        changed = True

    all_lengths = sorted(list(residuals), reverse=True)
    
    # --- Step 2: Define Cuts ---
    cuts = []
    for k in all_lengths:
        for l in unique_orders:
            if k > l:
                leftover = k - l
                if leftover in residuals or leftover < min_order:
                    cuts.append((k, l, leftover))

    # --- Step 3: Build LP ---
    prob = pulp.LpProblem("Dyckhoff_Solver", pulp.LpMinimize)
    y = pulp.LpVariable.dicts("Cut", range(len(cuts)), lowBound=0, cat='Integer')

    # Objective: Minimize new stock rolls used
    stock_cuts = [i for i, cut in enumerate(cuts) if cut[0] == bin_capacity]
    prob += pulp.lpSum([y[i] for i in stock_cuts]), "Minimize_Bins"

    # --- Step 4: Constraints ---
    lengths_to_balance = [l for l in all_lengths if l != bin_capacity]
    
    for length in lengths_to_balance:
        inflow = pulp.lpSum([y[i] for i, cut in enumerate(cuts) if cut[2] == length])
        outflow = pulp.lpSum([y[i] for i, cut in enumerate(cuts) if cut[0] == length])
        demand_qty = demands.get(length, 0)
        prob += (inflow >= outflow + demand_qty)

    # Solve using CBC (suppress output with msg=0)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # Return the objective value
    if pulp.LpStatus[prob.status] == 'Optimal':
        return int(pulp.value(prob.objective))
    else:
        return -1 # Error code

if __name__ == "__main__":
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python solve_bin_packing.py <path_to_folder>")
        sys.exit(1)

    target_folder = sys.argv[1]
    
    # Run
    if os.path.isdir(target_folder):
        print(f"--- Processing: {target_folder} ---")
        cap, opt_sol, items = read_instance(target_folder)
        
        print(f"Input: {len(items)} items, Capacity {cap}")
        
        calc_sol = solve_dyckhoff(cap, items)
        
        print("-" * 30)
        print(f"Optimal Solution (from file):  {opt_sol}")
        print(f"Calculated Solution (Solver):  {calc_sol}")
        print("-" * 30)
        
        if calc_sol == opt_sol:
            print(">> SUCCESS: Matches Optimal.")
        else:
            print(">> DIFFERENCE DETECTED.")
    else:
        print(f"Error: Folder '{target_folder}' not found.")