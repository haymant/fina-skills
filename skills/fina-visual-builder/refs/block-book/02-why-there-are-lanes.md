# Why there are five lanes, and what it costs

Read this after [01-how-a-block-is-built.md](01-how-a-block-is-built.md). It is not
about one block. It is about the shape of the repository, and it is the reason
[blocks/coupon-strip.md](blocks/coupon-strip.md) section 7 could report **two
opposite bugs about the same product feature at the same time** and neither one
contradict the other.

---

## What "lanes" means here

The design in [../../SKILL.md](../../SKILL.md) has exactly two lanes, and both are
projections of **one** DAG:

> **Compiled lane** — lower the DAG to `FcnTerms` and run the fused kernel across all
> paths (fast, no traces). This is the production path.
>
> **Traced lane** — interpret the same DAG topologically for one selected path and
> emit `{path_id, step, node_id, inputs, output, gate_state, cumulative_pv}` per node.

Same nodes. Same edges. Same bindings. One produces numbers, the other produces an
animation. Neither is allowed to contain arithmetic the other does not, because
neither contains arithmetic at all — the arithmetic lives in the kernels, which are
shared.

**What is actually in the repository is five implementations of the payoff:**

| # | lane | file | what it is |
|---|---|---|---|
| 1 | canonical lifecycle | `cpp/src/fina_risk/engine.cpp` | the production path; reads `fcn_terms` |
| 2 | scalar C++ | `cpp/src/fina_risk_cpp.cpp` | a second, simpler C++ engine, **same library target** |
| 3 | legacy numpy | `src/fina_risk/pricing.py` | the original pricing loop |
| 4 | independent oracle | `src/fina_risk/fcn_reference.py` | a scalar re-implementation, used as a differential test |
| 5 | hybrid / AAD / daily | `hybrid.py`, `aad.py`, `daily_termsheet.py` | partial re-implementations for specific questions |

Plus five benchmark executables that exist to compare them, and a CI job that
cannot see any of it.

### The CI job, corrected

I first wrote in this book that `publish-cpp.yml` triggers on a directory that does
not exist. **That was wrong too.** `native/` exists and is tracked; it holds
`CMakeLists.txt`, `pyproject.toml` and `README.md` — a scikit-build-core scaffold
whose only job is to host the real sources, which the workflow copies in with
`cp -r cpp native/cpp` before calling `cibuildwheel`. That part of the workflow is
correct and deliberate.

The real defect is subtler. The trigger is

```yaml
push:
  paths: ["native/**"]
```

which matches those three scaffold files and **not** `cpp/**`, `src/**` or
`tests/**`. So the filter watches the packaging shell rather than the source it
packages. **Commit `aae72d1` changed `cpp/src/fina_risk/engine.cpp` and this
workflow could not have run.** Because the filter misses everything real, the job
only ever fires on a version tag or a manual dispatch, so the accidental effect is
that it publishes to PyPI from tags only — which is probably what was wanted, just
not by any of this.

And the single check the job performed was `python -c "import fina_risk_cpp"` — an
import, not a test. No `pytest`, no `ctest`. The block test in
[blocks/coupon-strip.md](blocks/coupon-strip.md) was therefore unguarded: it is
registered with CTest locally, it passes, and nothing that runs on a push would
notice if it stopped.

### The worse thing, found while fixing it

Wiring up `pytest` surfaced something I had not looked for. The Python suite does
not test the C++ in this repository. It does `import fina_risk_cpp`, and that name
resolves to the **installed wheel** — a binary built from whatever tree it was
built from, whenever that was:

```
.venv/lib/python3.12/site-packages/fina_risk_cpp.cpython-312-...so
```

So all 65 passing tests were passing against a stale binary. A C++ change could
break the build, or change a PV, and the suite would stay green, because it was
never running the code it appeared to test. In CI the same thing is worse: `uv sync`
installs the *published* `fina-risk` wheel from PyPI, so the suite would have been
asserting that a released binary still behaves — a real check, but not the one the
repository's layout implies.

The fix is a build step plus one assertion, and the assertion is the point:

