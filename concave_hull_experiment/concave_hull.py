"""Configurable Moreira–Santos kNN concave hull.

Toggles:
  - knn_backend            ("scipy")
  - k_growth_strategy      ("linear" | "exponential" | "binary_search")
  - failure_strategy       ("restart" | "checkpoint")
  - checkpoint_strategy    ("none" | "extreme" | "convex_hull")
  - intersection_strategy  ("naive" | "bucketed")

restart  : on intersection, throw the hull away and retry with the next k.
checkpoint: on intersection, trim the hull back to the latest checkpoint at or
            before the failure, restore points to the kNN pool, bump k, and
            continue. If an enforced containment check finds excluded points
            after closure, raise k and retry the checkpoint construction.
"""
from dataclasses import dataclass, replace

from .checkpoints import select_checkpoints, trim_to_checkpoint
from .config import ConcaveHullConfig
from .geometry import (
    cleanList,
    compute_angle,
    find_lowest_point,
    points_outside_hull,
    sortByAngle,
)
from .intersections import IntersectionIndex, make_intersection_index
from .k_growth import (
    BinarySearchKGrowth,
    ExponentialKGrowth,
    KGrowth,
    LinearKGrowth,
)
from .knn import make_knn_index


def _make_k_growth(config: ConcaveHullConfig) -> KGrowth:
    if config.k_growth_strategy == "linear":
        return LinearKGrowth()
    if config.k_growth_strategy == "exponential":
        return ExponentialKGrowth(rate=config.k_growth_rate)
    if config.k_growth_strategy == "binary_search":
        return BinarySearchKGrowth()
    raise ValueError(f"unknown k_growth_strategy: {config.k_growth_strategy!r}")


def _bump_region_k(region_k_values: list[int], region: int, new_k: int, scope: str) -> None:
    """Raise k after a checkpoint failure, honoring checkpoint_k_scope.

    "per_region": bump only the failing region's k — independent and adaptive, but each
    region re-climbs from initial_k (the cost the global-k variant is meant to avoid).
    "global": raise a single shared k across ALL regions (monotone), like the restart
    baseline's global k, while still keeping the trimmed prefix.
    """
    if scope == "global":
        for i in range(len(region_k_values)):
            if new_k > region_k_values[i]:
                region_k_values[i] = new_k
    else:
        region_k_values[region] = new_k


def _next_checkpoint_k(growth: KGrowth, old_k: int, n: int) -> int | None:
    """Return the next checkpoint k, including one final all-points attempt at k=n."""
    new_k = growth.next_k(old_k, succeeded=False, n=n)
    if new_k is None and old_k < n:
        return n
    return new_k


Point = tuple[float, float]


@dataclass
class HullResult:
    hull: list[Point]
    success: bool
    final_k: int
    failure_reason: str | None = None
    # None = validation not run; 0 = all points inside; >0 = some points outside.
    points_outside: int | None = None
    # restart-mode: count of failed attempts.
    # checkpoint-mode: count of local rollbacks plus containment retries.
    restarts: int = 0
    # Sum of hull edges thrown away across all restarts/rollbacks.
    # Divide by `restarts` to get avg work-discarded per failure event.
    total_restart_edges: int = 0


@dataclass
class StepState:
    """Snapshot passed to on_step after each main-loop iteration."""
    iteration: int            # main-loop step counter
    hull: list[Point]         # hull so far (already includes `accepted` if not a rollback)
    current: Point            # current hull tip
    candidates: list[Point]   # angle-sorted kNN candidates considered this step
    accepted: Point | None    # the chosen one, or None if this was a rollback
    rolled_back: bool         # True iff this step was a checkpoint trim
    region: int | None        # current_region (checkpoint mode), else None
    k: int                    # k used for the current region/attempt


