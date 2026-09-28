# The block book

A working reference for the payoff-graph blocks, written for someone who is **not**
a veteran quant developer. It answers one question per block: *how do I know this
piece is right?*

It is deliberately small and deliberately honest. Only blocks that have actually
been built and tested get a page. Everything else is listed in
[registry/blocks.yaml](registry/blocks.yaml) with an honest status, so you can see
what is not done instead of guessing.

## Start here

| If you want to | Read |
|---|---|
| understand what a barrier, a fixing, a worst-of basket, or PV means | [00-glossary.md](00-glossary.md) |
| understand how a block gets built, tested, and evidenced | [01-how-a-block-is-built.md](01-how-a-block-is-built.md) |
| understand why this repo has five implementations of one payoff | [02-why-there-are-lanes.md](02-why-there-are-lanes.md) |
| see which lane implements a given block, and where they disagree | [03-where-each-block-lives.md](03-where-each-block-lives.md) |
| see the first block, end to end | [blocks/coupon-strip.md](blocks/coupon-strip.md) |
| know which blocks exist and which are trustworthy | [registry/blocks.yaml](registry/blocks.yaml) |

## The idea in one paragraph

A structured product is not one piece of pricing code. It is an assembly of small
pieces, each of which answers one question. This codebase calls those pieces
**blocks**. A block is worth having only if it is small enough that its
correctness can be settled by reading a sentence and running a test — no
simulation, no market data, no server. That is the whole standard this book
applies.

## The traceability chain

Every block answers these six questions in the same order. A block page fills in
this table, and every cell is a file you can open.

| # | Stage | The question | Where the answer lives |
|---|---|---|---|
| 1 | Concept | What is this, in plain words? | the block page, no jargon |
| 2 | Specification | What would a term sheet say about it? | the block page, one sentence |
| 3 | Registry | What kind of thing is it, what goes in and out? | `registry/blocks.yaml` |
| 4 | Kernel | Which function computes it? | `file:line` in the C++ |
| 5 | Test | What asserts it, and against what? | `cpp/tests/*.cpp` |
| 6 | Evidence | Can its real inputs be traced, and was its state complete? | the block page |

Stages 1–2 are for you. Stage 3 is the machine-readable version of 1–2. Stages
4–5 are for the code. **Stage 6 is the one that is usually missing, and it is the
one that decides whether a number is trustworthy.**

## Why stage 6 is separate

"There are three different questions hiding inside "is this block right?", and
they fail independently:

| Question | Answered by | Can a machine settle it? |
|---|---|---|
| **Does the code do what the specification says?** | the test | yes — and this book does it first |
| **Are the numbers fed into it right for a real deal?** | tracing a value to a term sheet or a booking system | **no** |
| **Was the engine handed a complete state, or a reconstructed one?** | comparing the evaluation date to the deal snapshot's own timestamps, and checking whether the fields the formula needs are populated at all | **no** |

The third question is the newest. It is here because `coupon_strip` ran into a
case the first two cannot express: correct arithmetic, a fully traced rate, and a
**source file that contains two different as-of dates**. Neither "does it match the
spec" nor "can I trace the inputs" can report that. It is recorded as a **proposed**
third axis and is not yet ratified — see the note at the top of
`registry/blocks.yaml`.

Two numbers, and they are not the same gap:

| gap | from | to | days |
|---|---|---|---|
| last fixing → pricing date | 2026-08-21 | 2026-09-07 | 17 |
| deal snapshot → pricing date | 2026-08-23 | 2026-09-07 | 15 |

The second is the defect. Four timestamps in the payload agree on 2026-08-21 or
2026-08-23, and two agree on 2026-09-07, and the engine mixes them. The first is
just the passage of time.

`coupon_strip` is the worked example of the whole distinction, and it is more
instructive than it was meant to be. Reading the real term sheet against the kernel
produced six findings in a single block:

1. **Half the block's specification is not in this contract at all.** The
   `carried_memory` term is live, and the contract scopes both of its counts to a
   single period. This was first recorded as `ambiguous_in_source` — "the source does
   not say which reading is right". **That label has been withdrawn.** Three
   independent sources now agree the carry is absent, and the platform forbids it
   for this product configuration, so the label is **`unsupported`**. A downgrade is
   the finding; so is the fact that it needed three sources to become a downgrade
   rather than a guess.
