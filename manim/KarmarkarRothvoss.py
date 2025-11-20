from manim import *
import numpy as np

class BinPackingGrandTour(Scene):
    def construct(self):
        # Professional dark background
        self.camera.background_color = "#000000"
        
        # --- PHASE 1: COMMON FOUNDATION ---
        self.intro_scene()
        self.transition_card("Part I: The Foundation", "The Gilmore-Gomory LP", YELLOW)
        self.lp_scene()
        
        # --- PHASE 2: THE DIVERGENCE ---
        # We create a visual menu/timeline to show the two paths
        self.branching_scene(selection="start")
        
        # --- PATH A: KARMARKAR-KARP ---
        self.branching_scene(selection="kk")
        self.transition_card("Path A: Karmarkar-Karp (1982)", "Linear Grouping Scheme", TEAL)
        self.kk_grouping_scene()
        self.transition_card("The Recursion", "Reducing Item Types", PURPLE)
        self.kk_recursion_scene()
        self.kk_mini_conclusion()
        
        # --- RESET FOR PATH B ---
        self.clear()
        
        # --- PATH B: ROTHVOSS ---
        self.branching_scene(selection="rothvoss")
        self.transition_card("Path B: Rothvoß (2013)", "Discrepancy & Gluing", GREEN)
        self.rothvoss_2013_scene()
        self.transition_card("Refinement: Hoberg & Rothvoß (2015)", "2-Stage Packing", ORANGE)
        self.hoberg_2015_scene()
        
        # --- PHASE 3: GRAND SUMMARY ---
        self.grand_summary_scene()

    # ==========================================
    #       HELPER & TRANSITION METHODS
    # ==========================================

    def transition_card(self, main_text, sub_text, color):
        self.clear()
        t1 = Text(main_text, font_size=48, color=color)
        t2 = Text(sub_text, font_size=32, color=WHITE).next_to(t1, DOWN)
        self.play(Write(t1), FadeIn(t2))
        self.wait(2)
        self.play(FadeOut(t1), FadeOut(t2))

    def branching_scene(self, selection="start"):
        # Visualizing the timeline split
        title = Text("The Algorithmic Landscape", font_size=40).to_edge(UP)
        
        # Root Node (Gilmore-Gomory)
        node_root = Circle(radius=0.6, color=YELLOW, fill_opacity=0.5).shift(UP * 1.5)
        label_root = Text("Gilmore-Gomory LP", font_size=24, color=YELLOW).next_to(node_root, UP)
        
        # Left Node (KK)
        node_kk = Circle(radius=0.5, color=TEAL, fill_opacity=0.5).shift(LEFT * 3 + DOWN * 1.5)
        label_kk = Text("1982: Karmarkar-Karp", font_size=24, color=TEAL).next_to(node_kk, DOWN)
        
        # Right Node (Rothvoss)
        node_rv = Circle(radius=0.5, color=GREEN, fill_opacity=0.5).shift(RIGHT * 3 + DOWN * 1.5)
        label_rv = Text("2013: Rothvoß", font_size=24, color=GREEN).next_to(node_rv, DOWN)
        
        # Connecting Lines
        line_left = Line(node_root.get_bottom(), node_kk.get_top(), color=GREY)
        line_right = Line(node_root.get_bottom(), node_rv.get_top(), color=GREY)
        
        # Group all potentially interactive elements
        group = VGroup(title, node_root, label_root, node_kk, label_kk, node_rv, label_rv, line_left, line_right)
        
        if selection == "start":
            self.play(FadeIn(title))
            self.play(GrowFromCenter(node_root), Write(label_root))
            self.play(Create(line_left), GrowFromCenter(node_kk), Write(label_kk))
            self.play(Create(line_right), GrowFromCenter(node_rv), Write(label_rv))
            self.wait(1)
            
            # Save references for the next step (KK) to allow seamless transition
            self.landscape_group = group
            self.landscape_components = {
                "node_root": node_root, "label_root": label_root,
                "node_kk": node_kk, "label_kk": label_kk,
                "node_rv": node_rv, "label_rv": label_rv,
                "line_left": line_left, "line_right": line_right
            }
            # Note: We do NOT FadeOut here. The objects stay on screen.
            
        elif selection == "kk":
            # Check if we have the existing objects from the 'start' selection.
            # We use hasattr because the VGroup wrapper 'landscape_group' might NOT be in 
            # self.mobjects (only its children were added via animations), so the 'in' check would fail.
            if hasattr(self, "landscape_group"):
                # Use the existing objects to ensure smooth transition
                group = self.landscape_group
                c = self.landscape_components
                node_root, label_root = c["node_root"], c["label_root"]
                node_kk, label_kk = c["node_kk"], c["label_kk"]
                node_rv, label_rv = c["node_rv"], c["label_rv"]
                line_left, line_right = c["line_left"], c["line_right"]
            else:
                # Fallback: add fresh objects if not found (e.g. if running isolated)
                self.add(group)
            
            # Buffer time to ensure smooth visual continuity
            self.wait(0.5)
            
            # Highlight KK
            self.play(
                node_root.animate.set_stroke(opacity=0.2).set_fill(opacity=0.2),
                label_root.animate.set_opacity(0.2),
                line_right.animate.set_opacity(0.2),
                node_rv.animate.set_stroke(opacity=0.2).set_fill(opacity=0.2),
                label_rv.animate.set_opacity(0.2),
                
                node_kk.animate.scale(1.2).set_fill(opacity=1),
                line_left.animate.set_color(TEAL).set_stroke(width=5),
            )
            self.wait(1)
            self.play(FadeOut(group))
            # Cleanup to prevent misuse later
            if hasattr(self, "landscape_group"):
                del self.landscape_group
            
        elif selection == "rothvoss":
            # Always add fresh group for Rothvoss as previous state was cleared
            self.add(group)
            
            # Highlight Rothvoss
            self.play(
                node_root.animate.set_stroke(opacity=0.2).set_fill(opacity=0.2),
                label_root.animate.set_opacity(0.2),
                line_left.animate.set_opacity(0.2),
                node_kk.animate.set_stroke(opacity=0.2).set_fill(opacity=0.2),
                label_kk.animate.set_opacity(0.2),
                
                node_rv.animate.scale(1.2).set_fill(opacity=1),
                line_right.animate.set_color(GREEN).set_stroke(width=5),
            )
            self.wait(1)
            self.play(FadeOut(group))

    # ==========================================
    #           COMMON SCENES
    # ==========================================

    def intro_scene(self):
        # --- Title Sequence ---
        title = Text("Advanced Bin Packing Algorithms", font_size=40, weight=BOLD)
        subtitle = Text("Breaking the Karmarkar-Karp Barrier", font_size=30, color=BLUE)
        subtitle.next_to(title, DOWN)
        
        self.play(Write(title), FadeIn(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

        # --- The Problem: Visualized ---
        problem_title = Text("1D Bin Packing Problem", font_size=36).to_edge(UP)
        self.play(Write(problem_title))

        # Create items of different sizes
        items = VGroup(
            Rectangle(height=1.5, width=1, color=RED, fill_opacity=0.7, stroke_width=1),
            Rectangle(height=0.8, width=1, color=GREEN, fill_opacity=0.7, stroke_width=1),
            Rectangle(height=2.2, width=1, color=BLUE, fill_opacity=0.7, stroke_width=1),
            Rectangle(height=1.0, width=1, color=YELLOW, fill_opacity=0.7, stroke_width=1),
            Rectangle(height=0.5, width=1, color=ORANGE, fill_opacity=0.7, stroke_width=1)
        ).arrange(RIGHT, buff=0.2)
        
        items_label = Text("Items", font_size=24).next_to(items, DOWN)

        # Create Bins (Height 4 represents capacity 1)
        bin_height = 4
        bins = VGroup(*[
            Rectangle(height=bin_height, width=1.2, color=WHITE, stroke_width=2) 
            for _ in range(3)
        ]).arrange(RIGHT, buff=1)
        bins_label = Text("Unit Capacity Bins", font_size=24).next_to(bins, DOWN)

        # Positioning
        main_group = VGroup(items, bins).arrange(RIGHT, buff=2)
        # Re-align labels after grouping
        items_label.next_to(items, DOWN)
        bins_label.next_to(bins, DOWN)

        self.play(FadeIn(items), Write(items_label))
        self.play(FadeIn(bins), Write(bins_label))
        self.wait(1)

        self.play(FadeOut(items_label))

        self.wait(1)
        # --- Naive Packing Animation ---
        self.play(
            items[0].animate.move_to(bins[0].get_bottom() + UP * (items[0].height/2)),
            items[1].animate.move_to(bins[0].get_bottom() + UP * (items[0].height + items[1].height/2 + 0.05)),
            run_time=1.5
        )
        self.play(
            items[2].animate.move_to(bins[1].get_bottom() + UP * (items[2].height/2)),
            items[3].animate.move_to(bins[1].get_bottom() + UP * (items[2].height + items[3].height/2 + 0.05)),
            items[4].animate.move_to(bins[2].get_bottom() + UP * (items[4].height/2)),
            run_time=1.5
        )

        goal = Text("Goal: Minimize number of bins", font_size=30, color=YELLOW).next_to(bins, UP, buff=0.5)
        self.play(Write(goal))
        self.wait(2)

        self.play(FadeOut(problem_title), FadeOut(items), FadeOut(bins), FadeOut(bins_label), FadeOut(goal))
        
    def lp_scene(self):
        # --- Concept of a Pattern ---
        pattern_text = Text("The Core Concept: 'Patterns'", font_size=32).to_edge(UP)
        self.play(Write(pattern_text))

        bin_rect = Rectangle(height=4, width=1.5, color=WHITE)
        # Pattern: 2 Reds, 1 Blue
        item1 = Rectangle(height=1, width=1.3, color=RED, fill_opacity=0.8, stroke_width=1)
        item2 = Rectangle(height=1, width=1.3, color=RED, fill_opacity=0.8, stroke_width=1)
        item3 = Rectangle(height=1.5, width=1.3, color=BLUE, fill_opacity=0.8, stroke_width=1)
        
        pattern_group = VGroup(item1, item2, item3).arrange(UP, buff=0.05)
        pattern_group.move_to(bin_rect.get_center())
        
        pattern_visual = VGroup(bin_rect, pattern_group).shift(LEFT*2)
        
        pattern_vec = MathTex(
            r"p = \begin{pmatrix} 2 \\ 1 \\ 0 \end{pmatrix} \begin{matrix} \leftarrow \text{Item A} \\ \leftarrow \text{Item B} \\ \leftarrow \text{Item C} \end{matrix}", 
            font_size=34
        ).next_to(pattern_visual, RIGHT, buff=1)

        self.play(Create(bin_rect), FadeIn(pattern_group))
        self.play(Write(pattern_vec))
        self.wait(2)

        # --- LP Matrix Visualization ---
        self.play(FadeOut(pattern_visual), FadeOut(pattern_vec), FadeOut(pattern_text))
        
        lp_header = Text("The Pattern Matrix A", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(lp_header))

        # Rows = Items, Cols = Patterns
        matrix_vals = [
            [1, 0, 2, 1],
            [0, 1, 0, 2],
            [1, 1, 0, 0],
            [0, 1, 1, 1]
        ]
        
        matrix = IntegerMatrix(matrix_vals, v_buff=0.6, h_buff=0.8).scale(0.8).shift(LEFT * 1.5)
        col_labels = VGroup(*[MathTex(f"P_{i+1}", font_size=24).next_to(matrix.get_columns()[i], UP) for i in range(4)])
        
        x_vec = Matrix([[0.5], [0.2], [0.8], [0.1]]).scale(0.8).next_to(matrix, RIGHT)
        x_label = MathTex("x", color=YELLOW).next_to(x_vec, UP)
        
        eq = MathTex(r"\ge b").scale(0.8).next_to(x_vec, RIGHT)

        self.play(Create(matrix), Write(col_labels))
        self.play(Create(x_vec), Write(x_label), Write(eq))
        
        # Highlight that x is fractional
        fractional_text = Text("Fractional Solution", font_size=24, color=YELLOW).next_to(x_vec, DOWN)
        self.play(Write(fractional_text))
        self.wait(2)
        
        self.play(FadeOut(lp_header), FadeOut(matrix), FadeOut(col_labels), FadeOut(x_vec), FadeOut(x_label), FadeOut(eq), FadeOut(fractional_text))

    # ==========================================
    #       KARMARKAR-KARP SCENES
    # ==========================================

    def kk_grouping_scene(self):
        title = Text("Strategy: Linear Grouping", font_size=36).to_edge(UP)
        self.play(Write(title))

        # 1. Create Sorted Items
        n_items = 12
        heights = np.linspace(1.5, 0.3, n_items)
        
        items = VGroup()
        for h in heights:
            items.add(Rectangle(height=h, width=0.4, color=BLUE_C, fill_opacity=0.8, stroke_width=1))
        
        items.arrange(RIGHT, buff=0.1, aligned_edge=DOWN).shift(DOWN * 1)
        
        label_sort = Text("1. Sort Items by Size", font_size=24, color=YELLOW).next_to(items, UP, buff=0.5)
        
        self.play(FadeIn(items, lag_ratio=0.1))
        self.play(Write(label_sort))
        self.wait(1)

        # 2. Grouping
        k = 4
        groups = VGroup()
        braces = VGroup()
        group_labels = VGroup()
        colors = [RED, GREEN, BLUE]
        
        for i in range(3):
            start = i * k
            end = (i + 1) * k
            subgroup = items[start:end]
            
            brace = Brace(subgroup, DOWN)
            t = Text(f"Group {i+1}", font_size=20).next_to(brace, DOWN)
            
            braces.add(brace)
            group_labels.add(t)
            
            # Animate color, brace, and label for this specific group
            self.play(
                subgroup.animate.set_color(colors[i]),
                Create(brace),
                Write(t),
                run_time=1.0
            )

        self.play(FadeOut(label_sort))
        
        # 3. The Logic Visual
        logic_text = Text("Key Property: Items decrease in size", font_size=28).to_edge(UP).shift(DOWN*1.0)
        self.play(Write(logic_text))
        
        # Highlight Group 1 (Large items)
        rect_discard = SurroundingRectangle(items[0:4], color=RED, buff=0.1)
        discard_text = Text("Discard Largest Group", font_size=24, color=RED).next_to(rect_discard, UP).shift(UP*0.5)
        
        self.play(Create(rect_discard), Write(discard_text))
        self.wait(1)
        
        # Explain shifting
        shift_text = Text("Group 2 fits in Group 1's spot", font_size=24, color=GREEN).next_to(discard_text, DOWN)
        
        self.play(Write(shift_text))
        self.wait(2)
        
        math_prop = MathTex(r"\text{Size}(G_{i+1}) \le \text{Size}(G_i)", font_size=36).next_to(items, DOWN, buff=1.5)
        self.play(Write(math_prop))
        self.wait(2)
        
        self.play(FadeOut(VGroup(items, braces, group_labels, rect_discard, discard_text, shift_text, logic_text, math_prop, title)))

    def kk_recursion_scene(self):
        title = Text("Reducing Complexity", font_size=36).to_edge(UP)
        self.play(Write(title))

        # Visualizing the Reduction
        start_text = Text("Original: Many Sizes", font_size=24).shift(LEFT*4 + UP*2)
        end_text = Text("Rounded: Few Sizes", font_size=24).shift(RIGHT*4 + UP*2)
        
        arrow = Arrow(start_text.get_right(), end_text.get_left(), buff=0.5).shift(DOWN*1.3)
        op_text = Text("Linear Grouping", font_size=20).next_to(arrow, UP)

        bars_left = VGroup(*[Rectangle(height=h, width=0.2, color=WHITE) for h in np.random.uniform(0.5, 2, 15)])
        bars_left.arrange(RIGHT, buff=0.05).next_to(start_text, DOWN)
        
        bars_right = VGroup(
            Rectangle(height=2, width=1, color=RED),
            Rectangle(height=1.5, width=1, color=GREEN),
            Rectangle(height=1, width=1, color=BLUE)
        ).arrange(RIGHT, buff=0.1).next_to(end_text, DOWN)

        self.play(Write(start_text), FadeIn(bars_left))
        self.wait(0.5)
        self.play(GrowArrow(arrow), Write(op_text))
        self.play(Write(end_text), TransformFromCopy(bars_left, bars_right))
        self.wait(1)
        
        error_text = Text("Cost of Rounding:", font_size=28, color=RED).shift(DOWN*1.0)
        error_math = MathTex(r"\text{Error per iteration} \approx \text{Number of Groups} (k)", font_size=32).next_to(error_text, DOWN)
        
        self.play(Write(error_text), Write(error_math))
        self.wait(2)

        self.play(
            FadeOut(start_text), FadeOut(bars_left), FadeOut(arrow), FadeOut(op_text),
            FadeOut(end_text), FadeOut(bars_right), FadeOut(error_text), FadeOut(error_math)
        )

        tree_root = Dot(point=UP*2)
        l1 = VGroup(Dot(point=UP+LEFT), Dot(point=UP+RIGHT))
        l2 = VGroup(Dot(point=LEFT*1.5), Dot(point=LEFT*0.5), Dot(point=RIGHT*0.5), Dot(point=RIGHT*1.5))
        
        lines = VGroup(
            Line(tree_root, l1[0]), Line(tree_root, l1[1]),
            Line(l1[0], l2[0]), Line(l1[0], l2[1]),
            Line(l1[1], l2[2]), Line(l1[1], l2[3])
        )
        
        recursion_label = Text("Recursive Elimination", font_size=32, color=BLUE).next_to(tree_root, UP)
        
        self.play(Write(recursion_label), Create(tree_root))
        self.play(Create(l1), Create(lines[0:2]))
        self.play(Create(l2), Create(lines[2:]))
        
        depth_text = MathTex(r"\text{Recursion Depth } \approx \log(\text{Input Size})", font_size=36).next_to(lines, DOWN, buff=1)
        self.play(Write(depth_text))
        self.wait(2)
        
        self.play(FadeOut(VGroup(tree_root, l1, l2, lines, recursion_label, depth_text, title)))

    def kk_mini_conclusion(self):
        bound = MathTex(r"OPT \le OPT_f + O(\log^2 OPT)", font_size=50, color=TEAL)
        text = Text("The 1982 Benchmark", font_size=32).next_to(bound, UP)
        self.play(Write(text), Write(bound))
        self.wait(2)
        self.play(FadeOut(text), FadeOut(bound))

    # ==========================================
    #           ROTHVOSS SCENES
    # ==========================================

    def rothvoss_2013_scene(self):
        title = Text("Rothvoß (2013): Handling Spikes", font_size=36).to_edge(UP)
        self.play(Write(title))

        # --- The "Spiky" Pattern Problem ---
        problem_header = Text("The Problem with KK82: Spiky Patterns", font_size=30, color=RED).shift(UP*2.5)
        self.play(Write(problem_header))

        # Draw a bin with many small items
        spiky_bin = Rectangle(height=4, width=1.5, color=WHITE).shift(LEFT * 3, DOWN * 0.5)
        
        # Create 20 small items (slivers)
        small_items = VGroup(*[
            Rectangle(height=0.15, width=1.3, color=RED, fill_opacity=0.9, stroke_width=0.5)
            for _ in range(20)
        ]).arrange(UP, buff=0.02).move_to(spiky_bin.get_center())

        spiky_label = Text("Pattern p", font_size=24).next_to(spiky_bin, UP)

        self.play(Create(spiky_bin), FadeIn(small_items), Write(spiky_label))

        # Math Explanation
        math_text = VGroup(
            MathTex(r"\text{Item } i \text{ count: } p_i = 20"),
            MathTex(r"||A_i||_2 \approx \text{Large}"),
            Text("High Error!", color=RED, font_size=36)
        ).arrange(DOWN, aligned_edge=LEFT).next_to(spiky_bin, RIGHT, buff=1.5)

        for line in math_text:
            self.play(Write(line))
            self.wait(0.5)

        self.wait(1)

        # --- The Fix: Gluing ---
        fix_arrow = Arrow(start=math_text.get_bottom() + DOWN*0.2, end=math_text.get_bottom() + DOWN*1.5, color=WHITE)
        fix_text = Text("Solution: Gluing", font_size=32, color=GREEN).next_to(fix_arrow, DOWN)
        
        self.play(FadeIn(fix_arrow), Write(fix_text))
        self.play(FadeOut(math_text), FadeOut(problem_header), FadeOut(fix_arrow), FadeOut(fix_text))
        
        gluing_title = Text("Gluing: Grouping Small Items", font_size=30, color=GREEN).shift(UP*2.5)
        self.play(Write(gluing_title))

        # Animate the transformation
        # Group 20 small items into 4 large items
        glued_items = VGroup(*[
            Rectangle(height=0.85, width=1.3, color=YELLOW, fill_opacity=0.9, stroke_width=1)
            for _ in range(4)
        ]).arrange(UP, buff=0.02).move_to(spiky_bin.get_center())

        glued_label = Text("Glued Items", font_size=24, color=YELLOW).next_to(spiky_bin, DOWN)

        self.play(
            ReplacementTransform(small_items, glued_items),
            Write(glued_label)
        )

        result_text = MathTex(r"\text{Result: } OPT + O(\log OPT \cdot \log \log OPT)").scale(0.8).next_to(spiky_bin, RIGHT, buff=1)
        self.play(Write(result_text))
        self.wait(3)

        self.play(FadeOut(Group(title, spiky_bin, glued_items, spiky_label, glued_label, result_text, gluing_title)))

    def hoberg_2015_scene(self):
        title = Text("Hoberg & Rothvoß (2015): 2-Stage Packing", font_size=36).to_edge(UP)
        self.play(Write(title))

        # --- 3-Layer Graph Construction ---
        # 1. Items Layer
        items_dots = VGroup(*[Dot(color=RED) for _ in range(6)]).arrange(DOWN, buff=0.4)
        items_box = SurroundingRectangle(items_dots, color=RED, buff=0.2)
        items_label = Text("Items", font_size=24).next_to(items_box, UP)
        layer1 = VGroup(items_dots, items_box, items_label).shift(LEFT * 4)

        # 2. Containers Layer
        cont_dots = VGroup(*[Dot(color=YELLOW, radius=0.15) for _ in range(3)]).arrange(DOWN, buff=1.2)
        cont_label = Text("Containers", font_size=24).next_to(cont_dots, UP).shift(UP*0.5)
        layer2 = VGroup(cont_dots, cont_label)

        # 3. Bins Layer
        bins_dots = VGroup(*[Dot(color=WHITE, radius=0.2) for _ in range(2)]).arrange(DOWN, buff=2.0)
        bins_label = Text("Bins", font_size=24).next_to(bins_dots, UP).shift(UP*0.5)
        layer3 = VGroup(bins_dots, bins_label).shift(RIGHT * 4)

        # --- Animation Sequence ---
        self.play(LaggedStart(*[GrowFromCenter(dot) for dot in items_dots], lag_ratio=0.15), run_time=1)
        self.play(Create(items_box), FadeIn(items_label, shift=UP * 0.2))

        self.play(LaggedStart(*[GrowFromCenter(dot) for dot in cont_dots], lag_ratio=0.15), FadeIn(cont_label, shift=UP * 0.2))
        self.play(LaggedStart(*[GrowFromCenter(dot) for dot in bins_dots], lag_ratio=0.15), FadeIn(bins_label, shift=UP * 0.2))

        # Arrows Stage 1: Items -> Containers
        arrows1 = VGroup()
        for i, dot in enumerate(items_dots):
            target = cont_dots[i % 3]
            arrows1.add(Line(dot.get_center(), target.get_center(), color=RED_A, stroke_opacity=0.5, buff=0.1))
        
        self.play(LaggedStart(*[Create(arrow) for arrow in arrows1], lag_ratio=0.15), run_time=1.5)
        stage1_txt = Text("Stage 1: Items → Containers", font_size=20, color=RED).next_to(layer1, DOWN)
        self.play(Write(stage1_txt))

        # Arrows Stage 2: Containers -> Bins
        arrows2 = VGroup()
        for i, dot in enumerate(cont_dots):
            target = bins_dots[i % 2]
            arrows2.add(Line(dot.get_center(), target.get_center(), color=YELLOW_A, buff=0.1))
            
        self.play(LaggedStart(*[Create(arrow) for arrow in arrows2], lag_ratio=0.15), run_time=1.5)
        stage2_txt = Text("Stage 2: Containers → Bins", font_size=20, color=YELLOW).next_to(layer3, DOWN)
        self.play(Write(stage2_txt))

        self.wait(1)
        self.play(FadeOut(layer1), FadeOut(layer2), FadeOut(layer3), FadeOut(arrows1), FadeOut(arrows2), FadeOut(stage1_txt), FadeOut(stage2_txt))
        
        # --- Key Insight ---
        insight_header = Text("Key Insight", font_size=48, color=BLUE, weight=BOLD).shift(UP*2.5)
        insight_points = VGroup(
            Text("• Containers are large objects", font_size=30),
            Text("• A bin fits very few containers", font_size=30),
            Text("• Therefore: No 'Spiky' patterns!", font_size=30, color=GREEN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).next_to(insight_header, DOWN, buff=0.8)

        self.play(Write(insight_header))
        self.play(FadeIn(insight_points, shift=UP), run_time=1.5)
        self.wait(2)

        self.play(FadeOut(insight_header), FadeOut(insight_points))

        # --- Final Result for this path ---
        final_bound = MathTex(r"\text{Bound: } OPT + O(\log OPT)", font_size=60, color=GOLD)
        self.play(Write(final_bound))
        self.play(Indicate(final_bound, scale_factor=1.2, color=YELLOW))
        self.wait(2)
        self.play(FadeOut(final_bound), FadeOut(title))

    # ==========================================
    #           GRAND CONCLUSION
    # ==========================================

    def grand_summary_scene(self):
        title = Text("Summary of Progress", font_size=40).to_edge(UP)
        self.play(Write(title))

        # 1. KK82
        line1_name = Text("1982: Karmarkar-Karp", font_size=32, color=TEAL)
        line1_bound = MathTex(r"OPT \le OPT_f + O(\log^2 OPT)", font_size=36)
        group1 = VGroup(line1_name, line1_bound).arrange(DOWN, buff=0.15)

        # 2. Rothvoss 2013
        line2_name = Text("2013: Rothvoß", font_size=32, color=GREEN)
        line2_bound = MathTex(r"OPT \le OPT_f + O(\log OPT \cdot \log \log OPT)", font_size=36)
        group2 = VGroup(line2_name, line2_bound).arrange(DOWN, buff=0.15)

        # 3. Hoberg & Rothvoss 2015
        line3_name = Text("2015: Hoberg & Rothvoß", font_size=32, color=GOLD)
        line3_bound = MathTex(r"OPT \le OPT_f + O(\log OPT)", font_size=36)
        group3 = VGroup(line3_name, line3_bound).arrange(DOWN, buff=0.15)

        # Layout
        summary = VGroup(group1, group2, group3).arrange(DOWN, buff=0.8)
        
        # Animation
        self.play(FadeIn(group1, shift=UP))
        self.wait(1)
        self.play(FadeIn(group2, shift=UP))
        self.wait(1)
        self.play(FadeIn(group3, shift=UP))
        self.wait(3)
        
        # Outro
        self.play(FadeOut(title), FadeOut(summary))
        
        end_text = Text("Thanks for watching!", font_size=48)
        self.play(Write(end_text))
        self.wait(2)
