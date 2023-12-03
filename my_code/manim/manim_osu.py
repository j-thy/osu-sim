from manim import *
import numpy as np

def title_slide(self):
    # Write out the title.
    title1 = Text('Using K-Means Clustering', color=WHITE, t2c={'K-Means Clustering':ORANGE}).shift(UP*1.5)
    title2 = Text('to recommend similar beatmaps', color=WHITE).next_to(title1, DOWN)
    title3 = Text('in a rhythm game called osu!', color=WHITE, t2c={'osu!':PINK}).next_to(title2, DOWN)
    name = Text('By Jonathan Ting', color=WHITE, t2c={'osu!':PINK}, font_size = 30).next_to(title3, DOWN)
    self.play(Write(title1, run_time=1.2))
    self.play(Write(title2, run_time=1.2))
    self.play(Write(title3, run_time=1.2))
    self.play(Write(name, run_time=1.2))

    # Transition to next scene.
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)

def osu_game_slide(self):

    # Animate 4 music notes.
    note = SVGMobject("8thNote.svg", fill_color=WHITE, fill_opacity=1, stroke_color=WHITE)
    note_group = VGroup(*[note.copy() for i in range(4)])
    note_group.arrange(RIGHT, buff=2)
    note_group.shift(DOWN*2)
    note_group.scale(0.5)

    self.play(DrawBorderThenFill(note_group))
    self.play(Succession(*[Indicate(note) for note in note_group]))

    # Transition to next scene.
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)