2. **The word "Memory" means two unrelated things.** The contract's memory is a
   per-asset *termination latch* on the call price. The engine's is an unpaid-coupon
   *carry*. Same word, different mechanism, and a reader who sees both names in one
   struct will reasonably assume they are variants of each other. Neither is wrong;
   together they are a trap.
3. **The product is a daily-callable note, and both lanes price it as un-callable.**
   One because the graph disables the call, one because
   `np.where(call_date <= end_step, amount, amount)` throws away a correctly computed
   call schedule. Opposite wrong answers, which is why no parity test sees either.
4. **Both legacy lanes divide by the wrong number.** They compute `(N2 - N1) / N2`
   where the platform's formula is `N1 / N2` — and the payload's `N1` is days
   *elapsed*, so neither expression is right. The past books at zero, the future
   books at certainty, and the 10% floor is never tested on a single simulated path.
5. **The fixture's `accruRate` is right and the compiled graph's `coupon.rate` is
   not.** Nine `0.00713` values should be `0.009642`. The right number is sitting in
   the same payload, unread.
6. **The term sheet requires a rounding rule twice, explicitly, and neither lane
   rounds.** `Round(denomination × rate × fraction, 2) × (notional / denomination)`,
   with the platform's own formula now known. Cheapest remaining conformance win.

Ten tests pass throughout. That is the point of the example rather than an
embarrassment of it: **the tests were never capable of catching any of the six,
and no test in the repository is.** All of it is in
[blocks/coupon-strip.md](blocks/coupon-strip.md) section 7, and the architecture
reason it survived is in [02-why-there-are-lanes.md](02-why-there-are-lanes.md).

## The platform's own documentation, checked against ours

The three authoritative sources in this repository do not agree with each other
about anything, so nothing here rests on one of them alone:

| rank | source | what it settles |
|---|---|---|
| 1 | the term sheet, 13 pages | what the contract promises |
| 2 | `modules/fina-skills/refs/MurexPlaybook/` | what the platform is built to do |
| 3 | legacy code and payloads | what the thing being replaced actually did |

The playbook earns rank 2 because it is unusually disciplined: it declares its own
gaps rather than papering over them, and where it declares one, the term sheet often
resolves it. Four of the six findings above changed status because the playbook
answered a question the term sheet did not ask:

- the accrual factor is `N1 / N2` in **twelve** files, not the complement the lanes
  compute;
- a coupon carry is a real product, gated on a separate Coupon Barrier, and
  **mutually exclusive with Global KO** — which this deal has;
- the physical-delivery quantity formula the playbook admits it cannot supply is in
  the term sheet, in the form `Nominal / Exercise Price`;
- simultaneity of memory hits, which the playbook raises as open at
  `raki-plus.md:224`, is answered at `raki-plus.md:213` in the same document:
  *"Never overwrite a prior memory-hit or KI state with a later non-hit unless
  product semantics explicitly provide for reset, which the source does not."*

It also supplied the one line that **falsified a claim this book had been carrying**:
`fina_risk_cpp.cpp` was recorded as "the one deliberate, documented departure in the
whole repository", and the playbook forbids that reading in as many words. The
label has been withdrawn, the code has been changed, and the comment that made the
claim has been deleted; see
[03-where-each-block-lives.md](03-where-each-block-lives.md).


## Two rules this book does not bend

**1. A test's expected values are derived by hand from the specification, never
by running the code and writing down what it printed.** A test that copies the
implementation's output into an assertion is a tautology: it passes forever and
catches nothing. This is the single most important habit in the book, and it is
the one that makes the tests worth reading.

**2. No pinned number may originate from an AI.** Every expected value traces to
a term sheet, a booking system, or a published reference. If a number cannot be
traced to one of those, the block's evidence status stays `unresolved` and the
question is written down for a human. A fixture invented by a machine is worse
than no fixture, because it acquires the authority of a test.

## Where the work stands

Stage 1 of the sequence in
[02-why-there-are-lanes.md](02-why-there-are-lanes.md) is **done, 10 of 11 items**,
and every one of the ten has a test that was shown to fail with the fix reverted.
The one left alone is the `coupon_quote_scale` default, which needs a human who
knows how the legacy system booked the coupon leg.

