# GRIVAPP 2027 Submission Target

**Status:** target venue and short-paper scope plan  
**Decision date:** 2026-07-29; scope revised 2026-08-27  
**Target:** Regular Paper, first submission round  
**Primary deadline:** 2026-09-15 (AOE)  
**Fallback round:** 2026-10-22  
**Conference:** 2027-02-26 through 2027-02-28

## Conference lineage

The original Moreira--Santos paper appeared at the **Second International
Conference on Computer Graphics Theory and Applications (GRAPP 2007)**:

> A. Moreira and M. Y. Santos, "Concave Hull: A k-Nearest Neighbours Approach
> for the Computation of the Region Occupied by a Set of Points," GRAPP 2007,
> Barcelona, Spain, pp. 61--68.

- Original paper: <https://www.scitepress.org/papers/2007/20808/20808.pdf>
- GRAPP 2007 site: <https://grapp.scitevents.org/GRAPP2007/>

Starting in 2026, GRAPP, IVAPP, and HUCAPP were merged into **GRIVAPP**, the
International Conference on Computer Graphics, Interaction and Visualization
Theory and Applications. GRIVAPP is therefore the direct organizational
successor and the intended venue for this paper.

The venue direction also follows Mario Lopez's earlier suggestion that the work
could be considered for publication in the same forum used by the original
authors. See [[advisor-guidance]].

- Official lineage announcement:
  <https://visigrapp.scitevents.org/home.aspx>
- GRIVAPP 2027:
  <https://grivapp.scitevents.org/?y=2027>

## Why the paper fits

The closest GRIVAPP 2027 area is **Modeling, Rendering, Animation and
Simulation**, especially "Mesh and Point-Based Representations and Processing"
and related geometry/modeling work. The paper is also unusually well positioned
historically: it supplies analysis and experimental improvements for an
algorithm first published in the predecessor conference.

- Call for papers and topics:
  <https://grivapp.scitevents.org/CallForPapers.aspx>

## Submission requirements

- Submit a Regular Paper through PRIMORIS by **2026-09-15**.
- Use the official SCITEPRESS template.
- Submit an English, double-blind PDF with author names, personal details, and
  acknowledgements removed.
- Regular-paper submissions must contain 10,000--50,000 characters excluding
  whitespace, including references, tables, figures, and appendices.
- Accepted Regular Papers may become a 12-page Full Paper or an 8-page Short
  Paper. Up to four paid extra pages are possible, but the plan must not rely on
  them.
- The conference requires disclosure of AI-generated text and citation of the
  AI system in affected sections. The final disclosure must follow the venue's
  instructions without compromising the anonymous review copy.

- Official dates:
  <https://grivapp.scitevents.org/CallForPapers.aspx>
- Guidelines:
  <https://grivapp.scitevents.org/Guidelines.aspx>

## Author constraints

The author has limited time before submission, and the draft is already long.
As of 2026-07-29, `concave_hull_paper.tex` is approximately 7,114 words and
41,622 non-whitespace LaTeX characters. That character count includes LaTeX
commands and is not identical to the conference's count, but it is close enough
to make length a real risk.

**Working rule: do not add a new experiment, proof, implementation, or section
unless it replaces material or is necessary to keep an existing claim honest.**

The goal is a coherent minimum viable submission, not completion of every open
research direction.

As of 2026-08-27, the submission source is
`scitepress_paper/short_paper_draft.tex`. After insertion of the approved
abstract, it compiles to 7 A4 pages and contains approximately 21,627 rendered
non-whitespace characters (4,221 rendered words). This leaves room for one
compact results table
and final framing while remaining shaped for an 8-page Short Paper if accepted
in that form. The full SCITEPRESS draft remains available as historical source,
but is no longer the active submission manuscript.

## Minimum viable paper

The submission should preserve this core story:

1. The original Moreira--Santos restart algorithm has an unanalyzed structural
   cost; this paper supplies a worst-case upper-bound analysis and shows that
   geometric growth changes the restart bound from O(n^4) to O(n^3). The factorial
   experiment verifies the corresponding practical runtime--shape tradeoff.
2. Spatial bucketing is an exact candidate-validation optimization and produces
   a measured 1.40--3.41x paired median practical speedup in the integrated factorial
   while producing the same valid hulls as naive intersection checking. It reduces
   calls to the exact intersection predicate by 6.9--188.6x across the tested datasets.
3. The k-nonmonotonicity counterexample is a clean proven result: increasing k
   can lower the hull/convex-hull area ratio even when both hulls enclose every
   input point. A 2026-08-31 six-point counterexample strengthens the section by
   showing that validity itself can follow true→false→true, ruling out ordinary
   binary search for the minimum valid k.

**Scope addition integrated (2026-08-31):** the six-point validity counterexample
is now Section 6.2 of the active draft, inside the renamed Non-Monotone Effects of
$k$ section. It retains the eight-point shape counterexample while adding compact
integer coordinates, exact walks, the ready three-panel figure, and the binary-search
consequence from [[2026-08-31-k-validity-nonmonotone]]. Section 3.2 also includes
the O(n³) geometric-growth corollary. The compiled paper remains seven A4 pages.

