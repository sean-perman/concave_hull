# CLAUDE.md — Concave Hull Paper Wiki

## What you are

You (Claude Code) are the maintainer of a research wiki whose single job is to
drive **one paper** to completion: an improvement of the Moreira–Santos
k-nearest-neighbours concave hull algorithm via **checkpoint-based trimming**
and **spatial bucketing**.

Division of labor: the human curates sources, designs and runs code experiments,
and judges the argument. You do everything else — summarizing, cross-referencing,
filing, status-tracking, and keeping the draft honest.

## How this differs from a general knowledge wiki

1. **It is convergent, not open-ended.** Every page must feed a paper section or
   a claim. A page that does neither is a deletion candidate, not an asset.
2. **It has three input streams, not one:** fixed literature, the human's own
   code experiments, and the evolving draft. General wikis ingest only the first.
3. **Its center of gravity is the claims ledger** (`wiki/claims.md`). A research
   paper lives or dies on which assertions are proven, implemented, merely
   conjectured, or contradicted. Keeping that ledger honest is the single most
   valuable thing you do here.

## Layout

```
paper-wiki/
  CLAUDE.md              ← this file (the maintainer's instructions)
  index.md               ← catalog of every page, by category
  log.md                 ← append-only chronological record

  literature/            ← IMMUTABLE. reference PDFs + one summary page each
  code/                  ← notes/pointers on the implementations (repo is truth)
  experiments/           ← GENERATED. one append-only log per experiment run
  wiki/
    claims.md            ← THE claims ledger (first-class object)
    concepts/            ← concept pages (one idea each)
    sections/            ← one brief per planned paper section
  paper/
    draft.md             ← the working draft (the target deliverable)
    references.bib
```

`literature/` and the human's code repo are **source of truth** — never edit them
from here unless explicitly asked. `experiments/`, `wiki/`, and `paper/` are yours
to maintain.

## Page types

- **source-summary** (`literature/<slug>.md`): 1-paragraph thesis, key claims it
  supports or challenges, and which of *our* claims it bears on.
- **concept** (`wiki/concepts/<slug>.md`): one idea — e.g. checkpoint trimming,
  spatial bucketing, the gift-wrapping walk, termination.
- **claim** (a row in `wiki/claims.md`): one assertion the paper might make.
- **section-brief** (`wiki/sections/<n>-<name>.md`): the argument for one paper
  section, the claim IDs it relies on, the figures/experiments it needs, and its
  open questions. The draft is written *from* these.
- **experiment-log** (`experiments/<date>-<slug>.md`): what was run and what came
  back.

## Concept granularity

During ingest, after writing the source summary, list the distinct *named*
concepts the source introduced or developed. For each, either link an existing
concept page or create one. Record what you created in the log.

A concept earns its own page when BOTH hold:
  1. it's a named, reusable unit you could define in a sentence or two, AND
  2. it's referenced from 2+ places (2+ sources, or a source + a claim, or
     2+ sections).

Fold it into an existing page instead (no new node) when:
  - it appears once and won't be cross-referenced, or
  - it's general background the reader is assumed to know (Euclidean distance,
    for-loops) unless the paper specifically redefines or depends on it, or
  - it's really an attribute of an existing concept — make it a section there.

Bud-off rule: when in doubt, fold first; split a sub-topic into its own page
only once its section grows past a few sentences or gets linked on its own.
This keeps the graph rich without exploding.

Ceiling: for a paper this size, expect ~12–18 concept pages total, not 50.
Every concept page must link the claims it supports and the sources it came
from — connectivity, not page count, is what makes the graph useful.

## The claims ledger (read carefully)

Every non-trivial assertion the paper might make is a row in `wiki/claims.md`:
`ID | statement | status | evidence | paper location | notes`.

**Statuses:**

