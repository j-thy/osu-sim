from manim import *
import numpy as np

def title_slide(self):
    progress_bar = Line(LEFT*7.1+UP*4, RIGHT*7.1+UP*4, color=ORANGE, stroke_width=30)

    # Write out the title.
    title1 = Text('Using K-Means Clustering', color=WHITE, t2c={'K-Means Clustering':ORANGE}).shift(UP*1.5)
    title2 = Text('to recommend similar beatmaps', color=WHITE).next_to(title1, DOWN)
    title3 = Text('in a rhythm game called osu!', color=WHITE, t2c={'osu!':PINK}).next_to(title2, DOWN)
    name = Text('By Jonathan Ting', color=WHITE, t2c={'osu!':PINK}, font_size = 30).next_to(title3, DOWN)
    self.play(
        Create(progress_bar, run_time=10),
        Succession(
            Write(title1, run_time=1.2),
            Write(title2, run_time=1.2),
            Write(title3, run_time=1.2),
            Write(name, run_time=1.2)
        )
    )

    # Transition to next scene.
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])

def osu_game_slide(self):
    progress_bar = Line(LEFT*7.1+UP*4, RIGHT*7.1+UP*4, color=ORANGE, stroke_width=30)

    # Animate 4 music notes.
    note = SVGMobject("8thNote.svg", fill_color=WHITE, fill_opacity=1, stroke_color=WHITE)
    note_group = VGroup(*[note.copy() for i in range(4)])
    note_group.arrange(RIGHT, buff=2)
    note_group.shift(DOWN*2)
    note_group.scale(0.5)

    # self.play(DrawBorderThenFill(note_group))
    # # Indicate each note.
    # for note in note_group:
    #     self.play(Indicate(note))

    self.play(
        Create(progress_bar, run_time=10),
        Succession(
            DrawBorderThenFill(note_group),
            *[Indicate(note) for note in note_group]
        )
    )

    # Transition to next scene.
    self.wait(1)
    self.play(*[FadeOut(mob)for mob in self.mobjects])


class OsuManim(Scene):
    def construct(self):
        # title_slide(self)
        osu_game_slide(self)