"""Strategies for choosing k across attempts.

Each strategy decides:
  - what k to start with, given n and config.initial_k
  - what k to try next, given the previous k and whether it succeeded
    (return None to stop searching)

The main run() loop picks the best (smallest-k) successful hull found.
"""
from abc import ABC, abstractmethod
import math


class KGrowth(ABC):
    @abstractmethod
    def initial_k(self, n: int, config_initial_k: int) -> int: ...

    @abstractmethod
    def next_k(self, k: int, succeeded: bool, n: int) -> int | None:
        """Return the next k to try, or None to stop searching."""


class LinearKGrowth(KGrowth):
    """k starts at config.initial_k, grows by +1 on failure, stops on first success."""

    def initial_k(self, n, config_initial_k):
        return max(3, config_initial_k)

    def next_k(self, k, succeeded, n):
        if succeeded:
            return None  # first success wins
        nxt = k + 1
        return nxt if nxt < n else None


class ExponentialKGrowth(KGrowth):
    """Constant-ratio geometric growth with an explicit all-candidates cap.

    On failure, use ``ceil(k * rate)`` while guaranteeing progress by at least
    one.  If that value would pass the largest meaningful restart value,
    ``n - 1`` is tested exactly once before stopping.  This matches the growth
    schedule analyzed in the paper and preserves its termination argument.
    """

    def __init__(self, rate: float = 2.0):
        if rate <= 1.0:
            raise ValueError(f"exponential rate must be > 1.0, got {rate}")
        self.rate = rate

    def initial_k(self, n, config_initial_k):
        return max(3, config_initial_k)

    def next_k(self, k, succeeded, n):
        if succeeded:
            return None  # first success wins
        cap = n - 1
        if k >= cap:
            return None
        nxt = max(k + 1, math.ceil(k * self.rate))
        return min(nxt, cap)


class BinarySearchKGrowth(KGrowth):
    """Bisect for the smallest k that produces a valid hull.

    Start at k = n // 2.
    On success: this k works, try smaller (move upper bound down).
    On failure: this k doesn't work, try larger (move lower bound up).
    Stop when the gap between known-failing-k and known-succeeding-k closes.
    """

    def __init__(self):
        # lo = largest k known to fail (exclusive lower bound on the answer).
        # hi = smallest k known to succeed (the current best answer).
        self.lo: int = 2  # k must be >= 3, so 2 is "no failure recorded"
        self.hi: int | None = None

    def initial_k(self, n, config_initial_k):
        return max(3, n // 2)

    def next_k(self, k, succeeded, n):
        if succeeded:
            self.hi = k
        else:
            self.lo = max(self.lo, k)

        if self.hi is None:
            # No success yet — keep growing until we find one.
            nxt = max(k + 1, k * 2)
            return nxt if nxt < n else None

        # We have a success at self.hi. Bisect (self.lo, self.hi].
        if self.lo + 1 >= self.hi:
            return None  # converged: no integer between lo and hi
        return (self.lo + self.hi) // 2
