from manim import *
import numpy as np

# Constants
CAPACITY = 524
K = 6
ITEMS_TO_ANIMATE = [442, 252, 252, 252, 127, 127, 85, 46, 12]
BIN_HEIGHT = 3  # Height of bins in the animation
BIN_WIDTH = 1  # Width of bins in the animation

# Harmonic intervals (normalized)
# I_1: (> 0.50 C) - Size > 262
# I_2: (> 0.33 C] - Size in (174.7, 262]
# I_3: (> 0.25 C] - Size in (131, 174.7]
# I_4: (> 0.20 C] - Size in (104.8, 131]
# I_5: (> 0.17 C] - Size in (87.3, 104.8]
# I_6: (<= 0.17 C] - Size <= 87.3

# Color scheme
GROUP_COLORS = [BLUE_D, ORANGE, GREEN_D, RED_D, PURPLE_D, MAROON_D]

# Harmonic thresholds (normalized sizes)
THRESHOLDS = [0.5, 1/3, 1/4, 1/5, 1/6]


def classify_item(item_size, capacity, k):
    """Classify item into one of k harmonic groups."""
    normalized_size = item_size / capacity
    
    for i in range(k - 1):
        if normalized_size > THRESHOLDS[i]:
            return i
    return k - 1  # Last group for smallest items