```yaml
- name: Build native module from source for the test run
  run: |
    cmake -S cpp -B build-pybind -DCMAKE_BUILD_TYPE=Release \
      -DPYTHON_EXECUTABLE="$(command -v python)" \
      -Dpybind11_DIR="$(python -c 'import pybind11; print(pybind11.get_cmake_dir())')"
    cmake --build build-pybind --target fina_risk_cpp
    PYTHONPATH="$PWD/build-pybind" python -c "
    import os, fina_risk_cpp
    here = os.path.abspath(fina_risk_cpp.__file__)
    print('pytest will import:', here)
    assert here.startswith(os.path.abspath('build-pybind')), 'resolved to the published wheel, not this commit'
    "
```

"65 tests pass" and "65 tests passed against the wrong binary" look identical from
the outside. This is the cheapest guard in the repository and it is the one that
was missing.

### What the workflow looks like now

A `verify` job runs on every push to real source and on every PR: build, `ctest -R
block/`, then `pytest`. It publishes nothing. The publish path is unchanged and
still gated on a `cpp-*` tag or a manual dispatch, so this adds verification
without adding an accidental release.

`pytest` is marked `continue-on-error`, and that is a debt, not a design. Two
tests in `test_fcn_native.py` fail, and they failed before any of this work:

> Both load `fina-skills/schema/fcn-native-pricing-result.schema.json`, and that
> file currently contains the **daily-term-sheet** schema. Its title is "FCN Native
> Daily-Term-Sheet Pricing Result", it requires `engine: cpp_daily_termsheet_eki`,
> `aad_engine`, `relative_delta`, `coupon_fixings`, `memory_carry`. The lane under
> test returns `cpp_fcn_rakiplus_v1` with `legs`, `delta`, `gamma`, `vega`,
> `state_transitions`. `additionalProperties` rejects it.

So the production result shape has **no schema at all**, and two tests are red
because of it. That is a real finding, not a flaky test, and the honest response is
to write the missing schema — which is not a test fix, so it is not done here. The
`continue-on-error` is there so the other 65 results are visible and a *new*
failure stands out in review, rather than the whole job being red for a reason that
predates it.

So the lanes are not compiled-vs-traced. They are **five independent
re-implementations that were each written to be checked against the others**, and
the checking has never been tighter than the checking.

---

## Why it was built this way, honestly

This is not stupidity, and the reasons are real. Recorded so the next person does not
re-litigate them:

**1. The clean-room re-implementation was the point.** `engine.cpp` was written to
be the *semantic contract* — the thing that is right — with the legacy loop kept
alongside as the thing that is *known*. From `CMakeLists.txt:36-38`:

> Semantic conformance is the native pricing contract; do not use fast-math to change
> barrier equality or lifecycle branch behaviour.

That is a good instinct and it is visible in the code: `engine.cpp` is explicitly
compiled `-fno-fast-math` while the rest of the library is not.

**2. A fused kernel has to win.** The per-path loop must be fast enough for
production RFQ quoting, and the block structure only pays off if it compiles down to
one pass. You cannot get that and also keep it trivially readable. So the fast lane
is a rewrite, and a rewrite is a second implementation.

**3. An independent oracle is genuinely valuable.** `fcn_reference.py` exists so the
fast path can be differentially tested. This is good practice and it is why several
of the defects on the coupon page were found at all.

**4. Someone had to own the correctness.** With no reference to compare against,
"the engine is the spec" is a survivable position. It is not a good one, but it is
understandable, and it is where this repository is.

---

## What it actually costs, measured on one deal

The cost is not duplication. Duplication is normal and survivable. **The cost is that
a single wrong *reading of the product* gets implemented five times, and each
implementation fails in its own local way, so cross-lane comparison cannot see it.**

The example deal is a daily-callable memory note. The call is the product. Here is
what each lane does with it:

| lane | the call | the note is priced as |
|---|---|---|
| `engine.cpp` + compiled graph | `ko_enabled: false` in the shipped fixture | **never callable** |
| `pricing.py` | latch computed correctly at `:290-307`, then discarded by `np.where(call_date <= end_step, amount, amount)` at `:327` | **always paid to maturity** |
| `daily_termsheet.py` | `np.all(performance ≥ b, axis=2)` at `:260-262`, used at `:300` | **callable, and the coupons stop** — the only lane that gets the effect right |
| `fcn_reference.py` | reads `memory_ko` at `:61` | follows whatever it is handed |
| `fina_risk_cpp.cpp` | joint same-fixing test at `:524-535`, which refuses to credit a latched asset | **misses calls; the put is suppressed and the coupons keep running** |