The first finding of the term-sheet and playbook review below has since been fixed
too, taking the repository to **eleven fixes, eleven tests**, all with the same
revert-and-fail evidence. It is the only one of the eleven that changed a rule
rather than a unit, and it is also the only one whose fix is **incomplete on
purpose**: it corrected one of the three places the global call test is written in
`fina_risk_cpp.cpp` and left the other two, because the fix there needs a record
schema that belongs to someone else. That is written up rather than smoothed over.

Two of the fixes changed a PV, and both were in the same direction — notes were
being priced as if features they did not have were switched off:

| | before | after |
|---|---|---|
| coupon leg, `termsheet1`, legacy lane | 0.509887 | **0.316356** |
| global call barrier, canonical lane | 1.00 (`float(True)`) | **1.10** |

**Both of those figures are now provisional.** The coupon-leg number was produced
by a fix that is correct, applied to a source file whose deal block is a different
snapshot from its pricing date. The number is right about the code and unknown about
the data. Correcting the accrual factor (finding 4 above) moves the same leg to
0.353528, +11.8%, and the total PV from 1.279426 to 1.316598, +2.9% — from a
*different* defect, in the same direction, and also not a fix.

### A term-sheet and playbook review, after stage 1

Ten new findings came out of reading the term sheet against the MurexPlaybook
line by line. Two are the highest-confidence fixes available in this repository,
and neither is a matter of judgement:

| # | finding | axis | fixable now? |
|---|---|---|---|
| 1 | `fina_risk_cpp.cpp` refuses to credit a latched asset, so the call can be missed forever | spec | **fixed, 1 site of 3** — see below |
| 2 | `memory_carry` is in the graph, the kernel, the fixture and both lanes, and is in no contract | spec + deal | **yes** — the removal is the evidence |
| 3 | `pricing.py:348` is a no-op: two variables holding the same expression | code | yes |
| 4 | the 0.01 rounding the term sheet demands twice | spec | yes, both lanes |
| 5 | `fixCoupon` is an *additive* coupon, not the Fixed/Variable flag | deal | no — a gap in the legacy system too |
| 6 | the accrual factor is the complement of the documented one | spec | **no** — blocked on data |
| 7 | the fixture mixes two as-of dates | lifecycle | **no** — blocked on the extractor |
| 8 | `N2[1] = 1` where the term sheet says CP1 is 21 days | deal | no — ambiguous, see below |
| 9 | the basket is capped at 2 by us, 6 by the platform | spec | yes, when wanted |
| 10 | `MaturBarrier ≥ KIBarrier` is load-bearing and asserted nowhere | spec | yes — a test |

Findings 6 and 7 are the important ones, because they are the two that **cannot**
be fixed by writing careful code, and both are the kind of problem that looks like
a code problem. Finding 6's root cause is that the payload carries no in-range day
count at all, so the question is not which expression to type — it is what the
legacy system populates. Finding 7's owner is the extraction job. Both are written
down and both are blocking; neither is guessed at.

#### Finding 1, and why the fix is one third of a fix

The Daily Callable Condition is a **per-asset latch**: the term sheet terminates the
note when *each* asset has **become** a Memorised Reference Asset, and "become" is
a status that persists. The playbook says the same in its own words — the product
"remembers which underlyings have already hit their barriers (tracked by per-stock
'locked' flags and dates in the flex block)" — and the deal file carries exactly
that: `KIKOSelect.GKOLocked = [true, false]`, one flag per asset with a date beside
it. A lane that never reads that field has no latch, and a joint test on a single
fixing is not a latch.

That joint test was in three places in `fina_risk_cpp.cpp`. One is now a sticky
per-asset latch seeded from `GKOLocked`, and the comment claiming the old reading was
"conservative" is gone — it was not conservative, it was the expensive side, since
a missed call keeps the note alive and the coupon leg running.

**The other two are untouched, and the reason is the finding.** `run_cpp_parity`
(`:884-895`) and `price_daily_compact` (`:1084-1090`) take the block from a *compact
instrument record* — `refs`, `strike`, `ki`, `call`, `expiry`, `notional`,
`quote_scale` — that has no latch field, and the record schema belongs to the
corpus producer, not to this file. So the C++ lane now contains both readings of the
contract, in one translation unit, and `price_daily_compact` is the lane
`termsheet1` is actually priced through. Adding the read without the schema field
would have been inert on every real deal while looking fixed in the diff, so the two
sites are recorded as open with their line numbers and the reason.