def features_slide(self):
    rotation_center = LEFT

    # Create the 45 degree angle.
    line1 = Line(LEFT, RIGHT)
    line2 = Line(LEFT, RIGHT)
    line2.rotate(
        45 * DEGREES, about_point=rotation_center
    )
    d1 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line1.get_end())
    d2 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line2.get_end())
    d3 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line2.get_start())
    n1 = DecimalNumber(3, num_decimal_places=0).move_to(d1.get_center())
    n2 = DecimalNumber(1, num_decimal_places=0).move_to(d2.get_center())
    n3 = DecimalNumber(2, num_decimal_places=0).move_to(d3.get_center())
    a1 = Angle(line1, line2, radius=0.8, other_angle=False)
    a_num1 = DecimalNumber(45, num_decimal_places=0, unit="^\\circ").move_to(
        Angle(
            line1, line2, radius=1 + 3 * SMALL_BUFF, other_angle=False
        ).point_from_proportion(0.5)
    )
    group1 = VGroup(line1, line2, a1, a_num1, d1, d2, d3, n1, n2, n3)

    # Create the 135 degree angle.
    line4 = Line(LEFT, RIGHT)
    line4.rotate(
        135 * DEGREES, about_point=rotation_center
    )
    d4 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line1.get_end())
    d5 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line4.get_end())
    d6 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line4.get_start())
    n4 = DecimalNumber(3, num_decimal_places=0).move_to(d4.get_center())
    n5 = DecimalNumber(1, num_decimal_places=0).move_to(d5.get_center())
    n6 = DecimalNumber(2, num_decimal_places=0).move_to(d6.get_center())
    a2 = Angle(line1, line4, radius=0.8, other_angle=False)
    a_num2 = DecimalNumber(135, num_decimal_places=0, unit="^\\circ").move_to(
        Angle(
            line1, line4, radius=1 + 3 * SMALL_BUFF, other_angle=False
        ).point_from_proportion(0.5)
    )
    group2 = VGroup(line1, line4, a2, a_num2, d4, d5, d6, n4, n5, n6)
    a_tex = Text("Angle", color=WHITE, font_size=50).next_to(group2, DOWN)

    line5 = Line(LEFT*0.6, ORIGIN)
    line6 = Line(ORIGIN, RIGHT*0.6)
    d7 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line5.get_start())
    d8 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line5.get_end())
    d9 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line6.get_end())
    n7 = DecimalNumber(1, num_decimal_places=0).move_to(d7.get_center())
    n8 = DecimalNumber(2, num_decimal_places=0).move_to(d8.get_center())
    n9 = DecimalNumber(3, num_decimal_places=0).move_to(d9.get_center())
    group3 = VGroup(line5, line6, d9, d8, d7, n9, n8, n7)

    line7 = Line(LEFT, ORIGIN)
    line8 = Line(ORIGIN, RIGHT)
    d10 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line7.get_start())
    d11 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line8.get_end())
    n10 = DecimalNumber(1, num_decimal_places=0).move_to(d10.get_center())
    n11 = DecimalNumber(3, num_decimal_places=0).move_to(d11.get_center())
    group4 = VGroup(line7, line8, d11, d8, d10, n11, n8, n10)
    d_tex = Text("Distance", color=WHITE, font_size=50).next_to(group4, DOWN)

    line9 = Line(LEFT+DOWN, RIGHT+DOWN)
    d12 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line9.get_start())
    d13 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line9.get_end())
    n12 = DecimalNumber(1, num_decimal_places=0).move_to(d12.get_center())
    n13 = DecimalNumber(2, num_decimal_places=0).move_to(d13.get_center())
    group5 = VGroup(d12, n12)
    group6 = VGroup(d13, n13)
    group7 = VGroup(line9, group5, group6)
    t_tex = Text("Time", color=WHITE, font_size=50).next_to(group7, DOWN)

    line10 = Line(LEFT+DOWN, RIGHT+DOWN, stroke_width=85, stroke_color=GRAY)
    d14 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line10.get_start())
    d15 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line10.get_end())
    n14 = DecimalNumber(1, num_decimal_places=0).move_to(d14.get_center())
    group8 = VGroup(line10, d14, d15, n14)
    sd_tex1 = Text("Slider", color=WHITE, font_size=50).next_to(group8, DOWN)
    sd_tex2 = Text("Distance", color=WHITE, font_size=50).next_to(sd_tex1, DOWN)

    line11 = Line(LEFT*1.4+DOWN, RIGHT*1.4+DOWN, stroke_width=85, stroke_color=GRAY)
    d16 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line11.get_start())
    d17 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line11.get_end())
    n15 = DecimalNumber(1, num_decimal_places=0).move_to(d16.get_center())
    group9 = VGroup(line11, d16, d17, n15)

    line12 = Line(LEFT*1.4+DOWN, RIGHT*1.4+DOWN, stroke_width=85, stroke_color=GRAY)
    d18 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line12.get_start())
    d19 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line12.get_start())
    d20 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line12.get_end())
    n16 = DecimalNumber(1, num_decimal_places=0).move_to(d18.get_center())
    group10 = VGroup(d18, n16)
    group11 = VGroup(line12, d19, group10, d20)
    sv_tex1 = Text("Slider", color=WHITE, font_size=50).next_to(group11, DOWN)
    sv_tex2 = Text("Velocity", color=WHITE, font_size=50).next_to(sv_tex1, DOWN)

    line13 = Line(LEFT, ORIGIN).shift(RIGHT*3.8+DOWN*0.74)
    line14 = Line(ORIGIN, RIGHT).shift(RIGHT*3.8+DOWN*0.74)
    d21 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line13.get_start())
    d22 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line13.get_end())
    d23 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line14.get_end())
    n17 = DecimalNumber(1, num_decimal_places=0).move_to(d21.get_center())
    n18 = DecimalNumber(2, num_decimal_places=0).move_to(d22.get_center())
    n19 = DecimalNumber(3, num_decimal_places=0).move_to(d23.get_center())
    group12 = VGroup(line13, line14, d21, d22, d23, n17, n18, n19)
    line15 = Line(LEFT*1.4+DOWN, RIGHT*1.4+DOWN, stroke_width=85, stroke_color=GRAY).next_to(group12, DOWN*2.5)
    d24 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line15.get_start())
    d25 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line15.get_end())
    n20 = DecimalNumber(1, num_decimal_places=0).move_to(d24.get_center())
    group13 = VGroup(line15, d24, d25, n20)
    group14 = VGroup(group12, group13)
    sr_tex1 = Text("Slider-to-Circle", color=WHITE, font_size=50).next_to(group14, DOWN)
    sr_tex2 = Text("Ratio", color=WHITE, font_size=50).next_to(sr_tex1, DOWN)

    self.play(Create(group1), Write(a_tex))
    self.play(ReplacementTransform(group1, group2))
    self.play(group2.animate.shift(UP*1.5+LEFT*3.8), a_tex.animate.shift(UP*1.5+LEFT*3.8))
    self.play(Create(group3), Write(d_tex))
    self.play(ReplacementTransform(group3, group4))
    self.play(group4.animate.shift(UP*1.5), d_tex.animate.shift(UP*1.5))
    self.play(Create(group7), Write(t_tex))
    self.play(Succession(Indicate(group5), Indicate(group6)))
    self.play(group7.animate.shift(UP*2.5+RIGHT*3.8), t_tex.animate.shift(UP*2.5+RIGHT*3.8))
    self.play(Create(group8), Write(sd_tex1), Write(sd_tex2))
    self.play(ReplacementTransform(group8, group9))
    self.play(group9.animate.shift(DOWN*0.75+LEFT*3.8), sd_tex1.animate.shift(DOWN*0.75+LEFT*3.8), sd_tex2.animate.shift(DOWN*0.75+LEFT*3.8))
    self.play(Create(group11), Write(sv_tex1), Write(sv_tex2))
    self.play(Transform(d19, d20))
    self.play(group11.animate.shift(DOWN*0.75), sv_tex1.animate.shift(DOWN*0.75), sv_tex2.animate.shift(DOWN*0.75))
    self.play(Create(group14), Write(sr_tex1), Write(sr_tex2))
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)

