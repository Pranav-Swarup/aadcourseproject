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
        current_h = sum([i.size for i in self.items]) * 0.25
        target_y = self.container.get_bottom()[1] + 0.1 + current_h + (item.rect.height / 2)
        target_pos = np.array([self.container.get_center()[0], target_y, 0])
        self.items.append(item)
        return target_pos

# ==========================================
# MAIN SCENE
# ==========================================

class HGGA_Final_Timed(Scene):
    def construct(self):
        # Estimated Duration: ~50 seconds
        
        # 1. Encoding (~15s)
        self.run_encoding()
        
        # 2. Tournament Selection (~15s)
        self.run_tournament()
        
        # 3. Marriage/Crossover (~20s)
        self.run_marriage()

    def run_encoding(self):
        # Title
        title = Text("1. Group Encoding", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Setup Items & Bins
        sizes = [6, 4, 7, 3, 5, 5]
        items = VGroup(*[PackingItem(i, s, color=BLUE) for i, s in enumerate(sizes)])
        items.arrange(RIGHT, buff=0.15).shift(UP * 1.0)
        
        bins = VGroup(PackingBin(10, "A"), PackingBin(10, "B"), PackingBin(10, "C"))
        bins.arrange(RIGHT, buff=0.8).shift(DOWN * 0.5)
        
        self.play(FadeIn(items), Create(bins), run_time=1.5)
        self.wait(1.0) # Pause to let viewer see the setup

        # Fast Packing
        moves = [
            items[0].animate.move_to(bins[0].add_item_visual(items[0])),
            items[1].animate.move_to(bins[0].add_item_visual(items[1])),
            items[2].animate.move_to(bins[1].add_item_visual(items[2])),
            items[3].animate.move_to(bins[1].add_item_visual(items[3])),
            items[4].animate.move_to(bins[2].add_item_visual(items[4])),
            items[5].animate.move_to(bins[2].add_item_visual(items[5])),
        ]
        self.play(*moves, run_time=2.0) # Slowed down packing
        self.wait(1.0)

        # Transform to Sets
        set_a = Text("{0, 1}", font_size=28, color=YELLOW).move_to(bins[0].container.get_center())
        set_b = Text("{2, 3}", font_size=28, color=YELLOW).move_to(bins[1].container.get_center())
        set_c = Text("{4, 5}", font_size=28, color=YELLOW).move_to(bins[2].container.get_center())
        
        self.play(
            FadeOut(items), FadeOut(bins),
            FadeIn(set_a), FadeIn(set_b), FadeIn(set_c),
            run_time=1.5
        )
        self.wait(1.0)

        # Align as Chromosome
        gene_box = VGroup(set_a, set_b, set_c)
        self.play(gene_box.animate.arrange(RIGHT, buff=0.5).move_to(ORIGIN), run_time=1.5)
        
        brace = Brace(gene_box, sharpness=1.0)
        lbl = Text("Chromosome", font_size=24, color=YELLOW).next_to(brace, DOWN)
        
        self.play(Create(brace), Write(lbl), run_time=1.0)
        self.wait(2.0) # Long pause to read the final state
        
        self.play(FadeOut(Group(title, gene_box, brace, lbl)), run_time=0.5)

    def run_tournament(self):
        title = Text("2. Tournament Selection", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Population Bars
        scores = [0.6, 0.85, 0.4, 0.9, 0.5, 0.7]
        pop = VGroup()
        for s in scores:
            bar = Rectangle(height=s*2.5, width=0.5, fill_color=GREY, fill_opacity=0.8, stroke_width=1)
            pop.add(bar)
        
        pop.arrange(RIGHT, buff=0.4).shift(DOWN*0.2)
        pop_lbl = Text("Population", font_size=24, color=GREY).next_to(pop, UP, buff=0.3)
        
        self.play(FadeIn(pop), Write(pop_lbl), run_time=1.0)
        self.wait(1.5)

        # Selection 1
        c1, c2 = pop[0], pop[1]
        box1 = SurroundingRectangle(c1, color=YELLOW, buff=0.05)
        box2 = SurroundingRectangle(c2, color=YELLOW, buff=0.05)
        self.play(Create(box1), Create(box2), run_time=0.5)
        self.wait(0.5)
        
        winner_box = SurroundingRectangle(c2, color=GREEN, buff=0.05)
        self.play(ReplacementTransform(box2, winner_box), FadeOut(box1), run_time=1.0)
        
        pa_lbl = Text("Parent A", color=BLUE, font_size=24).to_edge(LEFT, buff=1.0).shift(UP)
        self.play(c2.animate.set_fill(BLUE), Write(pa_lbl), FadeOut(winner_box), run_time=1.0)
        self.wait(1.0)

        # Selection 2
        c3, c4 = pop[3], pop[5]
        box3 = SurroundingRectangle(c3, color=YELLOW, buff=0.05)
        box4 = SurroundingRectangle(c4, color=YELLOW, buff=0.05)
        self.play(Create(box3), Create(box4), run_time=0.5)
        self.wait(0.5)
        
        winner_box_2 = SurroundingRectangle(c3, color=GREEN, buff=0.05)
        self.play(ReplacementTransform(box3, winner_box_2), FadeOut(box4), run_time=1.0)
        
        pb_lbl = Text("Parent B", color=RED, font_size=24).to_edge(RIGHT, buff=1.0).shift(UP)
        self.play(c3.animate.set_fill(RED), Write(pb_lbl), FadeOut(winner_box_2), run_time=1.0)
        
        self.wait(2.0)
        self.play(FadeOut(Group(pop, pop_lbl, title, pa_lbl, pb_lbl)), run_time=0.5)

    def run_marriage(self):
        # Scaling factor to keep things on screen
        SCALE_FACTOR = 0.75
        
        title = Text("3. BPRX Crossover", font_size=32).to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # --- Setup Parents ---
        pa_lbl = Text("Parent A", color=BLUE, font_size=20).shift(UP*2 + LEFT*3)
        
        bins_a = VGroup(
            PackingBin(10,"",color=BLUE), PackingBin(10,"",color=BLUE), PackingBin(10,"",color=BLUE)
        ).arrange(RIGHT, buff=0.2).scale(SCALE_FACTOR).next_to(pa_lbl, DOWN)
        
        items_a = []
        # Helper to fill scaled bins
        def fill_bin(bin_obj, sz_list, item_list):
            for s in sz_list:
                it = PackingItem(0, s)
                it.scale(SCALE_FACTOR)
                it.move_to(bin_obj.add_item_visual(it))
                bin_obj.add(it)
                item_list.append(it)

        fill_bin(bins_a[0], [5, 5], items_a)
        fill_bin(bins_a[1], [6, 4], items_a)
        fill_bin(bins_a[2], [8], items_a)

        # Parent B (Injection)
        pb_lbl = Text("Parent B (Injection)", color=RED, font_size=20).shift(DOWN*0.5 + LEFT*3)
        inj_bin = PackingBin(10, "", color=RED).scale(SCALE_FACTOR)
        fill_bin(inj_bin, [5, 4], []) 
        inj_bin.next_to(pb_lbl, DOWN)

        self.play(FadeIn(pa_lbl), FadeIn(bins_a), FadeIn(pb_lbl), FadeIn(inj_bin), run_time=1.5)
        self.wait(1.0)

        # --- Step 1: Injection ---
        # Fixed position: Move text closer to center to avoid edge cutoff
        txt_pos = UP*2 + RIGHT*1.0 
        txt1 = Text("1. Inject", color=YELLOW, font_size=24).move_to(txt_pos)
        self.play(Write(txt1), run_time=0.5)
        
        inj_copy = inj_bin.copy()
        self.play(inj_copy.animate.next_to(bins_a, RIGHT, buff=0.2), run_time=1.5)
        self.wait(1.0)

        # --- Step 2: Eliminate ---
        txt2 = Text("2. Eliminate Conflicts", color=YELLOW, font_size=24).next_to(txt1, DOWN)
        self.play(Write(txt2), run_time=0.5)

        rects = VGroup(
            SurroundingRectangle(bins_a[0], color=RED, buff=0.05),
            SurroundingRectangle(bins_a[1], color=RED, buff=0.05)
        )
        self.play(Create(rects), run_time=1.0)
        self.wait(0.5)
        
        loose_1 = items_a[0]
        loose_2 = items_a[2]
        
        self.play(
            FadeOut(bins_a[0]), FadeOut(bins_a[1]), FadeOut(rects),
            loose_1.animate.move_to(UP*0.5 + RIGHT*0.5).scale(0.8),
            loose_2.animate.move_to(UP*0.5 + RIGHT*1.5).scale(0.8),
            run_time=1.5
        )
        
        self.play(
            bins_a[2].animate.next_to(pa_lbl, DOWN).align_to(pa_lbl, LEFT),
            inj_copy.animate.next_to(pa_lbl, DOWN).align_to(pa_lbl, LEFT).shift(RIGHT*1.0), 
            run_time=1.5
        )
        self.wait(1.0)

        # --- Step 3: Re-insert ---
        txt3 = Text("3. Re-insert", color=YELLOW, font_size=24).next_to(txt2, DOWN)
        self.play(Write(txt3), run_time=0.5)
        
        new_bin_1 = PackingBin(10, "", color=GREEN).scale(SCALE_FACTOR).next_to(inj_copy, RIGHT, buff=0.2)
        new_bin_2 = PackingBin(10, "", color=GREEN).scale(SCALE_FACTOR).next_to(new_bin_1, RIGHT, buff=0.2)
        
        self.play(Create(new_bin_1), Create(new_bin_2), run_time=1.0)
        
        self.play(
            loose_1.animate.move_to(new_bin_1.add_item_visual(loose_1)),
            loose_2.animate.move_to(new_bin_2.add_item_visual(loose_2)),
            run_time=2.0 # Slower movement for clarity
        )
        
        final_grp = VGroup(bins_a[2], inj_copy, new_bin_1, new_bin_2)
        final_box = SurroundingRectangle(final_grp, color=WHITE, buff=0.1)
        final_lbl = Text("Child", font_size=24).next_to(final_box, UP)
        
        self.play(Create(final_box), Write(final_lbl), run_time=1.0)
        self.wait(3.0) # Final hold