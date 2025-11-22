from manim import *
import random

# ==========================================
# HELPER CLASSES (Visual Logic)
# ==========================================

class PackingItem(VGroup):
    def __init__(self, id, size, color=BLUE, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.size = size
        # Height scales with size (Size 1 = 0.3 units high)
        self.rect = Rectangle(
            height=size * 0.3, width=0.8, 
            fill_color=color, fill_opacity=0.9, 
            color=WHITE, stroke_width=2
        )
        self.label = Text(str(size), font_size=20).move_to(self.rect.get_center())
        self.add(self.rect, self.label)

class PackingBin(VGroup):
    def __init__(self, capacity=10, label="", color=WHITE, **kwargs):
        super().__init__(**kwargs)
        self.capacity = capacity
        self.items = [] 
        self.total_height = capacity * 0.3
        
        # Container Visuals
        self.container = Rectangle(height=self.total_height + 0.2, width=1.2, color=color, stroke_width=4)
        self.label = Text(label, font_size=20, color=color).next_to(self.container, UP)
        self.bg = Rectangle(height=self.total_height, width=1.2, color=color, fill_opacity=0.1, stroke_width=0)
        
        self.add(self.bg, self.container, self.label)

    def add_item_visual(self, item):
        # Logic to stack items visually from bottom up
        current_h = sum([i.size for i in self.items]) * 0.3
        target_y = self.container.get_bottom()[1] + 0.1 + current_h + (item.rect.height / 2)
        target_pos = np.array([self.container.get_center()[0], target_y, 0])
        self.items.append(item)
        return target_pos

# ==========================================
# MAIN SCENE
# ==========================================

class HGGA_Unified_Process(Scene):
    def construct(self):
        # 1. Encoding (Fast & Concise)
        self.run_encoding()
        
        # 2. Tournament Selection
        self.run_tournament()
        
        # 3. Marriage (BPRX Crossover)
        self.run_marriage()

    def run_encoding(self):
        # --- Setup ---
        title = Text("1. Encoding: Group Oriented", font_size=36).to_edge(UP)
        self.play(Write(title), run_time=0.5)

        # Create loose items
        sizes = [6, 4, 7, 3, 5, 5]
        items = VGroup()
        for i, s in enumerate(sizes):
            items.add(PackingItem(i, s, color=BLUE))
        items.arrange(RIGHT, buff=0.2).shift(UP)
        
        # Create Bins (The Solution)
        bins = VGroup(
            PackingBin(10, "Bin A"), PackingBin(10, "Bin B"), PackingBin(10, "Bin C")
        ).arrange(RIGHT, buff=1).shift(DOWN)
        
        self.play(FadeIn(items), Create(bins), run_time=0.8)

        # --- Fast Packing Animation ---
        # Hardcoded logic for speed: [6,4] -> A, [7,3] -> B, [5,5] -> C
        moves = []
        # Bin A
        moves.append(items[0].animate.move_to(bins[0].add_item_visual(items[0])))
        moves.append(items[1].animate.move_to(bins[0].add_item_visual(items[1])))
        # Bin B
        moves.append(items[2].animate.move_to(bins[1].add_item_visual(items[2])))
        moves.append(items[3].animate.move_to(bins[1].add_item_visual(items[3])))
        # Bin C
        moves.append(items[4].animate.move_to(bins[2].add_item_visual(items[4])))
        moves.append(items[5].animate.move_to(bins[2].add_item_visual(items[5])))
        
        self.play(*moves, run_time=1.2)

        # --- The Concept: Bins ARE Genes ---
        # Draw boxes to show they become genes
        gene_boxes = VGroup()
        for b in bins:
            gene_boxes.add(SurroundingRectangle(b, color=YELLOW, buff=0.1))
        
        gene_label = Text("One Bin = One Gene", color=YELLOW, font_size=30).next_to(bins, UP, buff=0.5)
        
        self.play(Create(gene_boxes), Write(gene_label), run_time=0.8)
        self.wait(0.5)
        
        # Cleanup
        self.play(FadeOut(Group(items, bins, gene_boxes, gene_label, title)), run_time=0.5)

    def run_tournament(self):
        title = Text("2. Tournament Selection", font_size=36).to_edge(UP)
        self.play(Write(title), run_time=0.5)

        # Visual Representation of Population (Bars with fitness scores)
        scores = [0.6, 0.85, 0.4, 0.9, 0.5, 0.7]
        pop_group = VGroup()
        for i, s in enumerate(scores):
            # Bar height represents fitness
            bar = Rectangle(height=s*3, width=0.8, fill_color=GREY, fill_opacity=0.8, stroke_color=WHITE)
            lbl = Text(f"{s}", font_size=16).next_to(bar, DOWN)
            pop_group.add(VGroup(bar, lbl))
        
        pop_group.arrange(RIGHT, buff=0.5)
        self.play(FadeIn(pop_group), run_time=0.5)

        # --- Selection 1 (Parent A) ---
        # Randomly pick Index 0 (0.6) and Index 1 (0.85)
        c1, c2 = pop_group[0], pop_group[1]
        
        # Highlight Contenders
        box1 = SurroundingRectangle(c1, color=YELLOW)
        box2 = SurroundingRectangle(c2, color=YELLOW)
        self.play(Create(box1), Create(box2), run_time=0.5)
        
        # Determine Winner
        winner_rect = SurroundingRectangle(c2, color=GREEN)
        self.play(ReplacementTransform(box2, winner_rect), FadeOut(box1), run_time=0.5)
        
        # Move Winner to "Parent A" slot
        parent_a_lbl = Text("Parent A", color=BLUE, font_size=24).to_edge(LEFT).shift(UP)
        self.play(c2[0].animate.set_fill(BLUE), Write(parent_a_lbl), run_time=0.5)
        self.play(FadeOut(winner_rect))

        # --- Selection 2 (Parent B) ---
        # Randomly pick Index 3 (0.9) and Index 5 (0.7)
        c3, c4 = pop_group[3], pop_group[5]
        
        box3 = SurroundingRectangle(c3, color=YELLOW)
        box4 = SurroundingRectangle(c4, color=YELLOW)
        self.play(Create(box3), Create(box4), run_time=0.5)
        
        # Determine Winner (0.9)
        winner_rect2 = SurroundingRectangle(c3, color=GREEN)
        self.play(ReplacementTransform(box3, winner_rect2), FadeOut(box4), run_time=0.5)
        
        # Move Winner to "Parent B" slot
        parent_b_lbl = Text("Parent B", color=RED, font_size=24).to_edge(RIGHT).shift(UP)
        self.play(c3[0].animate.set_fill(RED), Write(parent_b_lbl), run_time=0.5)
        
        self.wait(0.5)
        self.play(FadeOut(Group(pop_group, winner_rect2, title, parent_a_lbl, parent_b_lbl)))

    def run_marriage(self):
        title = Text("3. Marriage (BPRX Crossover)", font_size=36).to_edge(UP)
        self.play(Write(title), run_time=0.5)

        # --- Detailed Parent Setup ---
        # Parent A (Blue)
        # Bin A1: [1, 2] (Sizes 5, 5)
        # Bin A2: [3, 4] (Sizes 6, 4)
        # Bin A3: [5]    (Size 8)
        
        pa_lbl = Text("Parent A", color=BLUE, font_size=24).shift(UP*2 + LEFT*3)
        bins_a = VGroup(
            PackingBin(10, "", color=BLUE), PackingBin(10, "", color=BLUE), PackingBin(10, "", color=BLUE)
        ).arrange(RIGHT, buff=0.2).next_to(pa_lbl, DOWN)
        
        # Items for A (Track IDs for conflict!)
        # Item ID 1 (Size 5), ID 2 (Size 5) -> Bin 0
        # Item ID 3 (Size 6), ID 4 (Size 4) -> Bin 1
        # Item ID 5 (Size 8)                -> Bin 2
        
        items_a_data = [
            (0, [PackingItem(1, 5), PackingItem(2, 5)]),
            (1, [PackingItem(3, 6), PackingItem(4, 4)]),
            (2, [PackingItem(5, 8)])
        ]
        
        # Visual Packing A
        all_items_a = []
        for bin_idx, items in items_a_data:
            for it in items:
                it.move_to(bins_a[bin_idx].add_item_visual(it))
                bins_a[bin_idx].add(it)
                all_items_a.append(it)

        # Parent B (Red) - The Donor
        # Contains a "Super Bin" with ID 2 and ID 3 (Size 5 and 6? No, 5+6=11 overflow. Let's say Size 5 and 4)
        # Let's adjust: 
        # Injected Bin has: Item 2 (Size 5) and Item 4 (Size 4). Total 9.
        pb_lbl = Text("Parent B", color=RED, font_size=24).shift(DOWN*1 + LEFT*3)
        bin_b_special = PackingBin(10, "Injection", color=RED)
        
        # Items in Donor Bin
        d_item2 = PackingItem(2, 5, color=RED_C) # DUPLICATE of ID 2
        d_item4 = PackingItem(4, 4, color=RED_C) # DUPLICATE of ID 4
        d_item2.move_to(bin_b_special.add_item_visual(d_item2))
        d_item4.move_to(bin_b_special.add_item_visual(d_item4))
        bin_b_special.add(d_item2, d_item4)
        
        bin_b_special.next_to(pb_lbl, DOWN)
        
        self.play(FadeIn(pa_lbl), FadeIn(bins_a), FadeIn(pb_lbl), FadeIn(bin_b_special))
        
        # --- Step 1: Injection ---
        inj_txt = Text("Injection", font_size=24, color=YELLOW).to_edge(RIGHT).shift(UP)
        self.play(Write(inj_txt))
        
        injected_copy = bin_b_special.copy()
        # Move to end of Parent A
        self.play(injected_copy.animate.next_to(bins_a, RIGHT, buff=0.2))
        
        # --- Step 2: Elimination ---
        elim_txt = Text("Eliminate Conflicts", font_size=24, color=YELLOW).next_to(inj_txt, DOWN)
        self.play(Write(elim_txt))

        # Highlight Conflicts
        # Item 2 is in Bin A[0]
        # Item 4 is in Bin A[1]
        
        conflict_rects = VGroup(
            SurroundingRectangle(bins_a[0], color=RED),
            SurroundingRectangle(bins_a[1], color=RED)
        )
        self.play(Create(conflict_rects))
        self.play(
            Indicate(all_items_a[1], color=RED), # Item 2
            Indicate(all_items_a[3], color=RED)  # Item 4
        )
        
        # Destroy Bins A[0] and A[1]
        # Identify Loose items: Item 1 (from Bin 0) and Item 3 (from Bin 1)
        loose_item_1 = all_items_a[0] # Size 5
        loose_item_3 = all_items_a[2] # Size 6
        
        self.play(
            FadeOut(bins_a[0].container), FadeOut(bins_a[0].bg), FadeOut(all_items_a[1]), # Delete bin and dup item
            FadeOut(bins_a[1].container), FadeOut(bins_a[1].bg), FadeOut(all_items_a[3]), # Delete bin and dup item
            FadeOut(conflict_rects),
            loose_item_1.animate.move_to(UP*0.5 + RIGHT*1), # Float loose items
            loose_item_3.animate.move_to(UP*0.5 + RIGHT*2)
        )
        
        # Re-arrange remaining A bins (Bin 2 and Injected)
        self.play(
            bins_a[2].animate.next_to(pa_lbl, DOWN).align_to(pa_lbl, LEFT), # Move Bin A3 to start
            injected_copy.animate.next_to(pa_lbl, DOWN).align_to(pa_lbl, LEFT).shift(RIGHT*1.5) # Move Injected next to it
        )

        # --- Step 3: Re-insertion ---
        rein_txt = Text("Re-insert Loose Items", font_size=24, color=YELLOW).next_to(elim_txt, DOWN)
        self.play(Write(rein_txt))
        
        # Loose Item 1 (Size 5).
        # Available Bins: 
        # 1. Old Bin A3 (Has Item 5, Size 8). Capacity 10. Space 2. 5 > 2. No fit.
        # 2. Injected Bin (Has 5+4=9). Capacity 10. Space 1. 5 > 1. No fit.
        # Result: New Bin.
        
        # Loose Item 3 (Size 6). Same issue.
        
        # Let's cheat the visual slightly to show one successful insertion.
        # Let's pretend Old Bin A3 had size 4 (Space 6).
        # We will create a New Bin for Item 1.
        
        new_bin = PackingBin(10, "New", color=GREEN)
        new_bin.next_to(injected_copy, RIGHT, buff=0.2)
        self.play(Create(new_bin))
        
        # Move Item 1 into New Bin
        target_pos = new_bin.add_item_visual(loose_item_1)
        self.play(loose_item_1.animate.move_to(target_pos))
        new_bin.add(loose_item_1)
        
        # Move Item 3 into New Bin (Size 5 + 6 = 11? Overflow)
        # Need ANOTHER New Bin.
        new_bin_2 = PackingBin(10, "New 2", color=GREEN)
        new_bin_2.next_to(new_bin, RIGHT, buff=0.2)
        self.play(Create(new_bin_2))
        
        target_pos_2 = new_bin_2.add_item_visual(loose_item_3)
        self.play(loose_item_3.animate.move_to(target_pos_2))
        new_bin_2.add(loose_item_3)
        
        self.wait(1)
        
        # Final Frame
        final_rect = SurroundingRectangle(VGroup(bins_a[2], injected_copy, new_bin, new_bin_2), color=WHITE, buff=0.2)
        final_lbl = Text("Child Solution", font_size=32).next_to(final_rect, UP)
        self.play(Create(final_rect), Write(final_lbl))
        self.wait(2)