def angle_dist_slide(self):
    svg = ImageMobject("angle_dist.png").scale(0.6)
    rotation_center = LEFT

    # Create the 45 degree angle.
    line1 = Line(LEFT, RIGHT)
    d1 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line1.get_start())
    d2 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line1.get_end())
    n1 = DecimalNumber(1, num_decimal_places=0).move_to(d1.get_center())
    n2 = DecimalNumber(2, num_decimal_places=0).move_to(d2.get_center())
    n3 = DecimalNumber(0, num_decimal_places=0, unit="^\\circ").move_to(line1, DOWN)
    group1 = VGroup(line1, d1, d2, n1, n2, n3).shift(DOWN*1.9+LEFT*3.3).scale(0.5)

    line2 = Line(LEFT, RIGHT)
    line3 = Line(LEFT, RIGHT)
    line3.rotate(
        60 * DEGREES, about_point=rotation_center
    )
    d3 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line2.get_end())
    d4 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line3.get_end())
    d5 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line3.get_start())
    n4 = DecimalNumber(1, num_decimal_places=0).move_to(d3.get_center())
    n5 = DecimalNumber(2, num_decimal_places=0).move_to(d4.get_center())
    n6 = DecimalNumber(3, num_decimal_places=0).move_to(d5.get_center())
    a1 = Angle(line2, line3, radius=0.8, other_angle=False)
    a_num1 = DecimalNumber(60, num_decimal_places=0, unit="^\\circ").move_to(
        Angle(
            line2, line3, radius=1 + 3 * SMALL_BUFF, other_angle=False
        ).point_from_proportion(0.5)
    )
    group2 = VGroup(line2, line3, a1, a_num1, d3, d4, d5, n4, n5, n6).shift(DOWN*2.3+LEFT*1.3).scale(0.5)

    line4 = Line(LEFT, RIGHT)
    line5 = Line(LEFT, RIGHT)
    line5.rotate(
        90 * DEGREES, about_point=rotation_center
    )
    d6 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line4.get_end())
    d7 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line5.get_end())
    d8 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line5.get_start())
    n7 = DecimalNumber(1, num_decimal_places=0).move_to(d6.get_center())
    n8 = DecimalNumber(2, num_decimal_places=0).move_to(d7.get_center())
    n9 = DecimalNumber(3, num_decimal_places=0).move_to(d8.get_center())
    a2 = Angle(line4, line5, radius=0.8, other_angle=False)
    a_num2 = DecimalNumber(90, num_decimal_places=0, unit="^\\circ").move_to(
        Angle(
            line4, line5, radius=1 + 3 * SMALL_BUFF, other_angle=False
        ).point_from_proportion(0.5)
    )
    group3 = VGroup(line4, line5, a2, a_num2, d6, d7, d8, n7, n8, n9).shift(DOWN*2.4+RIGHT*0.8).scale(0.5)

    line6 = Line(LEFT, RIGHT)
    line7 = Line(LEFT, RIGHT)
    line7.rotate(
        180 * DEGREES, about_point=rotation_center
    )
    d9 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line6.get_end())
    d10 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line7.get_end())
    d11 = Dot(color=BLUE, radius=0.4, stroke_width=6, stroke_color=WHITE).move_to(line7.get_start())
    n10 = DecimalNumber(1, num_decimal_places=0).move_to(d9.get_center())
    n11 = DecimalNumber(2, num_decimal_places=0).move_to(d10.get_center())
    n12 = DecimalNumber(3, num_decimal_places=0).move_to(d11.get_center())
    a3 = Angle(line6, line7, radius=0.8, other_angle=False)
    a_num3 = DecimalNumber(180, num_decimal_places=0, unit="^\\circ").move_to(
        Angle(
            line6, line7, radius=1 + 3 * SMALL_BUFF, other_angle=False
        ).point_from_proportion(0.5)
    )
    group4 = VGroup(line6, line7, a3, a_num3, d9, d10, d11, n10, n11, n12).shift(DOWN*2.15+RIGHT*4.2).scale(0.5)

    self.play(FadeIn(svg))
    self.play(Create(group1))
    self.play(Create(group2))
    self.play(Create(group3))
    self.play(Create(group4))
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)