The test is `cpp/tests/global_ko_latch_test.cpp`, registered as **`lane/global_ko_latch`
and deliberately not named `block/`**. The kernel for this block is `resolve_ko`,
which is six lines long, correct, and **never called from this lane** — a block
test against it would pass today and prove nothing. The only way to test the defect
is to price a deal and look at the put, which means the test needs the JSON layer and
the pricing loop, the two things the `block/` tests are written to avoid. Naming it
`lane/` keeps that visible in `ctest` output instead of hiding a lane test among
block tests.

### Claims in this book that were wrong, and are corrected in place

Seven, each because something else contradicted it:

1. "the two NYSE calendars disagree on Memorial Day in 9 of 11 years" — the C++
   helper takes a *target weekday*, not "last working day". They agree.
2. "CI triggers on `native/**`, a directory that does not exist" — `native/`
   exists and is tracked; the trigger matched the packaging shell, not the source.
3. "`engine.cpp` prices the call as switched off" — it was switched **on**, at a
   100% barrier, which does not fire. Same boolean-as-a-level bug as `ko_enabled`
   in `fina-core/payoff.py`, reaching the production lane through the compiled
   graph, so the two lanes were wrong about the same feature in opposite ways.
4. the `coupon_quote_scale` three-way default disagreement is **not live** — the
   compiled graph always supplies the value explicitly, so every production lane
   uses 10.0. The facts were right, the framing implied a live bug.
5. "the `× 10` is a percent conversion" — it is a **ten-point price quotation**
   convention. The real defect is narrower and more embarrassing: only the coupon
   leg gets it.
6. **The global-KO reading in `fina_risk_cpp.cpp` is not "the one deliberate,
   documented departure in the whole repository".** The source comment explained that
   its reading was *conservative*; it was not — missing a call leaves the note alive and
   the coupon leg running, which is more liability, not less. And the playbook forbids
   the reading outright. The label was protecting a bug, the bug is now fixed, and
   the comment that made the claim has been deleted from the tree.
7. "`fixCoupon` might be the Fixed/Variable flag" — it is an additive coupon, in
   eleven files. The consequence is worse: the term sheet's Fixed/Variable
   *distinction* is not expressible in the platform's model at all.

Findings 6 and 7 are the reason this section exists in this shape. In both cases the
book had settled a question that was still open, using a source that had no
authority to settle it.

## Block index

| Block | Kernel | Test | Spec | Deal evidence | Lifecycle state | Page |
|---|---|---|---|---|---|---|
| `coupon_strip` | `period_rate` `coupon.hpp:15` | 10 cases, passing | **unsupported** | **partial** | **unresolved** | [link](blocks/coupon-strip.md) |
| `range_accrual` | `in_range` `coupon.hpp:9` | **blocked on data** | ok | **unresolved** | **unresolved** | — |
| `memory_carry` | `next_memory` `coupon.hpp:21` | not started | **unsupported** | **unsupported** | n/a | — |
| `knock_in_gate` | `update_knock_in` | not started | — | — | — | — |
| `down_and_in_put` | `terminal_option_payoff` | not started | — | — | — | — |
| `notional_return` | `funding_amount` | not started | — | — | — | — |
| `fixing_schedule` | `observation_on_or_before` | not started | — | — | — | — |
| `cash_settlement` | `settlement_for` | not started | — | — | — | — |
| `physical_delivery_settlement` | `settlement_for` *(shared)* | not started | **quantity formula found** | — | — | — |
| `global_ko_gate` | **none** — binds `resolve_ko`, a 6-line precedence switch that this lane never calls; 5 inlined formulations, and `fina_risk_cpp.cpp` now carries both the conformant one and the non-conformant one | `lane/global_ko_latch`, 7 cases, passing | **1 site of 3 conformant** | — | 2 sites blocked on a record schema | [link](03-where-each-block-lives.md) |
| `local_ko_gate` | **none** — same symbol; the node is now emitted when the deal has a real local call | blocked | — | — | — | [link](03-where-each-block-lives.md) |
| `worst_of_performance` | **none** — 19 inline sites, 6 lanes; a >2-name basket now refuses rather than truncating | blocked | ok | **defined by the term sheet** | — | [link](03-where-each-block-lives.md) |
| `payment_discount` | **none** — 5 lanes, 5 different rate sources; 2 of them now refuse an empty curve | blocked | — | — | — | [link](03-where-each-block-lives.md) |

Of the 13 catalogue blocks, 9 have a clean standalone kernel (sitting on 8 distinct
functions, because two settlement blocks share one) and **4 have none**.

