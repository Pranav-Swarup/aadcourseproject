import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import warnings

# Suppress the non-interactive backend warning from matplotlib
warnings.filterwarnings('ignore', category=UserWarning, message='.*FigureCanvasAgg.*')

def harmonic_k_with_bins(items, capacity, k):
    """
    Implements the Harmonic-k algorithm and returns the full
    structure of all bins used, organized by group.
    
    Returns:
    - list[list[list[int]]]: A list of k groups.
      Each group is a list of bins.
      Each bin is a list of item sizes it contains.
    """
    
    # We need k groups of bins.
    # bin_groups[0] is for I_1, bin_groups[1] for I_2, ..., bin_groups[k-1] for I_k
    bin_groups = [[] for _ in range(k)]
    
    # Define the harmonic intervals (e.g., (1/2, 1], (1/3, 1/2], ...)
    # intervals[0] = 1/2, intervals[1] = 1/3, ...
    intervals = [1.0 / (i + 2.0) for i in range(k - 1)]

    for item in items:
        if item > capacity:
            print(f"Error: Item size {item} exceeds capacity {capacity}. Skipping.")
            continue
            
        normalized_size = float(item) / capacity

        # 1. Classify the item
        group_index = k - 1 # Default to the last group (I_k) for smallest items
        for j in range(k - 1):
            # intervals[0] is 1/2. If norm_size > 1/2, it's group 0 (I_1)
            # intervals[1] is 1/3. If norm_size > 1/3, it's group 1 (I_2)
            if normalized_size > intervals[j]:
                group_index = j
                break
        
        # 2. Pack the item using First-Fit *within its group*
        target_group_bins = bin_groups[group_index]
        placed = False
        
        for b in target_group_bins:
            current_fill = sum(b)
            if (capacity - current_fill) >= item:
                b.append(item)  # Add item to this bin
                placed = True
                break
        
        if not placed:
            # No fitting bin found in this group, open a new one
            new_bin = [item]
            target_group_bins.append(new_bin)
            
    return bin_groups

def visualize_packing(bin_groups, capacity, k):
    """
    Creates a stacked bar chart to visualize the packed bins.
    """
    
    # Get a color map with k distinct colors
    # We use 'tab10' or 'tab20' for good categorical colors
    if k <= 10:
        colors = plt.colormaps['tab10']
    else:
        colors = plt.colormaps['tab20']

    bin_labels = []
    total_bin_count = 0
    
    # Set up the plot
    plt.figure(figsize=(16, 8))
    
    # Iterate through each group and each bin to draw it
    for group_index, group_bins in enumerate(bin_groups):
        if not group_bins: # Skip empty groups
            continue
            
        group_color = colors(group_index)
        group_name = f'I_{group_index + 1}'
        # Create consistent, valid labels describing the harmonic interval for the group
        if group_index == 0:
            group_label = f'{group_name} (> {1.0/(group_index+2):.2f} C)'
        elif group_index < k - 1:
            group_label = f'{group_name} (> {1.0/(group_index+2):.2f} C)'
        else:
            group_label = f'{group_name} (<= {1.0/(group_index+1):.2f} C)'

        for bin_items in group_bins:
            # Add a label for the x-axis tick
            bin_labels.append(f'Group {group_index + 1}\nBin {total_bin_count + 1}')
            
            bottom = 0
            for item_index, item_size in enumerate(bin_items):
                # The first item in the bin gets the group label for the legend
                label = group_label if item_index == 0 else None
                
                plt.bar(
                    total_bin_count,  # x-position
                    item_size,        # height
                    bottom=bottom,
                    color=group_color,
                    edgecolor='black', # Add a black edge to see items
                    linewidth=0.5,
                    label=label
                )
                bottom += item_size
            
            total_bin_count += 1

    # Add a red line for the capacity
    plt.axhline(y=capacity, color='red', linestyle='--', linewidth=2, label=f'Capacity ({capacity})')

    # --- Final plot styling ---
    plt.title(f'Harmonic-k Bin Packing Visualization (k={k})', fontsize=16)
    plt.ylabel('Capacity Used', fontsize=12)
    plt.xlabel('Bins (Organized by Harmonic Group)', fontsize=12)
    
    # Set x-axis ticks and labels
    if total_bin_count > 0:
        plt.xticks(range(total_bin_count), bin_labels, rotation=45, ha='right')
        plt.xlim(-0.5, total_bin_count - 0.5)
    
    plt.ylim(0, capacity * 1.1) # Give 10% extra space at top
    
    # Create a unique legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles)) # Removes duplicate labels
    plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.02, 1), loc='upper left')
    
    plt.tight_layout() # Adjust plot to prevent label overlap
    plt.savefig('harmonic_k_packing.png', dpi=150, bbox_inches='tight')
    print("Plot saved to 'harmonic_k_packing.png'")
    try:
        plt.show()  # Will display if interactive backend is available
    except Exception:
        pass  # Non-interactive backend; plot already saved


# --- Main Execution ---
if __name__ == "__main__":
    # Your dataset
    CAPACITY = 524
    ITEMS = [
        442, 252, 252, 252, 252, 252, 252, 252, 127, 127, 
        127, 127, 127, 106, 106, 106, 106, 85, 84, 46, 
        37, 37, 12, 12, 12, 10, 10, 10, 10, 10, 
        10, 9, 9
    ]
    
    # We'll choose k=6, which gives intervals
    # I_1: (> 1/2)
    # I_2: (> 1/3]
    # I_3: (> 1/4]
    # I_4: (> 1/5]
    # I_5: (> 1/6]
    # I_6: (<= 1/6]
    K_VALUE = 6

    # 1. Run the algorithm to get the bin structure
    all_bin_groups = harmonic_k_with_bins(ITEMS, CAPACITY, K_VALUE)
    
    # 2. Visualize the result
    visualize_packing(all_bin_groups, CAPACITY, K_VALUE)