def hyperparameter_slide(self):
    # Write out the title.
    title1 = Text('The main hyperparameter: # of clusters', color=WHITE, t2c={'K-Means Clustering':ORANGE}).shift(UP)
    title2 = Text('Too few: less correlation in clustered beatmaps', color=WHITE, t2c={'Too few':RED}).scale(0.7).next_to(title1, DOWN)
    title3 = Text('Too many: some clusters would have only one map', color=WHITE, t2c={'Too many':GREEN}).scale(0.7).next_to(title2, DOWN)
    self.play(Write(title1, run_time=1.2))
    self.wait(1)
    self.play(Write(title2, run_time=1.2))
    self.wait(1)
    self.play(Write(title3, run_time=1.2))

    # Transition to next scene.
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)

def results1_slide(self):
    png = ImageMobject("angle_map.png").scale(0.4).shift(DOWN*2)
    title1 = Text('Given Map', color=WHITE).scale(0.6).shift(UP*3.5+LEFT*3)
    title2 = Text('Recommended Map', color=WHITE).scale(0.6).shift(UP*3.5+RIGHT*3)

    self.play(FadeIn(png), Write(title1), Write(title2))
    self.wait(10)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)

def results2_slide(self):
    png = ImageMobject("distance_map.png").scale(0.4).shift(DOWN*2)
    title1 = Text('Given Map', color=WHITE).scale(0.6).shift(UP*3.5+LEFT*3)
    title2 = Text('Recommended Map', color=WHITE).scale(0.6).shift(UP*3.5+RIGHT*3)

    self.play(FadeIn(png), Write(title1), Write(title2))
    self.wait(10)
    self.play(*[FadeOut(mob)for mob in self.mobjects])
    self.wait(1)



class OsuManim(Scene):
    def construct(self):
        # title_slide(self)
        # osu_game_slide(self)
        # features_slide(self)
        # angle_dist_slide(self)
        # hyperparameter_slide(self)
        results1_slide(self)
        results2_slide(self)