**Correction, and then a correction of the correction.** An earlier version of this
table said `fina_risk_cpp.cpp` has "no call logic at all". That was wrong — `:458`
reads the barrier and `:524-535` implements a fifth distinct formulation.

The next version of this book then went further and called it **the one deliberate,
documented departure in the whole repository** — a defensible reserving decision
that should be preserved and labelled, and stage 1 left it alone on that basis. The
source comment is:

> Conservative global-KO read: the daily auto-call requires every underlying
> at/above the 110% call barrier on the SAME fixing; pre-locked memory state is
> intentionally not credited (that only makes the call easier and would lower the
> reserve).

**The label has been withdrawn, and so has the reasoning behind it.** Both halves of
the stated justification fail.

The "conservative" claim is simply inverted. *Missing* a call leaves the note alive,
which keeps the coupon leg running and means the terminal branch is never reached.
Both are more liability, not less. The reading the comment calls conservative is the
expensive side, and it is expensive precisely in the product's main feature.

And the departure is not defensible, because two higher sources forbid it in
specific words. The term sheet: a Reference Asset **becomes** a Memorised Reference
Asset, and termination needs **each** of them to have become one — a persistent
status, not a same-day test. And the platform's own documentation:

> Never overwrite a prior memory-hit or KI state with a later non-hit unless product
> semantics explicitly provide for reset, which the source does not.
> — `payoff/raki-plus.md:213`

> Update `ki_seen` monotonically. — `Products/KIKO/payoff/reverse-kiko.md:59`

> occurs at least once for all underlyings — `Memory_Range_Accrual_MemRaki.md:15`,
> and seven more files

**The teaching value here is worth more than the fix.** A code comment can be
confidently wrong, and when it is wrong *in the direction of looking prudent* it
survives review indefinitely — nobody challenges a comment that says the code is
being conservative. It takes a source with actual authority, read carefully, to
overturn one. And the mechanism that let a bug acquire the status of a decision is
this page itself: an earlier draft found a comment explaining a difference from the
contract, and recorded "documented departure" as though the comment had authority to
grant it. **A comment explaining why code differs from the specification is a claim
about the specification, not evidence for it.**

**Two lanes reach opposite wrong answers about whether the note can be called early.**
Two more reach a third and fourth. Per-block detail is in
[03-where-each-block-lives.md](03-where-each-block-lives.md).

And no parity test can catch this, which is the part that matters:

- A parity test asserts *the lanes agree*. These lanes were never supposed to agree
  on features one of them does not implement.
- So the result reads as "lane 1 and lane 3 differ on KO" — a known, expected,
  documented difference — and the real defect, which is that **both are wrong**, is
  invisible.
- Compare instead with the *term sheet*. That is the only document that says which
  is right, and no test in the repository reads it.

**A cross-lane test finds disagreement. Only a spec test finds error.** The book
exists to close that gap one block at a time, and `coupon_strip` is what it looks
like when the gap has been holding for a while.

---

## What a dynamically-constructed DAG would actually fix

The proposal in the question — build the max-potential DAG and construct the active
subgraph at runtime — is the right target, and here is precisely which findings it
would have prevented. Being concrete matters more than being enthusiastic.

| finding | would one shared DAG have caught it? |
|---|---|
| call off in one lane, ignored in the other | **yes** — the call is one node; a DAG has one `global_ko_gate` and every consumer reads it |
| `np.where(x, y, y)` discarding the call | **yes** — the call date would be a node output, and a node output is not allowed to go unread |
| `coupon.rate` present, unread | **yes** — a graph with typed ports and no dead edges either has the port bound or does not have the port |
| half the spec invented | **partly** — it would not invent the spec, but a single specification object, written once and lowered, cannot drift five ways. It would also have made the invention *harder* to hide, not impossible: a typed edge to a real `next_memory` kernel is a well-formed diagram of a mechanism the contract does not contain |
| **two hand-rolled NYSE calendars sharing one bug** | **partly** — the calendars are now compared day-for-day by a test, and both copies of the New Year observation are fixed. One source of truth would remove the pair, but then the cross-language check becomes meaningless, so two copies plus a diff is the better steady state |
| **worst-of inlined 19 times, 2 of them computing a different quantity** | **yes** — one node, one output port, and the second copy would not exist |
| **`daily_termsheet.py` hardcodes a 2-asset basket** | **yes** — a declared basket size is a port with a width |
| **0% discount when `curves` is empty, and the oracle defaults to 0% too** | **partly** — one shared curve node helps, but a DAG still has to *refuse*; see below |
| two legs scaled, one not | **no** — that is a units bug at the aggregation edge, not a topology bug |
| missing 0.01 rounding | **no** — a block that rounds is a block the spec must mention |
| the deliberate same-fixing call in `fina_risk_cpp.cpp` | **no** — it was once recorded as a disclosed reserving decision that should survive, and that label is now withdrawn: the reading is non-conformant and the platform documentation forbids it in specific words. **Neither an architecture nor a confident comment can fix this one** |

