"""Live step-by-step visualization for the concave-hull algorithm.

Standalone — none of the algorithm code imports this. Pass `viz.callback` to
`ConfigurableConcaveHull().run(points, cfg, on_step=viz.callback)` and watch
the hull build edge by edge.

Run as a script for a small demo:
  python -m concave_hull_experiment.viz
  python concave_hull_experiment/viz.py
"""
import matplotlib.pyplot as plt

if __package__ in (None, ""):
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from concave_hull_experiment.checkpoints import select_checkpoints
    from concave_hull_experiment.concave_hull import ConfigurableConcaveHull, StepState
    from concave_hull_experiment.config import ConcaveHullConfig
else:
    from .checkpoints import select_checkpoints
    from .concave_hull import ConfigurableConcaveHull, StepState
    from .config import ConcaveHullConfig


Point = tuple[float, float]


class StepVisualizer:
    """Live step-by-step visualizer.

    Pass `viz.callback` to `ConfigurableConcaveHull().run(points, cfg, on_step=viz.callback)`.

    Keyboard controls (focus on the figure window):
      space  step forward one iteration
      a      toggle autoplay
      +      faster autoplay
      -      slower autoplay
      q      skip to end (callback becomes a no-op)
      esc    close the figure (raises to abort the run)
    """

    def __init__(
        self,
        points: list[Point],
        *,
        checkpoint_strategy: str | None = None,
        autoplay: bool = False,
        delay: float = 0.05,
        title: str = "Concave hull (live)",
    ):
        self.points = points
        self.autoplay = autoplay
        self.delay = delay
        self.skip = False

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_aspect("equal")
        self.ax.set_title(title, fontsize=10)

        # Background scatter — input points.
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.ax.scatter(xs, ys, s=4, color="lightgray", zorder=1)

        # Checkpoints overlay (static).
        if checkpoint_strategy and checkpoint_strategy != "none":
            cps = select_checkpoints(points, checkpoint_strategy)
            self.ax.scatter(
                [p[0] for p in cps], [p[1] for p in cps],
                s=120, color="blue", marker="*", zorder=10, label="checkpoints",
            )

        # Persistent artists, updated each step.
        (self._hull_line,) = self.ax.plot([], [], color="red", linewidth=1.0, zorder=4)
        self._hull_dots = self.ax.scatter([], [], s=10, color="red", zorder=5)
        self._candidate_dots = self.ax.scatter([], [], s=24, color="green", zorder=6)
        (self._current_dot,) = self.ax.plot(
            [], [], marker="o", color="black", markersize=10, zorder=7,
        )
        (self._accepted_edge,) = self.ax.plot(
            [], [], color="blue", linewidth=2.5, zorder=8,
        )
        self._status = self.ax.text(
            0.02, 0.98, "", transform=self.ax.transAxes, va="top", ha="left",
            fontsize=9, family="monospace",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )

        # Keyboard handler.
        self._advance = False
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        plt.show(block=False)

    def _on_key(self, event):
        key = (event.key or "").lower()
        if key == " " or key == "space":
            self._advance = True
        elif key == "a":
            self.autoplay = not self.autoplay
            self._advance = True
        elif key in ("+", "="):
            self.delay = max(self.delay * 0.6, 0.005)
        elif key == "-":
            self.delay = min(self.delay * 1.6, 2.0)
        elif key == "q":
            self.skip = True
            self._advance = True
        elif key == "escape":
            plt.close(self.fig)
            raise KeyboardInterrupt("user closed visualizer")

    def callback(self, state: StepState):
        if self.skip:
            return

        # Hull line + vertices.
        hx = [p[0] for p in state.hull]
        hy = [p[1] for p in state.hull]
        self._hull_line.set_data(hx, hy)
        self._hull_dots.set_offsets(list(zip(hx, hy)) if hx else [[0, 0]])

        # Current vertex (the previous tip).
        self._current_dot.set_data([state.current[0]], [state.current[1]])

        # Candidate dots.
        if state.candidates:
            self._candidate_dots.set_offsets(
                [[p[0], p[1]] for p in state.candidates]
            )
        else:
            self._candidate_dots.set_offsets([[0, 0]])

        # Accepted edge (or recolor on rollback).
        if state.accepted is not None and not state.rolled_back:
            self._accepted_edge.set_data(
                [state.current[0], state.accepted[0]],
                [state.current[1], state.accepted[1]],
            )
            self._accepted_edge.set_color("blue")
        elif state.rolled_back:
            self._accepted_edge.set_data([], [])

        status_lines = [
            f"iter:    {state.iteration}",
            f"hull:    {len(state.hull)}",
            f"region:  {state.region if state.region is not None else '-'}",
            f"k:       {state.k}",
            f"action:  {'ROLLBACK' if state.rolled_back else 'accept'}",
            f"play:    {'AUTO' if self.autoplay else 'STEP'}  delay={self.delay:.2f}",
        ]
        self._status.set_text("\n".join(status_lines))

        self.fig.canvas.draw_idle()

        if self.autoplay:
            plt.pause(self.delay)
        else:
            self._advance = False
            while not self._advance and plt.fignum_exists(self.fig.number):
                plt.pause(0.02)

    def hold(self):
        """Block at the end so the final figure stays open until closed by the user."""
        if plt.fignum_exists(self.fig.number):
            self._status.set_text(self._status.get_text() + "\n[done — close window to exit]")
            self.fig.canvas.draw_idle()
            plt.show()


def _demo():
    """Live step-by-step run on a small dataset.

    Keyboard:  space=step  a=autoplay  +/-=speed  q=skip  esc=close
    """
    import numpy as np
    rng = np.random.default_rng(0)
    pts = []
    while len(pts) < 250:
        x, y = rng.uniform(-1.0, 1.0, size=2)
        if x * x + y * y <= 1.0:
            pts.append((float(x), float(y)))

    cfg = ConcaveHullConfig(
        initial_k=3,
        knn_backend="scipy",
        k_growth_strategy="linear",
        failure_strategy="checkpoint",
        checkpoint_strategy="convex_hull",
        checkpoint_k_scope="global",
        intersection_strategy="bucketed",
        validate_final_hull="enforce",
    )
    viz = StepVisualizer(
        pts,
        checkpoint_strategy="convex_hull",
        autoplay=False,
        title="Failing unit disk: n=250, seed=0 | space=step, a=autoplay, +/-=speed",
    )
    try:
        result = ConfigurableConcaveHull().run(pts, cfg, on_step=viz.callback)
    except KeyboardInterrupt:
        return
    print(f"done: success={result.success} hull_len={len(result.hull)} final_k={result.final_k}")
    viz.hold()


if __name__ == "__main__":
    _demo()