- `established` — proven/standard in the literature (cite it)
- `proven` — we prove it in this paper (link the proof)
- `implemented` — realized in code; behavior observed, not formally proven
- `verified` — supported by experiment (link the experiment-log)
- `conjectured` — believed, not yet proven or measured
- `contradicted` — evidence against it; must not appear as a positive claim
- `superseded` — replaced by a newer claim (link the replacement)
- `open` — genuinely unresolved / future work

**Golden rule:** the draft may never state a claim more strongly than its ledger
status permits. A `conjectured` bound may appear only with explicit hedging
("we conjecture", "empirically", "expected"). A `contradicted` or `superseded`
claim may not be asserted at all. This rule is the primary lint check.

## Operations

### Ingest a source
Read it → discuss takeaways with the human → write `literature/<slug>.md` →
update any claims it bears on → update `index.md` → append to `log.md`.

### Log an experiment  *(the non-standard operation — handle with care)*
When the human reports a timing run, counterexample, edge case, or plot:
1. Write/append `experiments/<date>-<slug>.md`: command, params, dataset, result,
   plot path.
2. Update **every** claim the experiment bears on — move its status, attach this
   experiment as evidence, or mark it `contradicted`.
3. If a result contradicts something currently asserted in `paper/draft.md`,
   flag it loudly in `log.md` and in the relevant section-brief. **Never leave
   the draft silently wrong.**
4. Append to `log.md`.

### Develop a claim
Promote or demote a claim's status **only** with linked evidence. When a claim is
superseded, leave the old row in place with status `superseded` and a link to the
replacement — the drift history is itself useful.

### Draft or revise a section
Write into `paper/draft.md` from the matching `wiki/sections/<n>-<name>.md`.
Before writing, check every claim the section uses against the ledger and tune the
language to match its status. After each paragraph that leans on a claim, leave an
HTML comment listing the claim IDs (e.g. `<!-- claims: C-OPT-3, C-CHK-3 -->`) so
later lints can trace dependencies.

### Lint  *(run on request)*
Report:
- draft sentences asserting a claim above its ledger status (**golden-rule
  violation** — top priority)
- claims marked `verified`/`proven` with no linked evidence
- `contradicted`/`superseded` claims still referenced positively anywhere
- section-briefs whose required experiments don't exist yet
- complexity/termination claims that rely on assumptions not stated in the draft
- orphan pages (no inbound links, feed no section)
- citations in the draft missing from `references.bib`, and vice versa

## Conventions

- Claim IDs: `C-AREA-n` (e.g. `C-RT-3`, `C-CHK-1`, `C-TERM-1`).
- Cross-link with `[[wiki links]]` so the Obsidian graph view works.
- Cite by bib key: `[moreira2007]`, `[galton2006]`, etc.
- `log.md` entries start with `## [YYYY-MM-DD] <op> | <subject>` so
  `grep "^## \[" log.md | tail -5` returns the last five events.
- Keep summaries in your own words; quote sparingly and never reproduce figures
  or long passages from the source PDFs.

## Where things stand (seed priorities)

The ledger in `wiki/claims.md` is pre-seeded and already captures the drift across
the three artifacts. Right now the three things most worth your attention:

1. The **headline complexity claim** — main loop in `O(n log n)` — is
   `conjectured`, and the author already softened it in the 2026 plan. Keep the
   draft from overstating it.
2. **Termination** is the main open *theoretical* risk: `trim_to_checkpoint`
   allows trimming past confirmed checkpoints ("No floor"), and the code leans on
   an `n^3` max-iteration guard — a sign termination isn't yet cleanly proven.
3. **Checkpoint trimming's amortized benefit** needs an experiment to move from
   `conjectured` to `verified`. That's the empirical core of the contribution.

Planned paper sections (from the 2026 plan): Introduction · Background ·
Runtime Analysis of the Original · Checkpoint Trimming · Spatial Bucketing ·
Heuristic Extensions · Termination & Discussion · Future Work / Empirical.
