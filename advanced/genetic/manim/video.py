from manim import *
import random

# --- Helper Classes (Simplified for this scene) ---
class ChromosomeVisual(VGroup):
    def __init__(self, fitness, id, color=BLUE, **kwargs):
        super().__init__(**kwargs)
        self.fitness = fitness
        # Visual: A bar where height = fitness
        self.bar = RoundedRectangle(corner_radius=0.1, height=1 + (fitness * 2), width=0.8, color=WHITE, fill_color=color, fill_opacity=0.8)
        self.label = Text(f"{fitness:.2f}", font_size=20).move_to(self.bar.get_center())
        self.id_label = Text(f"Sol {id}", font_size=16).next_to(self.bar, DOWN)
        self.add(self.bar, self.label, self.id_label)

class PackingItem(VGroup):
    def __init__(self, size, color=BLUE, **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.rect = Rectangle(height=size * 0.3, width=0.8, fill_color=color, fill_opacity=0.9, color=WHITE, stroke_width=2)
        self.label = Text(str(size), font_size=20).move_to(self.rect.get_center())
        self.add(self.rect, self.label)

class PackingBin(VGroup):
    def __init__(self, capacity=10, label="", color=WHITE, **kwargs):
        super().__init__(**kwargs)
        self.capacity = capacity
        self.items = []
        self.total_height = capacity * 0.3
        self.container = Rectangle(height=self.total_height + 0.2, width=1.2, color=color, stroke_width=4)
        self.label = Text(label, font_size=24, color=color).next_to(self.container, UP)
        self.bg = Rectangle(height=self.total_height, width=1.2, color=color, fill_opacity=0.1, stroke_width=0)
        self.add(self.bg, self.container, self.label)

    def add_item_visual(self, item):
        current_h = sum([i.size for i in self.items]) * 0.3
        target_y = self.container.get_bottom()[1] + 0.1 + current_h + (item.rect.height / 2)
        target_pos = np.array([self.container.get_center()[0], target_y, 0])
        self.items.append(item)
        return target_pos

class SelectionAndMutation(Scene):
    def construct(self):
        self.part_1_tournament()
        self.wait(1)
        self.clear()
        self.part_2_mutation()

    def part_1_tournament(self):
        # Title
        title = Text("Phase 1: Tournament Selection", font_size=40).to_edge(UP)
        self.play(Write(title))

        # Create a "Population" of solutions
        fitness_scores = [0.65, 0.82, 0.45, 0.91, 0.55, 0.78]
        population = VGroup()
        for i, fit in enumerate(fitness_scores):
            chrom = ChromosomeVisual(fit, i+1)
            population.add(chrom)
        
        population.arrange(RIGHT, buff=0.5).shift(DOWN * 0.5)
        
        pop_label = Text("Population (Fitness Scores)", font_size=24, color=GREY).next_to(population, UP, buff=0.5)
        self.play(FadeIn(population), Write(pop_label))
        self.wait(0.5)

        # --- The Tournament Logic ---
        # 1. Randomly select 2 individuals
        # Let's pick Index 0 (0.65) and Index 3 (0.91)
        idx1, idx2 = 0, 3
        c1 = population[idx1]
        c2 = population[idx2]

        # Visual selection boxes
        box1 = SurroundingRectangle(c1, color=YELLOW, buff=0.1)
        box2 = SurroundingRectangle(c2, color=YELLOW, buff=0.1)
        
        t_text = Text("Select 2 Randomly", color=YELLOW, font_size=24).to_edge(RIGHT).shift(UP)
        self.play(Create(box1), Create(box2), Write(t_text))
        self.wait(0.5)

        # 2. Compare Fitness
        # 0.91 > 0.65
        winner = c2
        loser = c1
        
        comp_text = Text(f"{winner.fitness} > {loser.fitness}", color=GREEN, font_size=32).next_to(t_text, DOWN)
        self.play(Write(comp_text))
        self.play(
            Indicate(winner, color=GREEN, scale_factor=1.2),
            box2.animate.set_color(GREEN),
            box1.animate.set_color(RED)
        )
        self.wait(0.5)

        # 3. Winner becomes Parent
        parent_label = Text("Selected Parent", color=GREEN, font_size=28).move_to(UP * 2)
        
        # Copy winner to parent slot
        parent_copy = winner.copy()
        self.play(
            parent_copy.animate.next_to(parent_label, DOWN),
            FadeIn(parent_label),
            FadeOut(box1), FadeOut(box2), FadeOut(t_text), FadeOut(comp_text)
        )
        self.wait(1)
        
        # Clean up for next scene
        self.play(FadeOut(Group(population, pop_label, title, parent_label, parent_copy)))

    def part_2_mutation(self):
        # Title
        title = Text("Phase 3: Mutation Operator", font_size=40).to_edge(UP)
        subtitle = Text("Logic: Eliminate a Bin -> Force Re-insertion", font_size=24, color=RED).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle))

        # Create a Child Solution
        bin1 = PackingBin(10, "Bin A", color=BLUE)
        bin2 = PackingBin(10, "Bin B", color=BLUE)
        bin3 = PackingBin(10, "Bin C", color=BLUE)
        
        # Bin B is the target for mutation (it's not full, maybe efficient to break it)
        # Bin A: [5, 5] (Full)
        # Bin B: [4, 2] (Half empty)
        # Bin C: [8] (Mostly full)
        
        items_a = [PackingItem(5), PackingItem(5)]
        items_b = [PackingItem(4, color=RED), PackingItem(2, color=RED)] # Red for visual focus
        items_c = [PackingItem(8)]

        for i in items_a: bin1.add(i); i.move_to(bin1.add_item_visual(i))
        for i in items_b: bin2.add(i); i.move_to(bin2.add_item_visual(i))
        for i in items_c: bin3.add(i); i.move_to(bin3.add_item_visual(i))

        solution = VGroup(bin1, bin2, bin3).arrange(RIGHT, buff=1).shift(DOWN * 1)
        self.play(Create(solution))
        self.wait(1)

        # --- Mutation Action ---
        # 1. Select a bin to eliminate
        mut_text = Text("Mutation: Destroy Bin B", color=RED, font_size=28).to_edge(RIGHT).shift(UP)
        self.play(Write(mut_text))
        
        arrow = Arrow(UP, DOWN, color=RED).next_to(bin2, UP)
        self.play(GrowArrow(arrow))
        
        # 2. Destroy Bin
        loose_items = VGroup(*items_b) # Group the items inside
        self.play(
            FadeOut(bin2.container), FadeOut(bin2.bg), FadeOut(bin2.label), FadeOut(arrow),
            loose_items.animate.arrange(RIGHT, buff=0.5).move_to(UP * 0.5) # Items float up
        )
        
        reinsert_text = Text("Items are now loose", color=YELLOW, font_size=24).next_to(loose_items, UP)
        self.play(Write(reinsert_text))
        self.wait(1)

        # 3. Re-insert (FFD Heuristic)
        # Item (4): Try Bin A (Full? No fit). Try Bin C (Space 2? No fit). -> New Bin.
        # Item (2): Try Bin A (Full). Try Bin C (Space 2? Fits!).
        
        # Re-insert Item 2 into Bin C
        item_2 = items_b[1] # Size 2
        target_pos = bin3.add_item_visual(item_2) # Calculate new pos in Bin C
        
        self.play(
            item_2.animate.move_to(target_pos)
        )
        bin3.add(item_2)
        self.wait(0.5)

        # Re-insert Item 4 (Cannot fit anywhere) -> New Bin
        item_4 = items_b[0] # Size 4
        new_bin = PackingBin(10, "Bin D", color=GREEN)
        new_bin.move_to(bin2.get_center()) # Take the old spot
        
        self.play(Create(new_bin))
        target_pos = new_bin.add_item_visual(item_4)
        self.play(item_4.animate.move_to(target_pos))
        
        final_text = Text("Result: Different Grouping Structure", color=GREEN, font_size=32).next_to(solution, DOWN)
        self.play(Write(final_text))
        self.wait(2)