The two KO gates used to be recorded as *"partial — maps to `resolve_ko`"*. That was
wrong in a way worth keeping: `resolve_ko` is a clean, correct, six-line function
that answers *"given two things fired, which counts?"* — not *"did a barrier
fire?"*, which is the block. **A declared binding is a claim about a block, and the
claim is only as good as the symbol it names.** An earlier version of this index
also said `worst_of_performance` was "inlined twice", which counted one file, and
that the two-name cap was "by construction" — implying the product cannot do better.
The playbook states the platform limit explicitly: **6 underlyings**, so the cap is
ours, and it is an implementation gap of at most two lines.

The four unblocked rows are where the catalogue stops describing the code, so they
are the four to read first. See
[01-how-a-block-is-built.md](01-how-a-block-is-built.md) for what a kernel is for,
and [03-where-each-block-lives.md](03-where-each-block-lives.md) for the
lane-by-lane matrix.

### The two rows that are worse than empty

A row with a dash says *not built*. Two rows here say something stronger.

**`memory_carry` is `unsupported` on both axes** — the first block to earn that. It
is not a block with a data problem. It is a correct implementation of a product
feature that this deal is documented as **excluded from**, sitting live in the
compiled graph, the kernel, both lanes, and 2000 of 2000 benchmark fixtures, 1333 of
which carry a feature combination the platform says cannot coexist. A dead flag on
2000 instruments looks like coverage and is not.

**`range_accrual` is `blocked_on_data`, and it is the block most worth arguing
about**, because it is the first one where the honest answer is a question rather
than a fix. Its output is a count of days in range. The payload does not contain
that count. It contains `N1`, which is identical to `fixingsDone` in every one of
the nine rows, so `N1` is days *elapsed*. Both legacy lanes then compute
`(N2 - N1) / N2` — the complement of the documented `N1 / N2` — which books the
three already-paid periods at **zero** and the five future periods at **certainty**,
and never tests the 10% floor on a single simulated path.

The tempting fix is to change the expression to `N1 / N2`. **That is equally
unfounded, because `N1` does not mean what the documentation says it means.** For
the three elapsed periods the right answer is a historical fact — the amount
actually paid on 2026-06-03, 2026-07-03 and 2026-08-05, 482.10 each, currently
valued at nothing. The record does not hold it. So the open question is *what does
the legacy system populate*, not *which line do I type*, and the block stays open
until someone answers it.

## Running the block tests

The block tests are C++ executables registered with CTest, one per block. They do
not need market data, a path cube, or a network connection.

```bash
cd modules/fina-risk
cmake -S cpp -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build -R block/ --output-on-failure
```

`ctest -R block/` runs only the block tests, which is the fast loop while you are
working on a block. `ctest` with no filter runs everything.

**These tests must never be compiled with `-ffast-math`.** A block test asserts
specified arithmetic and therefore compares to a tolerance; a compiler free to
reassociate `fixed + range * fraction` would move the last bits and turn a check
of the *specification* into a check of the *compiler*.

## Checking the book against the tree

Two scripts keep this book honest, and both have already earned their place.

```bash
# every quoted code block against the file and range its header names
python3 skills/fina-visual-builder/scripts/check_quotes.py

# links, anchors, table shape, registry coverage, and unsanitised names
python3 skills/fina-visual-builder/scripts/check_book.py
```

Run both from the `fina-skills` module root. `check_quotes.py` exits non-zero on a
drifted citation, so it is worth wiring into CI next to the CTest run.

`quote_check.py` is the one that matters. A line-number citation rots, the prose
around it does not, and an audit found 39 of 122 citations pointing at the wrong
line — including four addressed to an entirely different function. Every quoted
block now carries a `file:line-range` header and is verified verbatim; see
[01-how-a-block-is-built.md](01-how-a-block-is-built.md#how-this-book-cites-code-and-how-that-is-kept-true)
for the convention and for the four blocks that turned out to be paraphrases
dressed as quotations.

## Related

- [../../SKILL.md](../../SKILL.md) — the layer model and the 13-block design target
- [03-where-each-block-lives.md](03-where-each-block-lives.md) — the lane-by-lane
  matrix for the four blocks that have no kernel. Start here if you are trying to
  work out whether a number in a PV came from one place or five.
- [../ModelAndTradeLayer.md](../ModelAndTradeLayer.md) — the model and trade layers
