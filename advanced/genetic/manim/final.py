from manim import *
import random

# ==========================================
# HELPER CLASSES
# ==========================================

class PackingItem(VGroup):
    def __init__(self, id, size, color=BLUE, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.size = size
        self.rect = Rectangle(
            height=size * 0.25, width=0.7, 
            fill_color=color, fill_opacity=0.9, 
            color=WHITE, stroke_width=1.5
        )
        self.label = Text(str(size), font_size=16).move_to(self.rect.get_center())
        self.add(self.rect, self.label)

class PackingBin(VGroup):
    def __init__(self, capacity=10, label="", color=WHITE, **kwargs):
        super().__init__(**kwargs)
        self.capacity = capacity
        self.items = [] 
        self.total_height = capacity * 0.25
        self.container = Rectangle(height=self.total_height + 0.2, width=1.0, color=color, stroke_width=3)
        self.label = Text(label, font_size=20, color=color).next_to(self.container, UP, buff=0.1)
        self.bg = Rectangle(height=self.total_height, width=1.0, color=color, fill_opacity=0.1, stroke_width=0)
        self.add(self.bg, self.container, self.label)

    def add_item_visual(self, item):
        # Calculate stack height using the ACTUAL visual height of items
        current_h = sum([i.rect.get_height() for i in self.items])
        
        # Calculate target Y position
        rect_height = item.rect.get_height()
        target_y = self.container.get_bottom()[1] + 0.1 + current_h + (rect_height / 2)
        
        target_pos = np.array([self.container.get_center()[0], target_y, 0])
        self.items.append(item)
        return target_pos

# ==========================================
# MAIN SCENE
# ==========================================

class HGGA_Full_Process(Scene):
    def construct(self):
        # Total Duration: ~1 min 45s
        
        # 1. Encoding (~15s)
        self.run_encoding()
        
        # 2. Fitness Function (~20s)
        self.run_fitness_logic()
        
        # 3. Tournament Selection (~15s)
        self.run_tournament()
        
        # 4. Marriage/Crossover + Replacement (~35s)
        self.run_marriage()
        
        # 5. Mutation (~20s)
        self.run_mutation()

    def run_encoding(self):
        title = Text("1. Group Encoding", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        sizes = [6, 4, 7, 3, 5, 5]
        items = VGroup(*[PackingItem(i, s, color=BLUE) for i, s in enumerate(sizes)])
        items.arrange(RIGHT, buff=0.15).shift(UP * 1.35)
        
        bins = VGroup(PackingBin(10, "A"), PackingBin(10, "B"), PackingBin(10, "C"))
        bins.arrange(RIGHT, buff=0.8).shift(DOWN * 1.1)
        
        self.play(FadeIn(items), Create(bins), run_time=1.5)

        moves = [
            items[0].animate.move_to(bins[0].add_item_visual(items[0])),
            items[1].animate.move_to(bins[0].add_item_visual(items[1])),
            items[2].animate.move_to(bins[1].add_item_visual(items[2])),
            items[3].animate.move_to(bins[1].add_item_visual(items[3])),
            items[4].animate.move_to(bins[2].add_item_visual(items[4])),
            items[5].animate.move_to(bins[2].add_item_visual(items[5])),
        ]
        self.play(*moves, run_time=2.0)
        
        set_a = Text("{0, 1}", font_size=28, color=YELLOW).move_to(bins[0].container.get_center())
        set_b = Text("{2, 3}", font_size=28, color=YELLOW).move_to(bins[1].container.get_center())
        set_c = Text("{4, 5}", font_size=28, color=YELLOW).move_to(bins[2].container.get_center())
        
        self.play(
            FadeOut(items), FadeOut(bins),
            FadeIn(set_a), FadeIn(set_b), FadeIn(set_c),
            run_time=1.5
        )

        gene_box = VGroup(set_a, set_b, set_c)
        self.play(gene_box.animate.arrange(RIGHT, buff=0.5).move_to(ORIGIN), run_time=1.5)
        
        brace = Brace(gene_box, sharpness=1.0)
        lbl = Text("Chromosome", font_size=24, color=YELLOW).next_to(brace, DOWN)
        
        self.play(Create(brace), Write(lbl), run_time=1.0)
        self.wait(1.0)
        self.play(FadeOut(Group(title, gene_box, brace, lbl)), run_time=0.5)

    def run_fitness_logic(self):
        title = Text("2. The Fitness Function", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        formula = MathTex(
            r"f_{BPP} = \frac{\sum (Fill_i / C)^k}{N}",
            font_size=36
        ).to_edge(UP).shift(RIGHT * 3).shift(DOWN*1.3)
        
        param_k = Text("k = 2 (Punish empty space)", font_size=20, color=YELLOW).next_to(formula, DOWN)
        
        self.play(Write(formula), run_time=1.5)
        self.play(FadeIn(param_k), run_time=1.0)

        ex_bins = VGroup(PackingBin(10, "Bin 1"), PackingBin(10, "Bin 2"))
        ex_bins.arrange(RIGHT, buff=2.5).shift(LEFT * 3 + DOWN * 0.5)
        
        it1 = PackingItem(0, 5, color=GREEN)
        it2 = PackingItem(0, 5, color=GREEN)
        it1.move_to(ex_bins[0].add_item_visual(it1))
        it2.move_to(ex_bins[0].add_item_visual(it2))

        it3 = PackingItem(0, 5, color=RED)
        it3.move_to(ex_bins[1].add_item_visual(it3))
        
        items_vgroup = VGroup(it1, it2, it3)
        self.play(Create(ex_bins), FadeIn(items_vgroup), run_time=1.5)

        score1 = MathTex(r"(\frac{10}{10})^2 = 1.0", color=GREEN, font_size=28).next_to(ex_bins[0], DOWN)
        score2 = MathTex(r"(\frac{5}{10})^2 = 0.25", color=RED, font_size=28).next_to(ex_bins[1], DOWN)
        
        self.play(Write(score1), Write(score2), run_time=1.5)
        self.wait(2.0)
        
        self.play(FadeOut(Group(title, formula, param_k, ex_bins, it1, it2, it3, score1, score2)), run_time=0.5)

    def run_tournament(self):
        title = Text("3. Tournament Selection", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        scores = [0.60, 0.85, 0.40, 0.90, 0.50, 0.70]
        pop = VGroup()
        for s in scores:
            bar = Rectangle(height=s*2.5, width=0.5, fill_color=GREY, fill_opacity=0.8, stroke_width=1)
            pop.add(bar)
        pop.arrange(RIGHT, buff=0.4).shift(DOWN*0.2)
        
        score_labels = VGroup()
        for bar, score in zip(pop, scores):
            lbl = Text(f"{score:.2f}", font_size=18, color=WHITE)
            lbl.next_to(bar, DOWN, buff=0.1)
            score_labels.add(lbl)
        
        pop_lbl = Text("Population", font_size=24, color=GREY).next_to(pop, UP, buff=0.3)
        
        self.play(FadeIn(pop), FadeIn(score_labels), Write(pop_lbl), run_time=1.0)

        # Selection Battle 1 (Parent A)
        c1, c2 = pop[0], pop[1]
        lbl1, lbl2 = score_labels[0], score_labels[1]
        box1 = SurroundingRectangle(VGroup(c1, lbl1), color=YELLOW, buff=0.1)
        box2 = SurroundingRectangle(VGroup(c2, lbl2), color=YELLOW, buff=0.1)
        self.play(Create(box1), Create(box2), run_time=0.5)
        
        winner_box = SurroundingRectangle(VGroup(c2, lbl2), color=GREEN, buff=0.1)
        self.play(ReplacementTransform(box2, winner_box), FadeOut(box1), run_time=1.0)
        
        pa_lbl = Text("Parent A", color=BLUE, font_size=24).to_edge(LEFT, buff=1.0).shift(UP)
        self.play(
            c2.animate.set_fill(BLUE),
            lbl2.animate.set_color(BLUE),
            Write(pa_lbl),
            FadeOut(winner_box),
            run_time=1.0
        )
        self.wait(0.5)

        # Selection Battle 2 (Parent B)
        c3, c4 = pop[3], pop[4]  # Scores 0.90 vs 0.50 (winner has higher fitness)
        lbl3, lbl4 = score_labels[3], score_labels[4]
        box3 = SurroundingRectangle(VGroup(c3, lbl3), color=YELLOW, buff=0.1)
        box4 = SurroundingRectangle(VGroup(c4, lbl4), color=YELLOW, buff=0.1)
        self.play(Create(box3), Create(box4), run_time=0.5)
        
        winner_box_2 = SurroundingRectangle(VGroup(c3, lbl3), color=GREEN, buff=0.1)
        self.play(ReplacementTransform(box3, winner_box_2), FadeOut(box4), run_time=1.0)
        
        pb_lbl = Text("Parent B", color=RED, font_size=24).to_edge(RIGHT, buff=1.0).shift(UP)
        self.play(
            c3.animate.set_fill(RED),
            lbl3.animate.set_color(RED),
            Write(pb_lbl),
            FadeOut(winner_box_2),
            run_time=1.0
        )
        self.wait(0.5)
        
        self.play(FadeOut(Group(pop, score_labels, pop_lbl, title, pa_lbl, pb_lbl)), run_time=0.5)

    def run_marriage(self):
        SCALE_FACTOR = 0.75
        title = Text("4. BPRX Crossover + Replacement", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # --- Setup Parents ---
        pa_lbl = Text("Parent A", color=BLUE, font_size=20).shift(UP*2 + LEFT*3)
        
        # Create 3 Bins for Parent A
        bins_a = VGroup(
            PackingBin(10,"",color=BLUE), PackingBin(10,"",color=BLUE), PackingBin(10,"",color=BLUE)
        ).arrange(RIGHT, buff=0.2).scale(SCALE_FACTOR).next_to(pa_lbl, DOWN)
        
        items_a = []
        def fill_bin(bin_obj, sz_list, item_list):
            for s in sz_list:
                it = PackingItem(0, s)
                it.scale(SCALE_FACTOR)
                it.move_to(bin_obj.add_item_visual(it))
                bin_obj.add(it)
                item_list.append(it)

        # Parent A Setup:
        # Bin 0: [6, 2] (Sum 8). Gap 2. (Target for Replacement)
        # Bin 1: [5, 4] (Sum 9). Conflict Bin (Contains 5).
        # Bin 2: [8]    (Sum 8). Gap 2. (Target for Re-insertion)
        fill_bin(bins_a[0], [6, 2], items_a) 
        fill_bin(bins_a[1], [5, 4], items_a)
        fill_bin(bins_a[2], [8], items_a)

        # Parent B (Injection): [5, 5]
        # Note: Injecting [5, 5] will conflict with the '5' in Bin 1
        pb_lbl = Text("Parent B", color=RED, font_size=20).shift(DOWN*0.75 + LEFT*3)
        inj_bin = PackingBin(10, "", color=RED).scale(SCALE_FACTOR)
        fill_bin(inj_bin, [5, 5], []) 
        inj_bin.next_to(pb_lbl, DOWN)

        self.play(FadeIn(pa_lbl), FadeIn(bins_a), FadeIn(pb_lbl), FadeIn(inj_bin), run_time=1.5)

        # 1. INJECTION
        inj_copy = inj_bin.copy()
        self.play(inj_copy.animate.next_to(bins_a, RIGHT, buff=0.2), run_time=1.5)

        # 2. ELIMINATION
        # Bin 1 contains '5'. Injection has '5'. Conflict!
        rect = SurroundingRectangle(bins_a[1], color=RED, buff=0.05)
        self.play(Create(rect), run_time=1.0)
        
        # Identify items in Bin 1
        duplicate_item = items_a[2] # Size 5
        innocent_item  = items_a[3] # Size 4 (This becomes loose)
        
        self.play(
            FadeOut(bins_a[1]), FadeOut(rect), FadeOut(duplicate_item), # Bin and Duplicate vanish
            innocent_item.animate.move_to(UP*0.5 + RIGHT*1.5).scale(0.8), # Innocent floats
            run_time=1.5
        )
        
        # Shift remaining bins to close the visual gap
        self.play(
            bins_a[2].animate.next_to(pa_lbl, DOWN).align_to(pa_lbl, LEFT).shift(RIGHT*1.0),
            inj_copy.animate.next_to(pa_lbl, DOWN).align_to(pa_lbl, LEFT).shift(RIGHT*2.0),
            run_time=1.0
        )

        # 3. REPLACEMENT (DOMINANCE)
        # Logic: Bin 0 has [6, 2] (Fill 8). Loose item is [4].
        # Action: Swap [2] for [4]. New Fill: 6+4 = 10 (Perfect!).
        # Improvement: 8 -> 10.
        
        rep_title = Text("Replacement Step", color=YELLOW, font_size=24).to_edge(RIGHT).shift(UP)
        self.play(Write(rep_title), run_time=0.5)
        
        target_bin = bins_a[0]
        item_to_eject = items_a[1] # The Size 2 item
        better_item   = innocent_item # The Size 4 item
        
        # Visual Arrow indicating the swap idea
        arrow = Arrow(better_item.get_center(), target_bin.get_center(), color=YELLOW)
        self.play(Create(arrow), run_time=1.0)
        
        # Perform the Swap
        self.play(
            item_to_eject.animate.move_to(better_item.get_center()), # Eject 2
            better_item.animate.move_to(target_bin.add_item_visual(better_item)), # Insert 4
            FadeOut(arrow),
            run_time=2.0
        )
        target_bin.add(better_item)
        
        # Highlight Bin 0 as Perfect (Green)
        green_bg_1 = Rectangle(height=target_bin.total_height, width=1.0, color=GREEN, fill_opacity=0.3, stroke_width=0).move_to(target_bin.bg.get_center())
        self.play(Transform(target_bin.bg, green_bg_1), run_time=0.5)

        # 4. RE-INSERTION
        # Loose item is now [2]. 
        # Target: Bin 2 has [8]. (Fill 8).
        # 8 + 2 = 10. Perfect Fit!
        
        loose_2 = item_to_eject
        target_reinsert = bins_a[2]
        
        self.play(
            loose_2.animate.move_to(target_reinsert.add_item_visual(loose_2)),
            run_time=1.5
        )
        target_reinsert.add(loose_2)
        
        # Highlight Bin 2 as Perfect (Green)
        green_bg_2 = Rectangle(height=target_reinsert.total_height, width=1.0, color=GREEN, fill_opacity=0.3, stroke_width=0).move_to(target_reinsert.bg.get_center())
        self.play(Transform(target_reinsert.bg, green_bg_2), run_time=0.5)
        
        # 5. FINAL RESULT
        # We started with mediocre bins. Now we have 3 Perfect Bins!
        final_grp = VGroup(bins_a[0], bins_a[2], inj_copy)
        final_box = SurroundingRectangle(final_grp, color=GREEN, buff=0.1)
        final_lbl = Text("Perfect Child Solution!", font_size=24, color=GREEN).next_to(final_box, UP)
        
        self.play(FadeOut(pa_lbl), run_time=0.5)
        self.play(Create(final_box), Write(final_lbl), FadeOut(rep_title), run_time=1.5)
        self.wait(2.0)
        cleanup_group = Group(title, pb_lbl, final_grp, final_box, final_lbl, inj_bin)
        self.play(FadeOut(cleanup_group), run_time=0.5)

    def run_mutation(self):
        SCALE_FACTOR = 0.75
        title = Text("5. Mutation Operator", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # --- Realistic 4-Bin Setup ---
        # Bin A: [5, 5] (Full)
        # Bin B: [6] (Slack 4)
        # Bin C: [2] (Slack 8)
        # Bin D: [4, 4] (Sum 8) - TARGET for Destruction
        bins = VGroup(
            PackingBin(10,"",color=BLUE), 
            PackingBin(10,"",color=BLUE), 
            PackingBin(10,"",color=BLUE), 
            PackingBin(10,"",color=BLUE)
        ).scale(SCALE_FACTOR).arrange(RIGHT, buff=0.4).shift(DOWN*0.5)
        
        items = []
        def fill(b, sz):
            for s in sz:
                it = PackingItem(0, s).scale(SCALE_FACTOR)
                it.move_to(b.add_item_visual(it))
                b.add(it); items.append(it)

        fill(bins[0], [5, 5])
        fill(bins[1], [6])    
        fill(bins[2], [2])
        fill(bins[3], [4, 4]) # Target for destruction
        
        # Important: fade in the entire bins group (which already contains the stacked items)
        # instead of re-parenting items into a new VGroup, otherwise items detach and disappear.
        self.play(FadeIn(bins), run_time=1.5)
        self.wait(0.5)

        # Action: Eliminate Bin D
        mut_lbl = Text("Eliminate Random Bin", color=RED, font_size=24).next_to(bins[3], UP)
        self.play(Write(mut_lbl), Indicate(bins[3], color=RED), run_time=1.5)
        
        loose_4a = items[-2] # First 4
        loose_4b = items[-1] # Second 4
        
        self.play(
            FadeOut(bins[3]), FadeOut(mut_lbl),
            loose_4a.animate.move_to(UP * 0.5 + LEFT), # Float up
            loose_4b.animate.move_to(UP * 0.5 + RIGHT), 
            run_time=1.5
        )
        
        # Re-insert 4a into Bin B (6+4=10)
        # Bin 1 has [6], item is [4]. Fits!
        self.play(
            loose_4a.animate.move_to(bins[1].add_item_visual(loose_4a)),
            run_time=1.0
        )
        
        # Re-insert 4b into Bin C (2+4=6)
        # Bin 2 has [2], item is [4]. Fits!
        self.play(
            loose_4b.animate.move_to(bins[2].add_item_visual(loose_4b)),
            run_time=1.0
        )
        
        # Final Highlight: 3 Bins!
        final_grp = VGroup(bins[0], bins[1], bins[2])
        final_box = SurroundingRectangle(final_grp, color=GREEN, buff=0.1)
        final_lbl = Text("Optimization: 4 Bins -> 3 Bins", font_size=24, color=GREEN).next_to(final_box, UP)
        
        self.play(Create(final_box), Write(final_lbl), run_time=1.0)
        self.wait(3.0)