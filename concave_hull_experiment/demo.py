"""Interactive poster demo.

Single matplotlib window: pick a dataset on the right, flip feature toggles,
hit Run, watch the concave hull build edge by edge.

Run:
  python -m concave_hull_experiment.demo
  python concave_hull_experiment/demo.py

Keyboard (focus the window):
  space  step one iteration  (only in step mode)
  a      toggle autoplay
  +/-    autoplay faster / slower
  q      skip to the end of the current run
  esc    close
"""
import glob
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, RadioButtons, Slider

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from concave_hull_experiment.checkpoints import select_checkpoints
    from concave_hull_experiment.concave_hull import ConfigurableConcaveHull, StepState
    from concave_hull_experiment.config import ConcaveHullConfig
else:
    from .checkpoints import select_checkpoints
    from .concave_hull import ConfigurableConcaveHull, StepState
    from .config import ConcaveHullConfig


Point = tuple[float, float]

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
TROUBLESOME_UNIT_DISK = "__unit_disk_checkpoint_failure_n250_seed0__"


# ---------------------------------------------------------------------------
# Dataset discovery + loading
# ---------------------------------------------------------------------------
def _list_datasets() -> list[tuple[str, str]]:
    """Return (label, path-or-sentinel) pairs in display order."""
    csvs = sorted(glob.glob(os.path.join(DATASETS_DIR, "*.csv")))
    return [
        ("Troublesome unit disk (n=250, seed=0)", TROUBLESOME_UNIT_DISK),
        *((os.path.basename(p), p) for p in csvs),
    ]


def _load_dataset(path: str) -> list[Point]:
    if path == TROUBLESOME_UNIT_DISK:
        rng = np.random.default_rng(0)
        points: list[Point] = []
        while len(points) < 250:
            x, y = rng.uniform(-1.0, 1.0, size=2)
            if x * x + y * y <= 1.0:
                points.append((float(x), float(y)))
        return points
    arr = np.loadtxt(path, delimiter=",", skiprows=1)
    return [(float(x), float(y)) for x, y in arr]


# ---------------------------------------------------------------------------
# Live plot — owns the main axes and updates per-step.
# ---------------------------------------------------------------------------
class LivePlot:
    """Per-step drawing for the demo. Mirrors viz.py:StepVisualizer.callback."""

    def __init__(self, ax):
        self.ax = ax
        self.ax.set_aspect("equal")
        self._scatter = None
        self._checkpoints = None
        (self._hull_line,) = ax.plot([], [], color="red", linewidth=1.0, zorder=4)
        self._hull_dots = ax.scatter([], [], s=10, color="red", zorder=5)
        self._candidate_dots = ax.scatter([], [], s=24, color="green", zorder=6)
        (self._current_dot,) = ax.plot(
            [], [], marker="o", color="black", markersize=10, zorder=7,
        )
        (self._accepted_edge,) = ax.plot(
            [], [], color="blue", linewidth=2.5, zorder=8,
        )
        self._status = ax.text(
            0.02, 0.98, "", transform=ax.transAxes, va="top", ha="left",
            fontsize=10, family="monospace",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"),
        )

    def load_points(self, points: list[Point], checkpoint_strategy: str | None) -> None:
        """Re-bind the background scatter + checkpoints overlay for a new dataset."""
        self.clear_run_artists()
        if self._scatter is not None:
            self._scatter.remove()
        if self._checkpoints is not None:
            self._checkpoints.remove()
            self._checkpoints = None

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self._scatter = self.ax.scatter(xs, ys, s=4, color="lightgray", zorder=1)

        if checkpoint_strategy and checkpoint_strategy != "none":
            try:
                cps = select_checkpoints(points, checkpoint_strategy)
                self._checkpoints = self.ax.scatter(
                    [p[0] for p in cps], [p[1] for p in cps],
                    s=120, color="blue", marker="*", zorder=10,
                )
            except Exception:
                pass

        # Tight view with a 5% pad.
        if xs:
            pad_x = 0.05 * (max(xs) - min(xs) or 1.0)
            pad_y = 0.05 * (max(ys) - min(ys) or 1.0)
            self.ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
            self.ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)

    def clear_run_artists(self) -> None:
        self._hull_line.set_data([], [])
        self._hull_dots.set_offsets(np.empty((0, 2)))
        self._candidate_dots.set_offsets(np.empty((0, 2)))
        self._current_dot.set_data([], [])
        self._accepted_edge.set_data([], [])
        self._status.set_text("")

    def update(self, state: StepState) -> None:
        hx = [p[0] for p in state.hull]
        hy = [p[1] for p in state.hull]
        self._hull_line.set_data(hx, hy)
        self._hull_dots.set_offsets(np.column_stack([hx, hy]) if hx else np.empty((0, 2)))
        self._current_dot.set_data([state.current[0]], [state.current[1]])

        if state.candidates:
            self._candidate_dots.set_offsets(
                np.array([[p[0], p[1]] for p in state.candidates])
            )
        else:
            self._candidate_dots.set_offsets(np.empty((0, 2)))

        if state.accepted is not None and not state.rolled_back:
            self._accepted_edge.set_data(
                [state.current[0], state.accepted[0]],
                [state.current[1], state.accepted[1]],
            )
        else:
            self._accepted_edge.set_data([], [])

    def set_status(self, text: str) -> None:
        self._status.set_text(text)


