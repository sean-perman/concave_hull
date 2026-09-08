# Non-Monotone Effects of k

**Type:** concept · **Sources:** [[draft]] §2.2.3 (role of k), §k-nonmonotone
(counterexample section)

## Definition

The informal claim that increasing $k$ always produces a smoother or less concave
hull is **false**. A larger $k$ broadens the candidate set at each step, which can
change the *order* of the walk and the set of points still available later in ways
that produce a *more* concave hull.

## The area ratio (concavity measure)

To compare hulls across different $k$, the draft uses:

$$\rho(H) = \frac{\operatorname{area}(H)}{\operatorname{area}(\operatorname{conv}(S))}$$

with $0 < \rho(H) \leq 1$; $\rho = 1$ exactly when $H$ is the convex hull. A
*drop* in $\rho$ as $k$ increases means the hull became more concave — a violation
of monotonicity.

## The 8-point counterexample

Eight points in $[0,1]^2$ (Table in §k-nonmonotone) with
$\operatorname{area}(\operatorname{conv}(S)) = 0.32411$:

| k | area(H) | ρ | outside |
|---|---------|---|---------|
| 5 | 0.32223 | 0.9942 | 0 |
| 6 | 0.26187 | 0.8079 | 0 |

Both hulls enclose all 8 points (verified computationally via `monotonicity_test.py`),
ruling out the degenerate case where a larger $k$ causes early closure and point
leakage. The drop of 0.19 in $\rho$ is the counterexample: one valid all-enclosing
hull is strictly more concave at $k=6$ than at $k=5$.

**Mechanism:** at $k=5$ the walk cannot immediately see the far convex-hull corner
$(0.996, 0.950)$, so it routes through a nearby outer point first. At $k=6$ that
corner enters the candidate set early and wins the angular test, causing a jump that
forces the walk inward through $(0.507, 0.637)$, creating a deeper notch. The key
insight is that a larger $k$ changes *which points remain available later*, not just
how much smoothing is applied to the same walk.

## Implication for the paper

$k$ is a heuristic smoothness control, not a parameter with a guaranteed monotone
effect. The background section (§2.2.3) now says the hull "tends to be smoother"
at larger $k$ rather than "becomes smoother." The dedicated counterexample section
proves the stronger statement: monotonicity can fail even for small, all-enclosing
hulls.

This shape result alone did not disprove the validity predicate required by binary
search because both neighbouring hulls succeed. That separate question is now
resolved by [[k-validity-nonmonotone]] / C-MONO-2: a six-point set produces the
validity sequence true at $k=3$, false at $k=4$, and true at $k=5$.

## Claims it supports

- **C-MONO-1** — $k$ does not monotonically control concavity (*proven* by the
  8-point counterexample). See [[claims]].

## See also

[[gift-wrapping-walk]] · [[k-growth-strategy]] · [[k-validity-nonmonotone]] · [[claims]]