**Geometric-growth experiment completed and integrated (2026-09-01):**
`concave_hull_experiment/growth_factorial_benchmark.py` runs the controlled 2×2
comparison needed by the current abstract: linear/geometric growth crossed with
naive/bucketed intersection checking. The schedule was first corrected to use
`ceil(rk)` and to test the explicit `n-1` cap promised by the proof. Thirty tests pass.
The full run completed 110 paired inputs and 440 timed observations; every output was
valid and all 220 schedule-matched naive/bucketed comparisons were identical. The
command was:

```
python -m concave_hull_experiment.growth_factorial_benchmark --rate 2
```

The paper run uses 10 paired trials, unit-disk and eight-tip-star inputs from
1k through 50k points, and U.S. cities, gray wolf, and coast redwood. World capitals
is excluded by default because of the raw-longitude antimeridian limitation. Outputs
include raw and summary CSVs, metadata with source hash and environment, and a LaTeX
table. Paper interpretation must keep two comparisons distinct: naive and bucketed
must return identical hulls within a growth schedule; geometric and linear growth may
return different valid hulls and therefore require final-k and area-ratio reporting.
Geometric growth produced 1.36–44.57× paired median speedups with naive checking,
reduced attempts by 1.5–16.3×, and matched the linear hull in only 11/110 inputs. The
combined configuration was 1.89–147.94× faster than the original baseline. These
results and the generated table are now in the active manuscript, which compiles to
8 A4 pages. See [[2026-09-01-geometric-growth-factorial]].

**Scope decision (2026-08-27): checkpoint trimming is no longer a main-body
contribution of the submission.** Its implementation, termination argument,
k-scope experiments, and excluded-points limitation remain valid project history
but are deferred to Future Work. The short paper should contain at most one
compact paragraph explaining local rollback as a proposed next direction.

## Required before submission

These are paper-integrity or venue-compliance tasks, not optional research:

- Convert to the official SCITEPRESS template and measure the resulting page
  and character counts.
- Produce an anonymized review copy.
- Audit every strong claim against `wiki/claims.md`, especially C-RT-6,
  C-OPT-2, C-MONO-1, C-MONO-2, and the original-algorithm termination claim.
- State the O(n^4) result as a worst-case **upper bound** unless tightness is
  actually demonstrated.
- State the computational model used by the runtime proof; do not attribute an
  undocumented spatial index to the original Mathematica implementation.
- Put the original-algorithm termination argument in the body, not only the
  abstract, and distinguish it from the deferred checkpoint termination claim.
- Verify citations, figure legibility, table values, and reproducibility details.
- Obtain an advisor review before the final submission.

## Explicitly eligible for Future Work

Unless a small, clearly bounded fix becomes available, the following may be
deferred rather than allowed to block submission:

- checkpoint trimming as a whole, including local/global k and checkpoint-mode
  comparisons;
- checkpoint-aware excluded-points recovery;
- a tighter or amortized complexity analysis;
- proof of tightness for the O(n^4) upper bound;
- boundary-fidelity metrics and the global-k/local-k quality trade-off;
- broader datasets, density sweeps, separated clusters, and degenerate cases;
- parallel region construction;
- richer candidate-selection heuristics;
- geometric k-growth experiments (the O(n³) upper bound itself is already proved
  by C-KG-3 and does not require an experiment);
- hand-built grid k-NN work not used by the experiment harness.

Future Work must remain compact. It should introduce checkpoint trimming in two
or three sentences, identify correctness-preserving excluded-points recovery as
the key unresolved requirement, and group the remaining ideas into one short
paragraph rather than assuming the reader saw the removed checkpoint section.

## Cut order if the paper is too long

Cut or compress in this order:

1. Remove the empty Supplementary Material placeholder.
2. Compress Future Work from separate mini-sections into one or two paragraphs.
3. Remove repeated motivation and repeated explanations of restart cost.
4. Compress generic convex-hull/concave-hull background.
5. Shorten speculative guidance about checkpoint trimming, initial k, faster
   k-growth, parallelism, and richer heuristics.
6. Reduce secondary examples or figures that do not support a numbered claim.
7. Only then consider compressing the k-nonmonotonicity section; preserve the
   counterexample result if it can be stated compactly.

Do not cut the spatial-bucketing experiment table, the core algorithm
description, or the qualifications on the upper bounds merely to make the
results appear cleaner.

## Low-overhead timeline

- **By 2026-08-04:** freeze the contribution scope and decide that uncompleted
  research defaults to Future Work.
- **By 2026-08-11:** complete the claim/evidence audit; narrow any unsupported
  statements.
- **By 2026-08-18:** move the paper into the SCITEPRESS template and make the
  first length cuts.
- **By 2026-08-25:** finish the methods/results/limitations pass and citation
  cleanup.
- **By 2026-09-01:** obtain advisor feedback on one submission-shaped draft.
- **By 2026-09-08:** revise, anonymize, and run the final evidence/format lint.
- **2026-09-09 through 2026-09-14:** submission-system and PDF checks only;
  avoid new research unless it fixes a fatal correctness problem.
- **2026-09-15:** submit the Regular Paper.

If the first round cannot be reached honestly, use **2026-10-22** as the fallback
instead of filling the paper with rushed or unsupported claims.