# ---------------------------------------------------------------------------
# Demo controller — wires widgets to the algorithm.
# ---------------------------------------------------------------------------
class Demo:
    def __init__(self):
        self.fig = plt.figure(figsize=(15, 9))
        self.fig.canvas.manager.set_window_title("Concave hull — live demo")

        # Layout: big plot on the left (~64%), control sidebar on the right.
        gs = self.fig.add_gridspec(1, 2, width_ratios=[2.2, 1.0], wspace=0.25)
        self.ax_plot = self.fig.add_subplot(gs[0, 0])
        self.live = LivePlot(self.ax_plot)

        # Sidebar — manually-positioned widget axes inside gs[0, 1] region.
        self._sidebar_x = 0.69      # left edge in figure coords
        self._sidebar_w = 0.28      # width
        cur_y = 0.93                # cursor: top of next widget

        self.datasets = _list_datasets()
        dataset_labels = [name for name, _ in self.datasets]

        # Defaults
        self.dataset_choice = dataset_labels[0] if dataset_labels else ""
        self.k_growth_choice = "linear"
        self.failure_choice = "restart"
        self.checkpoint_choice = "convex_hull"
        self.intersection_choice = "bucketed"
        self.initial_k = 3
        self.autoplay_delay = 0.02

        self._restarts = 0
        self._rollbacks = 0
        self._prev_iteration = -1
        self._autoplay = True
        self._skip = False
        self._advance = False
        self._running = False

        cur_y = self._add_dropdown("Dataset", dataset_labels, "dataset_choice", cur_y)
        cur_y -= 0.02
        cur_y = self._add_radio("k_growth", ["linear", "exponential", "binary_search"],
                                "k_growth_choice", cur_y)
        cur_y -= 0.02
        cur_y = self._add_radio("failure", ["restart", "checkpoint"],
                                "failure_choice", cur_y)
        cur_y -= 0.02
        cur_y = self._add_radio("checkpoint", ["none", "extreme", "convex_hull"],
                                "checkpoint_choice", cur_y)
        cur_y -= 0.02
        cur_y = self._add_radio("intersection", ["naive", "bucketed"],
                                "intersection_choice", cur_y)

        cur_y -= 0.02
        cur_y = self._add_dropdown("initial_k", [3, 4, 5, 6, 7, 8, 10, 12, 15, 20],
                                   "initial_k", cur_y, coerce=int)
        cur_y -= 0.02
        cur_y = self._add_slider("delay (s)", 0.0, 0.2, 0.02, "autoplay_delay", cur_y, valfmt="%.3f")

        # Buttons
        cur_y -= 0.01
        btn_h = 0.045
        bx_run = self.fig.add_axes([self._sidebar_x, cur_y - btn_h, self._sidebar_w / 2 - 0.005, btn_h])
        bx_reset = self.fig.add_axes([self._sidebar_x + self._sidebar_w / 2 + 0.005, cur_y - btn_h,
                                      self._sidebar_w / 2 - 0.005, btn_h])
        self.btn_run = Button(bx_run, "Run")
        self.btn_reset = Button(bx_reset, "Reset")
        self.btn_run.on_clicked(self._on_run)
        self.btn_reset.on_clicked(self._on_reset)

        # Tip strip at the bottom of the sidebar.
        self.fig.text(self._sidebar_x, 0.015,
                      "keys: space=step  a=autoplay  +/-=speed  q=skip  esc=close",
                      fontsize=7, color="gray")

        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        # Initial dataset load.
        self._reload_dataset()

    # -----------------------------------------------------------------------
    # Widget helpers
    # -----------------------------------------------------------------------
    def _add_radio(self, label, options, attr, cur_y, *, height_per_row=0.028):
        h = max(0.06, height_per_row * len(options) + 0.02)
        self.fig.text(self._sidebar_x, cur_y, label, fontsize=9, weight="bold")
        ax = self.fig.add_axes([self._sidebar_x, cur_y - h - 0.005, self._sidebar_w, h])
        ax.set_facecolor("#f7f7f7")
        rb = RadioButtons(ax, options, active=options.index(getattr(self, attr))
                                                  if getattr(self, attr) in options else 0)
        for lbl in rb.labels:
            lbl.set_fontsize(8)

        def _cb(val, _attr=attr):
            setattr(self, _attr, val)
            if _attr == "dataset_choice" or _attr == "checkpoint_choice":
                self._reload_dataset()

        rb.on_clicked(_cb)
        setattr(self, f"_rb_{attr}", rb)  # keep alive
        return cur_y - h - 0.02

    def _add_dropdown(self, label, options, attr, cur_y, *, coerce=None):
        """A click-to-expand picker: closed shows the current selection; open
        shows the full list of options floating over the plot area. Click an
        option to choose it and collapse the list. Scales to any number of
        datasets without using sidebar space.

        ``options`` are the labels shown to the user. ``coerce`` (optional) maps
        the chosen label to the value stored on ``attr`` — e.g. ``int`` for a
        discrete numeric picker.
        """
        h = 0.04
        self.fig.text(self._sidebar_x, cur_y, label, fontsize=9, weight="bold")
        btn_ax = self.fig.add_axes([self._sidebar_x, cur_y - h - 0.005, self._sidebar_w, h])
        cur_val = getattr(self, attr)
        labels = [str(o) for o in options]
        current = str(cur_val) if str(cur_val) in labels else (labels[0] if labels else "")
        if current:
            setattr(self, attr, coerce(current) if coerce else current)
        btn = Button(btn_ax, f"{current}  ▼")
        btn.label.set_fontsize(9)

        state = {"open": False, "popup_axes": [], "popup_buttons": []}

        def _close():
            for ax in state["popup_axes"]:
                ax.remove()
            state["popup_axes"] = []
            state["popup_buttons"] = []
            state["open"] = False
            self.fig.canvas.draw_idle()

        def _select(opt):
            setattr(self, attr, coerce(opt) if coerce else opt)
            btn.label.set_text(f"{opt}  ▼")
            _close()
            # Datasets and checkpoint strategy both need a re-render of the canvas.
            if attr in ("dataset_choice", "checkpoint_choice"):
                self._reload_dataset()

        def _open(_event):
            if state["open"]:
                _close()
                return
            row_h = 0.035
            n = len(options)
            # Float the list to the LEFT of the sidebar so it doesn't cover its own button.
            popup_x = self._sidebar_x - 0.30
            popup_w = 0.29
            top = cur_y - h - 0.01
            for i, opt in enumerate(labels):
                y = top - (i + 1) * row_h
                if y < 0.02:
                    break  # ran out of vertical space — truncate cleanly
                ax = self.fig.add_axes([popup_x, y, popup_w, row_h * 0.9])
                ax.set_zorder(50)
                ob = Button(ax, opt, color="#ffffff", hovercolor="#e0e8ff")
                ob.label.set_fontsize(9)
                ob.on_clicked(lambda evt, _opt=opt: _select(_opt))
                state["popup_axes"].append(ax)
                state["popup_buttons"].append(ob)
            state["open"] = True
            self.fig.canvas.draw_idle()

        btn.on_clicked(_open)
        setattr(self, f"_dd_{attr}_btn", btn)
        setattr(self, f"_dd_{attr}_state", state)
        return cur_y - h - 0.02

    def _add_slider(self, label, vmin, vmax, vinit, attr, cur_y, *, valfmt="%.2f"):
        h = 0.03
        ax = self.fig.add_axes([self._sidebar_x + 0.04, cur_y - h, self._sidebar_w - 0.05, h])
        sl = Slider(ax, label, vmin, vmax, valinit=vinit, valfmt=valfmt)
        sl.label.set_fontsize(8)
        sl.valtext.set_fontsize(8)

        def _cb(val, _attr=attr):
            if _attr == "initial_k":
                setattr(self, _attr, int(round(val)))
            else:
                setattr(self, _attr, float(val))

        sl.on_changed(_cb)
        setattr(self, f"_sl_{attr}", sl)
        return cur_y - h - 0.02

    # -----------------------------------------------------------------------
    # Dataset (re-)load — also redraws checkpoints overlay.
    # -----------------------------------------------------------------------
    def _reload_dataset(self):
        if not self.dataset_choice:
            return
        path = dict(self.datasets)[self.dataset_choice]
        try:
            self.points = _load_dataset(path)
        except Exception as e:
            self.live.set_status(f"load error: {e}")
            self.points = []
            self.fig.canvas.draw_idle()
            return
        cp_strategy = self.checkpoint_choice if self.failure_choice == "checkpoint" else None
        self.live.load_points(self.points, cp_strategy)
        self.live.set_status(f"loaded {self.dataset_choice}\n{len(self.points)} points")
        self.fig.canvas.draw_idle()

    # -----------------------------------------------------------------------
    # Keyboard
    # -----------------------------------------------------------------------
    def _on_key(self, event):
        key = (event.key or "").lower()
        if key == " ":
            self._advance = True
        elif key == "a":
            self._autoplay = not self._autoplay
            self._advance = True
        elif key in ("+", "="):
            self.autoplay_delay = max(self.autoplay_delay * 0.6, 0.001)
            self._sl_autoplay_delay.set_val(self.autoplay_delay)
        elif key == "-":
            self.autoplay_delay = min(self.autoplay_delay * 1.6, 2.0)
            self._sl_autoplay_delay.set_val(self.autoplay_delay)
        elif key == "q":
            self._skip = True
            self._advance = True
        elif key == "escape":
            plt.close(self.fig)

    # -----------------------------------------------------------------------
    # Run / Reset
    # -----------------------------------------------------------------------
    def _on_run(self, _event):
        if self._running or not self.points:
            return
        self._running = True
        self._restarts = 0
        self._rollbacks = 0
        self._prev_iteration = -1
        self._skip = False

        try:
            cfg = ConcaveHullConfig(
                initial_k=self.initial_k,
                knn_backend="scipy",
                k_growth_strategy=self.k_growth_choice,
                failure_strategy=self.failure_choice,
                checkpoint_strategy=self.checkpoint_choice
                    if self.failure_choice == "checkpoint" else "none",
                intersection_strategy=self.intersection_choice,
                # A closed polygon is successful only if it encloses every
                # input point. Restart mode raises k and tries again; checkpoint
                # mode uses its containment-recovery retry.
                validate_final_hull="enforce",
            )
        except ValueError as e:
            self.live.set_status(f"config error:\n{e}")
            self.fig.canvas.draw_idle()
            self._running = False
            return

        try:
            result = ConfigurableConcaveHull().run(
                self.points, cfg, on_step=self._on_step,
            )
        except Exception as e:
            self.live.set_status(f"run error: {e}")
            self.fig.canvas.draw_idle()
            self._running = False
            return

        final_state = (
            f"done — success={result.success}\n"
            f"final_k={result.final_k}\n"
            f"hull_len={len(result.hull)}\n"
            f"outside={result.points_outside if result.points_outside is not None else 'n/a'}\n"
            f"restarts={self._restarts}  rollbacks={self._rollbacks}"
        )
        if not result.success:
            final_state += f"\nreason: {result.failure_reason}"
        self.live.set_status(final_state)
        self.fig.canvas.draw_idle()
        self._running = False

    def _on_reset(self, _event):
        if self._running:
            self._skip = True
            return
        self.live.clear_run_artists()
        cp_strategy = self.checkpoint_choice if self.failure_choice == "checkpoint" else None
        self.live.load_points(self.points, cp_strategy)
        self.live.set_status(f"ready — {self.dataset_choice}\n{len(self.points)} points")
        self.fig.canvas.draw_idle()

    # -----------------------------------------------------------------------
    # on_step callback — fires once per algorithm iteration
    # -----------------------------------------------------------------------
    def _on_step(self, state: StepState):
        if self._skip:
            return

        # Restart detection: in restart-mode each fresh _attempt resets `iteration`
        # back to 2 on a non-rollback step. Checkpoint-mode also drops the iteration
        # counter on its rolled_back step — gating on `not rolled_back` keeps the
        # two counters from double-counting the same event.
        if (not state.rolled_back and self._prev_iteration >= 0
                and state.iteration < self._prev_iteration):
            self._restarts += 1
        self._prev_iteration = state.iteration

        if state.rolled_back:
            self._rollbacks += 1

        self.live.update(state)
        self.live.set_status(
            f"iter:      {state.iteration}\n"
            f"hull:      {len(state.hull)}\n"
            f"k:         {state.k}\n"
            f"restarts:  {self._restarts}\n"
            f"rollbacks: {self._rollbacks}\n"
            f"region:    {state.region if state.region is not None else '-'}\n"
            f"action:    {'ROLLBACK' if state.rolled_back else 'accept'}"
        )
        self.fig.canvas.draw_idle()

        if self._autoplay:
            plt.pause(max(self.autoplay_delay, 0.001))
        else:
            self._advance = False
            while not self._advance and plt.fignum_exists(self.fig.number):
                plt.pause(0.02)

    def show(self):
        plt.show()


def main():
    Demo().show()


if __name__ == "__main__":
    main()
