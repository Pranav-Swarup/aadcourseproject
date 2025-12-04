# heuristics/bf/bf.py
"""
Algorithm: Best-Fit (BF)
----------------------------------------
Two implementations:
1. Naive O(n²) approach
2. AVL Tree (multiset) O(n log n) approach
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

# ============================================================================
# AVL TREE IMPLEMENTATION (Multiset approach)
# ============================================================================

class AVLNode:
    """Node in AVL tree storing (remaining_capacity, bin_object)."""
    
    def __init__(self, capacity, bin_obj):
        self.capacity = capacity
        self.bin = bin_obj
        self.height = 1
        self.left = None
        self.right = None


class AVLTree:
    """
    Self-balancing binary search tree for Best-Fit queries.
    
    Supports:
    - Insert: O(log n)
    - Find smallest capacity >= item_size: O(log n)
    - Delete: O(log n)
    
    Acts as a C++ multiset<pair<double, Bin*>>
    """
    
    def __init__(self):
        self.root = None
    
    def height(self, node):
        return node.height if node else 0
    
    def balance_factor(self, node):
        return self.height(node.left) - self.height(node.right) if node else 0
    
    def update_height(self, node):
        if node:
            node.height = 1 + max(self.height(node.left), self.height(node.right))
    
    def rotate_right(self, y):
        """Right rotation for balancing."""
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self.update_height(y)
        self.update_height(x)
        
        return x
    
    def rotate_left(self, x):
        """Left rotation for balancing."""
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self.update_height(x)
        self.update_height(y)
        
        return y
    
    def insert(self, node, capacity, bin_obj):
        """Insert (capacity, bin) pair into AVL tree."""
        # Standard BST insertion
        if not node:
            return AVLNode(capacity, bin_obj)
        
        if capacity < node.capacity:
            node.left = self.insert(node.left, capacity, bin_obj)
        else:
            node.right = self.insert(node.right, capacity, bin_obj)
        
        # Update height
        self.update_height(node)
        
        # Balance the tree
        balance = self.balance_factor(node)
        
        # Left-Left Case
        if balance > 1 and capacity < node.left.capacity:
            return self.rotate_right(node)
        
        # Right-Right Case
        if balance < -1 and capacity >= node.right.capacity:
            return self.rotate_left(node)
        
        # Left-Right Case
        if balance > 1 and capacity >= node.left.capacity:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        
        # Right-Left Case
        if balance < -1 and capacity < node.right.capacity:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        
        return node
    
    def find_best_fit(self, node, item_size, best=None):
        """
        Find bin with SMALLEST capacity >= item_size (Best-Fit property).
        Returns: (capacity, bin_object) or None
        
        Time: O(log n)
        """
        if not node:
            return best
        
        # If current node fits the item
        if node.capacity >= item_size:
            # Update best if this is tighter fit
            if best is None or node.capacity < best[0]:
                best = (node.capacity, node.bin)
            # Check left subtree for even better fit
            return self.find_best_fit(node.left, item_size, best)
        else:
            # Current doesn't fit, go right
            return self.find_best_fit(node.right, item_size, best)
    
    def delete(self, node, capacity, bin_obj):
        """Delete specific (capacity, bin) pair from tree."""
        if not node:
            return node
        
        # Standard BST deletion
        if capacity < node.capacity:
            node.left = self.delete(node.left, capacity, bin_obj)
        elif capacity > node.capacity:
            node.right = self.delete(node.right, capacity, bin_obj)
        else:
            # Found matching capacity - check if it's the right bin object
            if node.bin is bin_obj:
                # Node with one child or no child
                if not node.left:
                    return node.right
                elif not node.right:
                    return node.left
                
                # Node with two children: get inorder successor
                temp = self._min_value_node(node.right)
                node.capacity = temp.capacity
                node.bin = temp.bin
                node.right = self.delete(node.right, temp.capacity, temp.bin)
            else:
                # Same capacity but different bin, search further
                node.right = self.delete(node.right, capacity, bin_obj)
        
        if not node:
            return node
        
        # Update height and balance
        self.update_height(node)
        balance = self.balance_factor(node)
        
        # Left-Left Case
        if balance > 1 and self.balance_factor(node.left) >= 0:
            return self.rotate_right(node)
        
        # Left-Right Case
        if balance > 1 and self.balance_factor(node.left) < 0:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        
        # Right-Right Case
        if balance < -1 and self.balance_factor(node.right) <= 0:
            return self.rotate_left(node)
        
        # Right-Left Case
        if balance < -1 and self.balance_factor(node.right) > 0:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        
        return node
    
    def _min_value_node(self, node):
        """Find node with minimum capacity (leftmost node)."""
        current = node
        while current.left:
            current = current.left
        return current
    
    def insert_bin(self, capacity, bin_obj):
        """Public insert method."""
        self.root = self.insert(self.root, capacity, bin_obj)
    
    def find_best_bin(self, item_size):
        """Public best-fit query method."""
        return self.find_best_fit(self.root, item_size)
    
    def remove_bin(self, capacity, bin_obj):
        """Public delete method."""
        self.root = self.delete(self.root, capacity, bin_obj)


def run_bf_avl(items, flag):
    """
    Best-Fit using AVL Tree (multiset): O(n log n) time complexity.
    
    Time Complexity:
    - Each of n items:
      * O(log n) to find best-fit bin
      * O(log n) to delete old entry
      * O(log n) to insert updated entry
    - Total: O(n log n)
    
    Space Complexity: O(n) for AVL tree nodes
    
    Returns: (bins_used, list_of_bins)
    """
    bins = []
    avl_tree = AVLTree()
    
    if flag == 0:
        print("\n[BF-AVL] Starting Best-Fit with AVL Tree...")
    else:
        print("\n[BFD-AVL] Starting Best-Fit Decreasing with AVL Tree...")
    
    for idx, item in enumerate(items, 1):
        print(f"  Item {idx}: size={item:.3f}")
        
        # O(log n) query for best-fit bin
        result = avl_tree.find_best_bin(item)
        
        if result:
            old_capacity, best_bin = result
            
            # Remove old entry from tree: O(log n)
            avl_tree.remove_bin(old_capacity, best_bin)
            
            # Place item in bin
            best_bin.try_add(item)
            bin_idx = bins.index(best_bin)
            print(f"    -> Placed in Bin {bin_idx + 1} (remaining={best_bin.remaining:.3f})")
            
            # Insert updated entry: O(log n)
            avl_tree.insert_bin(best_bin.remaining, best_bin)
        else:
            # No suitable bin found, create new one
            new_bin = Bin()
            new_bin.try_add(item)
            bins.append(new_bin)
            print(f"    -> Created new Bin {len(bins)} (remaining={new_bin.remaining:.3f})")
            
            # Insert new bin into tree: O(log n)
            avl_tree.insert_bin(new_bin.remaining, new_bin)
    
    if flag == 0:
        print(f"[BF-AVL] Finished: Used {len(bins)} bins.\n")
    else:
        print(f"[BFD-AVL] Finished: Used {len(bins)} bins.\n")
    
    return len(bins), bins