class ConfigurableConcaveHull:
    def run(
        self,
        points: list[Point],
        config: ConcaveHullConfig,
        *,
        on_step=None,
    ) -> HullResult:
        """on_step: optional callable receiving a StepState after each main-loop iteration."""
        cleaned = cleanList([tuple(p) for p in points])

        if len(cleaned) < 3:
            return HullResult(
                hull=cleaned, success=False, final_k=config.initial_k,
                failure_reason="fewer than 3 unique points",
            )
        if len(cleaned) == 3:
            return HullResult(
                hull=cleaned, success=True, final_k=config.initial_k,
            )

        if config.failure_strategy == "checkpoint":
            return self._run_with_checkpoints(cleaned, config, on_step=on_step)
        return self._run_with_restart(cleaned, config, on_step=on_step)

    def _run_with_restart(
        self, points: list[Point], config: ConcaveHullConfig, *, on_step=None
    ) -> HullResult:
        n = len(points)
        growth = _make_k_growth(config)
        k: int | None = growth.initial_k(n, config.initial_k)
        attempts = 0
        restarts = 0
        total_restart_edges = 0
        # Track the smallest-k success across attempts (matters for binary search).
        best: HullResult | None = None
        last_k = k

        while k is not None and k < n:
            attempts += 1
            last_k = k
            hull, partial_size = self._attempt(points, k, config, on_step=on_step)
            succeeded = hull is not None

            # Validation: count points outside the closed hull.
            # In "enforce" mode, a leaky hull is treated as a failure so the outer loop
            # bumps k and tries again — the original Moreira-Santos correctness check.
            outside: int | None = None
            if succeeded and config.validate_final_hull != "off":
                outside = points_outside_hull(points, hull)
                if config.validate_final_hull == "enforce" and outside > 0:
                    succeeded = False

            if succeeded:
                if best is None or k < best.final_k:
                    best = HullResult(
                        hull=hull, success=True, final_k=k, points_outside=outside,
                    )
            else:
                restarts += 1
                total_restart_edges += partial_size
            k = growth.next_k(k, succeeded, n)

        if best is not None:
            best.restarts = restarts
            best.total_restart_edges = total_restart_edges
            return best
        return HullResult(
            hull=[], success=False, final_k=last_k or config.initial_k,
            failure_reason=f"no valid hull found after {attempts} attempt(s)",
            restarts=restarts, total_restart_edges=total_restart_edges,
        )

    def _run_with_checkpoints(
        self, points: list[Point], config: ConcaveHullConfig, *, on_step=None
    ) -> HullResult:
        """Run checkpoint trimming, retrying with a larger k if containment fails.

        Dead ends are still recovered locally within each attempt.  A closed hull
        with excluded points is a global failure, however: until an excluded point
        can be assigned reliably to one checkpoint region, the conservative recovery
        is to raise the starting k and rebuild.  This preserves the original
        all-points-enclosed success condition when validation is set to ``enforce``.
        """
        if config.validate_final_hull != "enforce":
            return self._checkpoint_attempt(points, config, on_step=on_step)

        n = len(points)
        growth = _make_k_growth(config)
        retry_k = growth.initial_k(n, config.initial_k)
        retries = 0
        total_rollbacks = 0
        total_discarded_edges = 0
        last_k = retry_k

        while retry_k is not None and retry_k <= n:
            last_k = retry_k
            attempt_config = replace(
                config,
                initial_k=retry_k,
                validate_final_hull="report",
            )
            result = self._checkpoint_attempt(
                points, attempt_config, on_step=on_step
            )
            total_rollbacks += result.restarts
            total_discarded_edges += result.total_restart_edges

            if not result.success:
                result.restarts = total_rollbacks + retries
                result.total_restart_edges = total_discarded_edges
                return result

            if result.points_outside == 0:
                result.restarts = total_rollbacks + retries
                result.total_restart_edges = total_discarded_edges
                return result

            # A closed-but-incomplete hull is discarded just as it is in the
            # original algorithm.  The next attempt starts above the largest k
            # reached anywhere in this checkpoint run.
            retries += 1
            total_discarded_edges += len(result.hull)
            last_k = result.final_k
            retry_k = _next_checkpoint_k(growth, result.final_k, n)

        return HullResult(
            hull=[],
            success=False,
            final_k=last_k or config.initial_k,
            failure_reason=(
                f"no containing checkpoint hull found after {retries + 1} attempt(s)"
            ),
            restarts=total_rollbacks + retries,
            total_restart_edges=total_discarded_edges,
        )

    def _checkpoint_attempt(
        self, points: list[Point], config: ConcaveHullConfig, *, on_step=None
    ) -> HullResult:
        """One continuous checkpoint run with local rollback on dead ends."""
        # ---------- 1. Setup: checkpoints divide the hull into independent regions ----------
        n = len(points)
        growth = _make_k_growth(config)
        initial_k = growth.initial_k(n, config.initial_k)

        # Anchor points around the perimeter (extreme = 4 cardinals, convex_hull = ~all CH verts).
        # Each consecutive pair defines a region with its own k.
        checkpoints = select_checkpoints(points, config.checkpoint_strategy)
        checkpoint_set = {tuple(p) for p in checkpoints}
        region_k_values = [initial_k] * len(checkpoints)
        current_region = 0

        # ---------- 2. Build the data structures the loop reads from ----------
        knn = make_knn_index(config.knn_backend)
        knn.build(points)
        edges = make_intersection_index(
            config.intersection_strategy, points, config.intersection_bucket_size
        )
        first_point = find_lowest_point(points)
        knn.remove(first_point)

        # ---------- 3. Hull state ----------
        hull: list[Point] = [first_point]
        current = first_point
        prev_angle = 0.0
        step = 2
        first_point_in_pool = False  # tracks whether first_point is currently re-added

        rollbacks = 0
        total_restart_edges = 0
        max_rollbacks = n * 4  # safety net: bounds the wrong-checkpoint loop

        while (current != first_point or step == 2) and knn.size() > 0:
            # ---------- 4. Keep first_point available once the hull is long enough to close ----------
            # Held out at start so we don't accidentally close the hull immediately. Re-introduced
            # at step >= 5; pulled back out if a trim drops us below that threshold.
            if step >= 5 and not first_point_in_pool:
                knn.add(first_point)
                first_point_in_pool = True
            elif step < 5 and first_point_in_pool:
                knn.remove(first_point)
                first_point_in_pool = False

            # ---------- 5. Pick the next candidate edge ----------
            # k is per-region, not global — sparse and dense regions can grow independently.
            k = min(region_k_values[current_region], knn.size())
            if k <= 0:
                return HullResult(
                    hull=[], success=False, final_k=max(region_k_values),
                    failure_reason="kNN pool exhausted",
                    restarts=rollbacks, total_restart_edges=total_restart_edges,
                )

            candidates = knn.query(current, k)
            ordered = sortByAngle(candidates, current, prev_angle)
            accepted = self._first_non_intersecting(ordered, current, edges)

            # ---------- 6. Failure path: roll back, then bump the landing region's k ----------
            if accepted is None:
                # Trim first to figure out which region we'll restart in. The intersection-walk
                # can land at a checkpoint earlier than the one we entered the current region from,
                # so bumping current_region's k before the trim would bump the wrong slot.
                pre_trim_len = len(hull)
                roll = trim_to_checkpoint(
                    hull, knn, edges, ordered, checkpoints, checkpoint_set, first_point
                )
                hull = roll.hull
                total_restart_edges += pre_trim_len - len(hull)
                current = roll.current
                prev_angle = roll.prev_angle
                step = roll.step
                current_region = roll.current_region

                # Bump the k of the region we're about to re-traverse.
                old_k = region_k_values[current_region]
                new_k = _next_checkpoint_k(growth, old_k, n)
                if new_k is None:
                    return HullResult(
                        hull=[], success=False, final_k=old_k,
                        failure_reason=f"region {current_region} k exhausted",
                        restarts=rollbacks, total_restart_edges=total_restart_edges,
                    )
                _bump_region_k(region_k_values, current_region, new_k, config.checkpoint_k_scope)

                rollbacks += 1
                if rollbacks > max_rollbacks:
                    return HullResult(
                        hull=[], success=False, final_k=max(region_k_values),
                        failure_reason=f"rollback limit ({max_rollbacks}) exceeded",
                        restarts=rollbacks, total_restart_edges=total_restart_edges,
                    )

                if on_step is not None:
                    on_step(StepState(
                        iteration=step, hull=list(hull), current=current,
                        candidates=ordered, accepted=None,
                        rolled_back=True, region=current_region,
                        k=region_k_values[current_region],
                    ))
                continue

            # ---------- 7. Accept the candidate: extend the hull by one edge ----------
            prev_current = current
            edges.add_edge(current, accepted)
            current = accepted
            hull.append(current)
            prev_angle = compute_angle(hull[-1], hull[-2])
            knn.remove(current)
            step += 1

            # ---------- 8. Region advancement (or rollback on out-of-order checkpoint hit) ----------
            # Hitting checkpoint N+1 advances the region. Hitting any OTHER checkpoint means
            # the algorithm wandered into the wrong region — undo the append, bump this
            # region's k, and trim back so we can try a different angle.
            if tuple(current) in checkpoint_set:
                next_idx = (current_region + 1) % len(checkpoints)
                if current == first_point:
                    # Returning to the start closes the polygon even if some
                    # checkpoints were skipped. Final-hull containment
                    # validation decides whether that closure is acceptable;
                    # in enforce mode, excluded points trigger a larger-k retry.
                    pass
                elif tuple(current) == tuple(checkpoints[next_idx]):
                    current_region = next_idx
                else:
                    # Wrong checkpoint — algorithm overshot N+1 and landed on some CP > N+1.
                    # Trim back to CP N (the current region's anchor) and bump region N's k.
                    # This is NOT an intersection failure, so we don't use the intersection-walk
                    # variant of trim — that can trim too aggressively past other regions.
                    wrong_cp = current
                    hull.pop()
                    edges.remove_edge(prev_current, wrong_cp)
                    knn.add(wrong_cp)
                    step -= 1

                    # Bump region N's k so the next attempt has more close-in candidates,
                    # increasing the chance of a tighter (more convex) path that reaches N+1.
                    old_k = region_k_values[current_region]
                    new_k = _next_checkpoint_k(growth, old_k, n)
                    if new_k is None:
                        return HullResult(
                            hull=[], success=False, final_k=old_k,
                            failure_reason=f"region {current_region} k exhausted (out-of-order checkpoint)",
                            restarts=rollbacks, total_restart_edges=total_restart_edges,
                        )
                    _bump_region_k(region_k_values, current_region, new_k, config.checkpoint_k_scope)
                    rollbacks += 1
                    if rollbacks > max_rollbacks:
                        return HullResult(
                            hull=[], success=False, final_k=max(region_k_values),
                            failure_reason=f"rollback limit ({max_rollbacks}) exceeded (out-of-order checkpoint)",
                            restarts=rollbacks, total_restart_edges=total_restart_edges,
                        )

                    # Walk hull backward to find CP N (the most recent checkpoint).
                    trim_to = 0
                    for idx in range(len(hull) - 1, -1, -1):
                        if tuple(hull[idx]) in checkpoint_set:
                            trim_to = idx
                            break

                    # Restore the trimmed-off points + edges to the indexes.
                    for pt in hull[trim_to + 1:]:
                        if pt == first_point:
                            continue
                        knn.add(pt)
                    for i in range(trim_to, len(hull) - 1):
                        edges.remove_edge(hull[i], hull[i + 1])

                    total_restart_edges += len(hull) - (trim_to + 1)
                    hull = hull[: trim_to + 1]
                    current = hull[-1]
                    prev_angle = compute_angle(hull[-1], hull[-2]) if len(hull) >= 2 else 0.0
                    step = len(hull) + 1
                    # current_region stays the same — CP N is the anchor of region N.

                    if on_step is not None:
                        on_step(StepState(
                            iteration=step, hull=list(hull), current=current,
                            candidates=ordered, accepted=None,
                            rolled_back=True, region=current_region,
                            k=region_k_values[current_region],
                        ))
                    continue

            if on_step is not None:
                on_step(StepState(
                    iteration=step, hull=list(hull), current=prev_current,
                    candidates=ordered, accepted=accepted,
                    rolled_back=False, region=current_region, k=k,
                ))

        # ---------- 9. Hull closed ----------
        # final_k = worst per-region k = closest single-number summary of "how hard was this hull?"
        outside: int | None = None
        if config.validate_final_hull != "off":
            outside = points_outside_hull(points, hull)
        return HullResult(
            hull=hull, success=True, final_k=max(region_k_values),
            points_outside=outside,
            restarts=rollbacks, total_restart_edges=total_restart_edges,
        )

    def _attempt(
        self, points: list[Point], k: int, config: ConcaveHullConfig, *, on_step=None
    ) -> tuple[list[Point] | None, int]:
        """Single Moreira–Santos pass with fixed k.

        Returns (hull, partial_size). On success hull is the closed polygon and
        partial_size == len(hull). On intersection failure hull is None and
        partial_size == len(hull at failure) — the wasted-work count.
        """
        knn = make_knn_index(config.knn_backend)
        knn.build(points)

        edges = make_intersection_index(
            config.intersection_strategy, points, config.intersection_bucket_size
        )

        first_point = find_lowest_point(points)
        knn.remove(first_point)

        hull: list[Point] = [first_point]
        current = first_point
        prev_angle = 0.0
        step = 2

        while (current != first_point or step == 2) and knn.size() > 0:
            # Re-introduce first_point so the hull can close
            # (matches baseline/concavehull.py:363).
            if step == 5:
                knn.add(first_point)

            candidates = knn.query(current, k)
            ordered = sortByAngle(candidates, current, prev_angle)

            accepted = self._first_non_intersecting(ordered, current, edges)

            if accepted is None:
                # Every candidate intersects an existing edge — retry the whole hull with larger k.
                return None, len(hull)

            prev_current = current
            edges.add_edge(current, accepted)
            current = accepted
            hull.append(current)
            prev_angle = compute_angle(hull[-1], hull[-2])
            knn.remove(current)
            step += 1

            if on_step is not None:
                on_step(StepState(
                    iteration=step, hull=list(hull), current=prev_current,
                    candidates=ordered, accepted=accepted,
                    rolled_back=False, region=None, k=k,
                ))

        return hull, len(hull)

    @staticmethod
    def _first_non_intersecting(
        candidates: list[Point],
        prev_point: Point,
        intersection_index: IntersectionIndex,
    ) -> Point | None:
        """Return the first candidate whose edge from prev_point doesn't cross any stored hull edge.

        do_intersect already returns False for shared-endpoint pairs, so we don't need
        to special-case the most-recent edge or the closing edge.
        """
        for cand in candidates:
            if not intersection_index.would_intersect(prev_point, cand):
                return cand
        return None
