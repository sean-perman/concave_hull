"""One-shot extractor: pulls the point-cloud literals out of
`seans_concavehull_4.py` and writes one CSV per dataset.

Re-runnable. The star dataset is procedural — seeded so the output is
deterministic.
"""
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "seans_concavehull_4.py")

# Each entry: (output_csv_name, source_line_range_inclusive).
# Line ranges cover the `points = [...]` block (commented or not) in source.
BLOCKS = [
    ("world_capitals.csv",         (914, 1109)),
    ("us_mainland_cities.csv",     (1133, 1401)),
    ("gray_wolf_sightings.csv",    (1404, 1406)),
    ("coast_redwood_sightings.csv",(1409, 1409)),
]

# Matches a [num, num] pair where num may be negative / decimal.
PAIR = re.compile(r"\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]")


def extract_pairs(text: str) -> list[tuple[float, float]]:
    return [(float(a), float(b)) for a, b in PAIR.findall(text)]


def read_block(path: str, lo: int, hi: int) -> str:
    with open(path) as f:
        lines = f.readlines()
    return "".join(lines[lo - 1 : hi])


def write_csv(out_path: str, points: list[tuple[float, float]]) -> None:
    with open(out_path, "w") as f:
        f.write("x,y\n")
        for x, y in points:
            f.write(f"{x},{y}\n")


def generate_star(num_points: int = 300, num_tips: int = 8, outer_r: float = 100.0,
                  inner_r: float = 4.0, jitter: float = 3.0, seed: int = 42
                  ) -> list[tuple[float, float]]:
    """Ported from the procedural block in seans_concavehull_4.py:1111-1130."""
    rng = random.Random(seed)
    pts = []
    for _ in range(num_points):
        angle = rng.uniform(0, 2 * math.pi)
        sector = angle / (math.pi / num_tips)
        frac = sector - int(sector)
        if int(sector) % 2 == 0:
            base_r = outer_r + (inner_r - outer_r) * frac
        else:
            base_r = inner_r + (outer_r - inner_r) * frac
        r = base_r * (0.7 + 0.3 * rng.random())
        x = r * math.cos(angle) + rng.uniform(-jitter, jitter)
        y = r * math.sin(angle) + rng.uniform(-jitter, jitter)
        pts.append((x, y))
    return pts


def main() -> None:
    if not os.path.exists(SRC):
        print(f"ERROR: source not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    for csv_name, (lo, hi) in BLOCKS:
        block = read_block(SRC, lo, hi)
        pts = extract_pairs(block)
        out = os.path.join(HERE, csv_name)
        write_csv(out, pts)
        print(f"  {csv_name:<32s} {len(pts):>5d} points")

    star = generate_star()
    out = os.path.join(HERE, "star_8_tips.csv")
    write_csv(out, star)
    print(f"  {'star_8_tips.csv':<32s} {len(star):>5d} points (procedural, seed=42)")


if __name__ == "__main__":
    main()
