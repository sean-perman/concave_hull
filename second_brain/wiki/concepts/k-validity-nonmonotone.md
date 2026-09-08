# Nonmonotone Validity in k

**Type:** concept + computational counterexample  
**Evidence:** [[2026-08-31-k-validity-nonmonotone]]  
**Claims:** C-MONO-2, C-KG-4

## Definition

Let $V(k)$ mean that a fixed-$k$ Moreira--Santos attempt closes without a dead
end and its final simple polygon encloses every input point. Binary search for
the smallest valid $k$ requires $V(k)$ to be monotone: after its first `true`, it
must remain `true` for every larger $k$.

## Counterexample

The six-point integer set in
`validity_monotonicity/counterexample_points.csv` has

$$
V(3)=\mathrm{true},\qquad
V(4)=\mathrm{false},\qquad
V(5)=\mathrm{true}.
$$

At $k=4$, the greedy walk takes the partial route $F\to B\to A$ and then every
available continuation intersects the existing edge $FB$. The neighbouring
values $k=3$ and $k=5$ both close and enclose all six points. The set has no
collinear triple and no equal-distance k-NN ties.

## Consequences

- A smallest valid $k$ still exists because the finite all-candidates endpoint
  is valid; what fails is the interval property that every larger $k$ is valid.
- Standard binary search for the smallest valid $k$ is unsound in general.
- Exponential/geometric forward growth does not need monotone validity for
  termination, provided it is capped at and explicitly tests the all-candidates
  endpoint.
- This result is distinct from [[k-nonmonotone]], which shows that the *shape*
  or area ratio can reverse even when both neighbouring $k$ values are valid.

## Paper placement

Integrated into the active short paper on 2026-08-31 as Section 6.2, inside the
renamed Non-Monotone Effects of $k$ section. The paper gives the exact coordinates
and walks, includes the three-panel figure, and connects the result to the O(n³)
geometric-growth corollary in Section 3. Ordinary binary search is explicitly
ruled out as a general minimum-valid-k strategy.

## See also

[[k-growth-strategy]] · [[k-nonmonotone]] · [[gift-wrapping-walk]] ·
[[termination-argument]]