**So a shared DAG addresses six of ten and leaves the units and the rounding exactly
where they are.** That is worth saying plainly, because it is the kind of claim that
gets made too confidently in either direction: a better architecture is not a
substitute for reading the contract.

The tenth row used to end with "and it should survive", on the reasoning that a
disclosed decision is not a bug. That reasoning is only as good as the disclosure,
and the disclosure turned out to be a comment arguing its own case in the direction
that looks prudent. **A good architecture is not a substitute for reading the
contract, and it is emphatically not a mandate to preserve whatever someone once
wrote down.**

The 0% discount case is the interesting one. A DAG makes the curve a *node*, so one
consumer cannot pick a different pillar than another — but a node still evaluates.
The thing that actually fixes it is not topology, it is **a block that is allowed to
refuse**: `payment_discount` given an empty curve should return
`EvidenceStatus::unresolved`, the way `engine.cpp:252` already does for a missing
fixing. That capability is a property of *having a block with its own signature*,
which is the argument for the catalogue in its simplest form.

### Three things a shared DAG would *not* do

- **It would not tell you the specification is wrong.** A DAG derived from a
  misread product is a faithful, well-typed, well-tested diagram of the wrong thing.
  The `coupon_strip` carry is exactly this: a clean graph edge
  `coupon_strip → memory_carry`, correctly typed, wired to a mechanism the contract
  does not mention — and it survived a full term-sheet review, because a well-formed
  edge reads like evidence that the edge is wanted. Topology has no way to say
  "this connection is invented"; only a document with authority can.
- **It would not fix the units.** `result.pv = funding_pv + coupon_pv - put_pv` is
  an aggregation bug and stays one.
- **It would not retire the lanes on its own.** The compiled and traced lanes would
  share a DAG, but `pricing.py` and `fcn_reference.py` exist to be *different*, and
  their value depends on staying independent. The honest target is three
  implementations — canonical, oracle, legacy — not one.

---

## The realistic sequence

In dependency order, and each step is provably safe on its own:

