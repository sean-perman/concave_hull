# Termination Argument

**Type:** concept (main open theoretical risk) · **Sources:** [[draft]] §4 *(stub —
heading only)*, [sean2026] §3

## Definition

The argument that the [[checkpoint-trimming]] variant always halts. Intended shape:
the point set is finite, and every trim **strictly increases the per-region *k***,
so a region cannot be retried at the same *k* forever — therefore no infinite
cycling.

## Why it's the risk

Trimming can move the walk *backward*. For the no-cycle argument to hold, the
*k*-increase must dominate any backward progress. The danger is **"No floor"**: if a
trim can pass a previously confirmed checkpoint, progress is not obviously monotone
and the simple finiteness argument breaks.

## Unresolved tension (resolve before writing §4)

- **Code/ledger note:** `trim_to_checkpoint` allows trimming *past* confirmed
  checkpoints ("No floor") — hardest case to prove.
- **Draft prose ([[draft]] §5.2):** says trim goes back to "the most recent
  checkpoint" / "the current checkpoint" — implies a **floor**, which would make the
  monotonicity argument easy.
  These contradict; pin down which is the real behavior.
- **The `n³` guard (C-TERM-2):** a `max_iterations = n³` backstop exists in code. A
  safety net is a *smell* — its presence suggests termination isn't yet cleanly
  proven. Either prove C-TERM-1 and frame the guard as defensive, or report it as a
  current limitation.

## Claims it supports

- **C-TERM-1** — always terminates (*conjectured*; the proof goes here).
- **C-TERM-2** — `n³` max-iteration guard (*implemented*).
See [[claims]].

## See also

[[checkpoint-trimming]] · [[gift-wrapping-walk]]