class HarmonicKScene(Scene):
    def construct(self):
        self.camera.background_color = BLACK
        
        # Create title
        title = Text("Harmonic-k Bin Packing (k=6)", font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        
        # Removed reference capacity rectangle & label (was visually distracting)
        
        # Create rules table on the left
        rules_table, rules_rows = self.create_rules_table()
        # Move table further left (more space from bins) and group rows tighter
        rules_table.to_edge(LEFT, buff=0.2).shift(UP * 0.5)
        self.play(Create(rules_table), run_time=1.5)
        self.wait(0.5)
        
        # Create zones at the bottom for each group
        zones, zone_centers = self.create_zones()
        shift_vec = DOWN * 2.5
        zones.shift(shift_vec)
        # Update zone centers after shifting
        zone_centers = [np.array(center) + shift_vec for center in zone_centers]
        self.play(Create(zones), run_time=1.5)
        self.wait(0.5)

    # Create a row of item numbers above the bins and to the right of the table
    top_number_labels = [Text(str(s), font_size=20, color=WHITE) for s in ITEMS_TO_ANIMATE]
    numbers_row = VGroup(*top_number_labels)
    numbers_row.arrange(RIGHT, buff=0.35)
    # Place the row to the right of the rules table
    numbers_row.next_to(rules_table, RIGHT, buff=0.6)
    # Lift the row so it sits above the top of the zones
    row_x = numbers_row.get_center()[0]
    row_y = zones.get_top()[1] + 0.8
    numbers_row.move_to([row_x, row_y, 0])
    self.play(Write(numbers_row), run_time=1.0)
    self.wait(0.3)
        
        # Initialize bin groups: each group has a list of bins
        # Each bin is a dict with:
        #   'items': list of item VGroups
        #   'sizes': list of item sizes (for calculation)
        #   'visual_bin': Rectangle
        bin_groups = [[] for _ in range(K)]
        all_items_visual = []  # Track all item VGroups for final scene
        
        # Animate each item
        for item_idx, item_size in enumerate(ITEMS_TO_ANIMATE):
            # Classify the item
            group_idx = classify_item(item_size, CAPACITY, K)
            
            # Create item rectangle - use BIN_HEIGHT for consistency with actual bins
            item_height = (item_size / CAPACITY) * BIN_HEIGHT
            item_rect = Rectangle(
                height=item_height,
                width=0.8,
                color=GROUP_COLORS[group_idx],
                fill_color=GROUP_COLORS[group_idx],
                fill_opacity=0.8,
                stroke_width=2
            )
            
            # Reuse the corresponding top number label and animate it with the item
            num_label = top_number_labels[item_idx]
            
            # Start position (near rules table, since reference bin removed)
            spawn_anchor = rules_table.get_right() + np.array([1.0, -1.0, 0])
            start_pos = spawn_anchor
            # Position rectangle and bring the number label down to its center
            item_rect.move_to(start_pos)
            self.play(FadeIn(item_rect), num_label.animate.move_to(item_rect.get_center()), run_time=0.6)
            item = VGroup(item_rect, num_label)
            self.wait(0.4)
            
            # Highlight the classification in rules table
            self.play(Indicate(rules_rows[group_idx], color=YELLOW), run_time=0.8)
            self.wait(0.4)
            
            # Move item to its zone (center of zone initially)
            target_zone_center = zone_centers[group_idx]
            self.play(item.animate.move_to([target_zone_center[0], target_zone_center[1], 0]), run_time=1.2)
            self.wait(0.4)
            
            # Try to pack the item (First-Fit within group)
            packed = False
            existing_bins = bin_groups[group_idx]
            zone_x = zone_centers[group_idx][0]
            zone_y = zone_centers[group_idx][1]
            # Calculate zone bottom properly using zone height
            zone_bottom = zone_y - (BIN_HEIGHT / 2)  # Bottom of zone (zone center - half height)
            
            # Bin spacing
            bin_spacing = 1.2
            
            for bin_idx, bin_data in enumerate(existing_bins):
                bin_visual_items = bin_data['items']  # List of item VGroups in this bin
                bin_sizes = bin_data['sizes']  # List of item sizes
                visual_bin = bin_data['visual_bin']
                bin_x = visual_bin.get_center()[0]  # Get actual x position from visual bin
                
                # Calculate current fill of this bin
                current_fill = sum(bin_sizes)
                remaining_space = CAPACITY - current_fill
                
                # Calculate cumulative height of items already in bin (in visual units)
                cumulative_height = (current_fill / CAPACITY) * BIN_HEIGHT
                
                # Show checking animation - move item above the bin
                check_y = zone_bottom + cumulative_height + item_height / 2
                check_pos = np.array([bin_x, check_y + 0.4, 0])
                
                # Move item to check position
                self.play(item.animate.move_to(check_pos), run_time=0.5)
                self.wait(0.3)
                
                if item_size <= remaining_space:
                    # Item fits - pack it into this bin
                    # Position item at the top of the current stack
                    final_y = zone_bottom + cumulative_height + (item_height / 2)
                    final_pos = np.array([bin_x, final_y, 0])
                    
                    self.play(item.animate.move_to(final_pos), run_time=0.7)
                    bin_data['items'].append(item)
                    bin_data['sizes'].append(item_size)
                    all_items_visual.append(item)
                    packed = True
                    self.wait(0.4)
                    break
                else:
                    # Item doesn't fit - show failure
                    fail_x = VGroup(
                        Line(UL, DR, color=RED, stroke_width=4),
                        Line(UR, DL, color=RED, stroke_width=4)
                    ).scale(0.4)
                    fail_x.move_to(item.get_center())
                    self.add(fail_x)
                    self.play(Wiggle(item, scale_factor=1.3), run_time=0.6)
                    self.play(FadeOut(fail_x), run_time=0.3)
                    self.wait(0.3)
            
            if not packed:
                # Need to create a new bin
                # Position new bin to the right of existing bins
                if len(existing_bins) > 0:
                    last_bin = existing_bins[-1]['visual_bin']
                    bin_x = last_bin.get_center()[0] + bin_spacing
                else:
                    # First bin in zone - center it in the zone
                    bin_x = zone_x
                
                # Create empty bin rectangle
                new_bin_rect = Rectangle(
                    height=BIN_HEIGHT,
                    width=BIN_WIDTH,
                    color=GROUP_COLORS[group_idx],
                    stroke_width=2,
                    stroke_opacity=0.6,
                    fill_opacity=0
                )
                # Center bin vertically in zone (zone center is at zone_y)
                new_bin_rect.move_to([bin_x, zone_y, 0])
                self.play(Create(new_bin_rect), run_time=0.6)
                self.wait(0.3)
                
                # Pack item into new bin (at the bottom)
                final_y = zone_bottom + (item_height / 2)
                final_pos = np.array([bin_x, final_y, 0])
                self.play(item.animate.move_to(final_pos), run_time=0.7)
                
                # Store the bin
                bin_groups[group_idx].append({
                    'items': [item],  # Store the item VGroup
                    'sizes': [item_size],  # Store the item size
                    'visual_bin': new_bin_rect
                })
                all_items_visual.append(item)
                self.wait(0.4)
        
        # Wait a moment before final scene
        self.wait(2)
        
        # Collect all visual bins
        all_visual_bins = []
        for group_bins in bin_groups:
            for bin_data in group_bins:
                all_visual_bins.append(bin_data['visual_bin'])
        
        # Collect all items and bins into a single VGroup for proper centering
        all_objects_list = list(all_items_visual) + list(all_visual_bins)
        if len(all_objects_list) == 0:
            # No objects to display
            return
        
        # Create VGroup for proper bounding box calculations
        all_objects = VGroup(*all_objects_list)
        
        # Calculate total bins
        total_bins = sum(len(bins) for bins in bin_groups)
        
        # Calculate theoretical optimal (ceiling of sum of items / capacity)
        total_items = sum(ITEMS_TO_ANIMATE)
        optimal = int(np.ceil(total_items / CAPACITY))
        
        # Fade out rules table, title, and zones (reference bin removed earlier)
        to_fade = VGroup(rules_table, title, zones)
        self.play(FadeOut(to_fade), run_time=1.5)
        self.wait(0.8)
        
        # Center and frame all bins - calculate proper center
        # Get the bounding box of all objects before shifting
        all_center = all_objects.get_center()
        # Calculate shift to center objects on screen (horizontally centered, slightly above center vertically)
        target_x = 0  # Center horizontally
        target_y = 0.5  # Position objects slightly above center for summary text space
        shift_vec = np.array([target_x - all_center[0], target_y - all_center[1], 0])
        
        # Apply shift to all objects using individual animations to maintain relative positions
        shift_anims = [obj.animate.shift(shift_vec) for obj in all_objects_list]
        self.play(*shift_anims, run_time=1.5)
        self.wait(0.8)
        
        # Recreate VGroup after shift to get updated positions for summary text positioning
        all_objects = VGroup(*all_objects_list)
        
        # Create summary text
        summary_text = VGroup(
            Text(f"Algorithm Bins: {total_bins}", font_size=36, color=WHITE),
            Text(f"Theoretical Optimal: {optimal}", font_size=36, color=WHITE)
        )
        summary_text.arrange(DOWN, buff=0.4)
        
        # Position summary text above the bins
        # Get the top of the all_objects VGroup after shifting (objects are already shifted)
        all_objects_top = all_objects.get_top()[1]
        summary_y = all_objects_top + 1.2
        summary_text.move_to([0, summary_y, 0])
        
        self.play(Write(summary_text), run_time=1.5)
        self.wait(3)
    
    def create_rules_table(self):
        """Create a table showing the harmonic groups, intervals, and colors."""
        # Group definitions
        group_labels = [
            (r"$I_1$", "(> 0.50 C)", "Size > 262"),
            (r"$I_2$", "(> 0.33 C]", "Size in (174.7, 262]"),
            (r"$I_3$", "(> 0.25 C]", "Size in (131, 174.7]"),
            (r"$I_4$", "(> 0.20 C]", "Size in (104.8, 131]"),
            (r"$I_5$", "(> 0.17 C]", "Size in (87.3, 104.8]"),
            (r"$I_6$", "(<= 0.17 C]", "Size <= 87.3"),
        ]
        
        table_rows = []
        for i, (group_name, interval, desc) in enumerate(group_labels):
            # Create colored square indicator
            color_square = Square(
                side_length=0.3,
                color=GROUP_COLORS[i],
                fill_color=GROUP_COLORS[i],
                fill_opacity=0.8
            )
            
            group_text = Tex(group_name, font_size=14, color=WHITE)
            interval_text = Text(interval, font_size=12, color=WHITE)
            desc_text = Text(desc, font_size=10, color=GRAY)
            
            row = VGroup(color_square, group_text, interval_text, desc_text)
            # Tighter internal spacing between columns
            row.arrange(RIGHT, buff=0.2)
            table_rows.append(row)
        
        # Arrange all rows
        all_rows = VGroup(*table_rows)
        all_rows.arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        
        return all_rows, table_rows
    
    def create_zones(self):
        """Create 6 zones at the bottom for bins of each group."""
        zones = VGroup()
        zone_width = 1.3
        zone_height = BIN_HEIGHT  # Use BIN_HEIGHT constant for consistency
        
        zone_centers = []
        
        # Calculate total width needed
        total_width = K * zone_width + (K - 1) * 0.1
        start_x = -total_width / 2 + zone_width / 2
        
        for i in range(K):
            zone_x = start_x + i * (zone_width + 0.1)
            zone_y = 0  # Will be shifted later
            
            zone = Rectangle(
                height=zone_height,
                width=zone_width,
                color=GROUP_COLORS[i],
                stroke_width=2,
                stroke_opacity=0.3,
                fill_opacity=0
            )
            zone.move_to([zone_x, zone_y, 0])
            
            zone_label = Tex(rf"$I_{{{i+1}}}$", font_size=20, color=GROUP_COLORS[i])
            zone_label.next_to(zone, UP, buff=0.1)
            
            zone_group = VGroup(zone, zone_label)
            zones.add(zone_group)
            
            zone_centers.append(np.array([zone_x, zone_y, 0]))
        
        return zones, zone_centers