| stage | what | why it is safe to do alone |
|---|---|---|
| **0a** | ~~fix `publish-cpp.yml` to trigger on `cpp/**` and actually run `pytest`~~ **done** | a `verify` job now runs ctest + pytest on every real source push; the publish path is still tag-gated, so this added verification without adding an accidental release |
| **0b** | commit a cube fixture with a `.meta.json` recording the source of every pinned number | makes every later diff interpretable |
| **1** | ~~**fix the things that are ours**~~ **done, 10 of 11** | see [What stage 1 changed](#what-stage-1-changed) below. The eleventh, the `coupon_quote_scale` default, needs a human who knows the legacy booking convention |
| **1b** | ~~read the term sheet and the platform playbook against the kernels~~ **done** | found ten more defects, two of them blockers that no amount of careful coding can fix, and falsified a claim this book had been carrying. See [What the review found](#what-the-review-found) below |
| **2** | write the specification sentences from the term sheet, one per block, and mark each term as traced or invented | this is the actual deliverable; everything else is bookkeeping |
| **3** | `range_accrual`, then `memory_carry` — the two blocks that decide the two mechanisms the last page found contradictory | they are the smallest and the most load-bearing |
| **4** | schema v2: typed ports, no dead edges, `activation` as a first-class object | needs 2 and 3 to know what the ports are |
| **5a** | ~~make the two NYSE calendars comparable~~ **done** | the cross-language test is in place and the calendars **agree** — my Memorial Day claim was wrong. What it found instead is a bug **both** copies share: New Year's Day falling on a Saturday is observed on the preceding Friday, 31 December of the previous year, and neither copy flags it. PV-neutral for `termsheet1`; live for any deal spanning a New Year |
| **5b** | the generated views, and the QuantLib model layer | PV-neutral changes first, so the risky ones are never the ones also changing arithmetic |

**Stage 1 before stage 2** is the recommendation, and it is a change from the order
this book started in. The reason is that stage 1 items are *provably* wrong
independently of any judgement call, and they are currently live. Stage 2 is
irreplaceable but slow, and it will go faster on a codebase that is not quietly
mispricing a product in two directions at once.

---

## What stage 1 changed

Eleven items. Ten needed no judgement about the deal; the eleventh did, and was left
alone deliberately. Every one of the ten is covered by a test that was shown to
fail with the fix reverted: the tests were checked by putting the bug back, not
just by passing once.

| # | what | where | effect on a PV |
|---|---|---|---|
| 1 | `publish-cpp.yml` watched `native/**`, the packaging shell, so no source change could trigger it; and its only check was an import | `.github/workflows/publish-cpp.yml` | none |
| 2 | the same job never built the C++ it was testing, so `pytest` asserted against the **installed wheel** | workflow, plus `tests/test_nyse_calendar.py` style guard | none, but it is why 1–8 were invisible to the suite |
| 3 | `np.where(call_date <= end_step, amount, amount)` — both branches identical, so a correctly computed call schedule was computed and thrown away | `pricing.py:342` | **−38%** on the coupon leg for `termsheet1` |
| 4 | `float(features.get("ko_enabled") or ...)` — a boolean OR'd into a barrier level, so `ko_enabled=True` set the call to 100% | `fina-core/payoff.py` | wrong barrier wherever the flag is on |
| 5 | `local_ko_gate` was declared and read back but never emitted, so `local_enabled` was permanently false | `fina-core/payoff.py` | none for `termsheet1` (it has no local call); wrong for any deal that does |
| 6 | `locBarPrice = 999.99` read as a real level, so "no local call" and "a call at 99999%" were the same thing | `fina-core/payoff.py` | as 5 |
| 7 | no discount curve meant 0% discount and a plausible undiscounted PV, in both lanes | `engine.cpp`, `fcn_native.py` | none where a curve is supplied; a wrong price where it is not |
| 8 | a pillar with a date but no rate became a genuine **0% rate** | `engine.cpp` | as 7 |
| 9 | two calendars, one bug: New Year on a Saturday is observed on the previous Friday | `nyse_calendar.hpp`, `daily_termsheet.py` | none for `termsheet1`; 4 wrong trading days per 26 years |
| 10 | `cashflows[].discounted_amount` was per-unit and quote-scaled while `amount` beside it was absolute | `engine.cpp`, `leg_result.hpp` | none — reporting only; legs now carry an explicit `unit` |
| 11 | a three-name basket was priced as a two-name basket, silently | `pricing.py` | none for 2-name deals; refuses now |

**Left alone on purpose: the `coupon_quote_scale` default.** It is `1.0` in
`engine.cpp`, `terms.hpp` and `fcn_reference.py`, and `10.0` in `etl.py`,
`pricing.py`, `daily_termsheet.py` and `fina_risk_cpp.cpp` -- under two different
field names, `coupon_quote_scale` and `legacyCouponQuoteScale`.

Chasing this narrowed the question considerably, and in a way worth recording,
because the obvious framing of it is wrong. The production path does **not** use
`engine.cpp`'s `1.0` default, because the compiled graph always supplies a value
explicitly:

```
payoff.py:455    "coupon_quote_scale": float(legacy... or terms... or 10.0)
payoff.py:588    "coupon_quote_scale": float(graph.get("coupon_quote_scale", 10.0))
engine.cpp:125   terms.coupon_quote_scale = numeric(fcn, "coupon_quote_scale", 1.0);
```

`termsheet1` carries no `legacyCouponQuoteScale`, so the `or 10.0` is what fires,
and `engine.cpp` receives a `10.0` and never reaches its own default. **So the
three-way default disagreement is confined to hand-built requests and tests. In
production every lane prices with 10.0, and they agree.**

What is left is the real question, and it is a smaller one: **`10.0` is a code
default that the term sheet never states.** `legacyCouponQuoteScale` occurs zero
times in the 162,687-byte document. Ten points is the convention for quoting an
equity-linked note's price, so it is a reasonable guess -- but a guess is not a
specification, and it is applied to the coupon leg only, while `funding_pv` and
`put_pv` are per unit of notional. Settling it needs someone who knows how the
legacy system booked the coupon leg, not a majority vote among the defaults.

What could be done without that answer has been done: item 10 above gives every
leg an explicit `unit` field, so the PV now *says* what it is instead of not
saying.

---

## What the review found

Stage 1 fixed ten bugs that were *provably* wrong from inside the repository. Reading
the term sheet and the platform playbook line by line, afterwards, found ten more of
a different kind — and, more usefully, found that **two of the book's own claims were
wrong**, and that both were wrong in the same way.

### Two blockers that code cannot fix

These are the reason this section exists. Both look like arithmetic, both survive any
amount of testing, and neither has a fix that is not a guess.

**1. Both legacy lanes divide by the wrong number, and the right one is not in the
file.** The documented accrual factor is `N1 / N2` — "the number of days the accrual
condition is met" over "the total number of days in the observation period", stated
that way in twelve platform documents. `pricing.py:333,342` and
`fina_risk_cpp.cpp:594` both compute `(N2 - N1) / N2`.

The obvious fix is to type `N1 / N2`. **That is equally unfounded, because `N1` does
not mean what the documentation says.** In this payload `N1` is identical to
`fixingsDone` in all nine rows, so it is days *elapsed*, and the payload contains no
in-range day count anywhere. The two lanes therefore book:

| periods | shipped | should be | why |
|---|---|---|---|
| CP1–CP3, already elapsed | **zero** | 482.10 each, a historical fact | `N1 == N2`, so the fraction is 0 |
| CP4, part elapsed | 0.333 | in-range days / 21 | `N1` is a day count, not a flag |
| CP5–CP9, all future | **1.0, certainty** | in-range days / N2, per path | the 10% floor is never tested |

So the range-accrual feature is absent from the entire forward-looking part of the
note. On a 50,000 notional that is 2,571.20 of undiscounted cash shipped against
1,767.70 documented — **+45.5%** — and at PV level, 30,000 paths, seed 1729, the
coupon leg goes 0.316356 → 0.353528 (+11.8%) and the total 1.279426 → 1.316598
(+2.9%).

The right question is not "which line do I change". It is **what does the legacy
system populate**, and the answer is not in this repository. For the three elapsed
periods the correct coupon is a fact about the past — the amount actually paid on
2026-06-03, 2026-07-03 and 2026-08-05 — and the record does not hold it. Change the
expression and you have replaced one unfounded number with another and lost the
ability to tell them apart.

**2. The fixture contains two as-of dates, and the engine mixes them.** The deal
block is a 2026-08-21/23 snapshot; the pricing date is 2026-09-07. Four timestamps
agree on the first, two on the second, and `pricing.py` reads both. CP4 ended
2026-09-01, six days before the evaluation date, yet `N1[4] = 14` of 21. CP5 is four
sessions underway, yet `N1[5] = 0`. The termination latch
`GKOLocked = [true, false]` cannot be verified at all, and the engine would still
report `status: LIVE`.

This is not fixable by choosing a snapshot, and it is not fixable by any test. Every
figure in this book that mixes the two dates — **including the 0.316356 coupon-leg
figure produced by stage-1 item 3** — is right about the code and unknown about the
data. The owner is the extraction job.

### Two findings that are pure ours

**The global-KO latch**, described above, and **now fixed in one of the three
places it appears.** `pricing.py:304-321` was conformant — per-asset, sticky, OR'd into a
path-level copy, seeded from `GKOLocked` — and `fina_risk_cpp.cpp:560-572` was a
joint test on a single fixing that read no latch at all. Stage 1 made the C++
lane match, at `:464-493` and `:560-572`, and `cpp/tests/global_ko_latch_test.cpp`
(`lane/global_ko_latch`) pins it with seven hand-derived cases: three fail when the
fix is reverted, and two of those three fail again when only the seed is dropped,
so the two halves of the fix are separately pinned.

**Two sites in the same file are still non-conformant, and the reason they could
not be fixed in the same pass is the reason this section exists.**
`run_cpp_parity:884-895` and `price_daily_compact:1084-1090` — the lane
`termsheet1` is actually priced through — take the block from a *compact instrument
record* whose schema has no latch field. Fixing the rule there is a record-schema
change owned by the corpus producer, not a code change in this file. So the
finding is now *one site of three*, and the two open ones are recorded as open
rather than left to look untouched.

**`memory_carry`, which should not exist.** The word "memory" means two unrelated
things in this repository, and the engine implemented the wrong one:

- the **contract's** memory is a per-asset termination latch on the call price —
  "at or above its Call Price" on a Call Fixing Date, permanent, all assets to
  terminate the note;
- the **engine's** memory is an unpaid-coupon carry — `carried_memory`,
  `state.unpaid_coupon`, `coupon_memory`.

Three sources agree the carry is absent here, and one of them forbids it. It is not
in the 13-page term sheet. A carry *is* a real platform product — but a different
one, gated on a separate Coupon Barrier, and **mutually exclusive with Global KO**,
which this deal has. And the payload has no coupon-barrier field, no memory flag
and no accrual-state field. The only source left is
`payoff/raki-plus-native-engine-methodology.md:30,52,88`, which breaks its own rule
at line 38 of the same file: *"Never fill the gap with a convenient default merely
because it is easy to code."*

And it has propagated: `scripts/generate_benchmark.py:182` writes a hardcoded
`"unpaidPeriodRule": "N2-N1"` into **2000 of 2000** synthetic instruments, 1333 of
which also carry `features.globalMemoryCall = true` — the exact combination the
platform says cannot coexist. It is a string constant, so it cannot even be switched
off. It has **zero consumers** in any code path or schema. A dead flag on 2000
instruments reads as coverage and provides none.

### Three smaller ones

- **`pricing.py:348` is a no-op.** `accrual_fraction` and `unpaid_fraction` hold the
  same expression, so `min(unpaid / accrual, 1.0)` is exactly 1.0, verified
  numerically. This is the *second* instance of the pattern stage 1 removed at
  `:358-363`. The signature is a line that was disabled rather than deleted, and it
  now appears twice in one function.
- **The 0.01 rounding the term sheet requires twice.** Its platform implementation is
  now known: `Round(denomination × rate, 2) × (notional / denomination)`, with
  `denomination = 10000` already in the payload. Rounding per denomination and then
  scaling is **not** the same as rounding the total, so this is a real formula, not a
  tidy-up. Cheapest remaining conformance win in the repository.
- **`fixCoupon` is an additive coupon, not the Fixed/Variable flag** it was
  speculated to be. All zeros is correct. The consequence is worse than the original
  guess: the term sheet's Fixed/Variable *distinction* is not expressible in the
  platform's model at all, because `AccruRate × (N1/N2)` is one formula for every
  period. **A gap in the legacy system, not only in this repository's lanes.**

### Why the review went the way it did

Ranking the sources mattered more than the reading:

| rank | source | what it settles |
|---|---|---|
| 1 | the term sheet | what the contract promises |
| 2 | the MurexPlaybook | what the platform is built to do |
| 3 | code and comments | what somebody once believed |

The playbook earned rank 2 because it declares its own gaps instead of hiding them,
and because when it declares one, the term sheet often closes it: the playbook admits
it cannot supply a physical-delivery quantity formula, and the term sheet has it in
the form `Nominal / Exercise Price`. It also raised simultaneity as open at
`raki-plus.md:224` and answered it at `:213`.

**The pattern across both falsified claims is the same: this book settled a question
using a source with no authority to settle it.** Once, that was a code comment
claiming to be conservative. Once, it was this book's own reading of a term sheet
that turned out to be one phrase short of the real answer. A review is only worth
running against a source that can overrule you.

---

## The one-line version

Lanes are not the problem — independent oracles are worth their cost. **The problem
is that no lane is checked against the document, so a misread product becomes five
consistent-looking implementations of the wrong thing, and the consistency reads as
confidence.** A shared DAG reduces five misreadings to one. It does not reduce one
misreading to zero, and only the term sheet does that.
