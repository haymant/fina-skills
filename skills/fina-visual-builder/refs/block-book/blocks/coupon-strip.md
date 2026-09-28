# Block 1 — `coupon_strip`

The first block built to completion: specification, registry record, kernel, test,
and evidence. Read [../01-how-a-block-is-built.md](../01-how-a-block-is-built.md)
first if you have not.

---

## Traceability

| # | Stage | Answer | Where |
|---|---|---|---|
| 1 | Concept | Turns "how many days qualified" into "what rate applies this period" | below |
| 2 | Specification | one term-sheet sentence | below |
| 3 | Registry | typed ports, kernel, **not-in-scope** | [registry/blocks.yaml](../registry/blocks.yaml) |
| 4 | Kernel | `fina::risk::fcn::period_rate` | `modules/fina-risk/cpp/include/fina_risk/coupon.hpp:15` |
| 5 | Test | 10 hand-derived cases, all passing | `modules/fina-risk/cpp/tests/coupon_strip_test.cpp` |
| 6 | Evidence | **`unsupported`** — the carry is not in this contract *and* the platform forbids it for this configuration; rate **traced**; accrual factor **not derivable**; lifecycle state **unresolved** | section 7 below |

Run it:

```bash
cd modules/fina-risk
ctest --test-dir build -R block/coupon_strip --output-on-failure
```

> **Corrections on this page.** Six, all left visible rather than silently deleted,
> because in each case the book told a reader not to worry about something that does
> need attention. The last three came out of a line-by-line read of the term sheet
> against the platform's own playbook, and two of them are the reason the first
> correction mattered.
>
> | # | what an earlier version said | what is true |
> |---|---|---|
> | 1 | the `× 10` quote scale is a percent conversion | it is a **ten-point price quotation** convention (`pricing.py:384-387`). The real defect is that only the coupon leg gets it. |
> | 2 | `accruRate[0] = 0.0` is a fully-paid period | it is a synthetic pre-callable stub; the Fixed coupon is **not** lost |
> | 3 | this block is `implemented_and_evidenced` | it is **`unsupported`** — the carry is absent from the contract, not ambiguous in it. See section 2. |
> | 4 | the accrual fraction is `(N2−N1)/N2` and that is a small modelling choice | it is **not an accrual factor under any reading**, and the documented factor is `N1/N2`. Both legacy lanes are wrong, the past books at **zero** and the future at **certainty**. **Blocked on data.** See below. |
> | 5 | `fixCoupon` might be the term sheet's Fixed/Variable flag | it is an **additive** coupon — `PayRate = AccruRate × (N1/N2) + FixCoupon` — in eleven playbook files. All zeros is correct. The consequence is worse: the Fixed/Variable *distinction* is not expressible in the platform model at all. |
> | 6 | the snapshot was "17 days after the last fixing" | the fixture holds **two** as-of dates. The deal block is a 2026-08-21/23 snapshot; the pricing date is 2026-09-07; a **15-day** gap. Not a lifecycle subtlety — a fixture-integrity defect. |
>
> Correction 3 is the serious one. It is not a detail that was slightly off; it was
> the strongest claim the book is capable of making, and it was not earned.

---

## 1. Concept

A range-accrual note pays a coupon each period for the days on which the basket's
worst performer stayed inside a price range. This block takes the count of those
qualifying days and produces the rate for the period.

It does **not** decide which days qualified, and it does **not** decide how much
is paid. It is arithmetic on a count.

The band can be one-sided. On the example deal the term sheet gives a **Floor** of
10% of initial spot and writes **"N/A"** in the Barrier column for periods 2–9, so
the only live bound is a lower one. The upper bound exists in the data as the
sentinel `upRange = 999.99`, which `payoff.py:172` passes through literally rather
than translating to an infinity — see section 5.

## 2. Specification — and where it stops being the term sheet

**This section is the most important one on the page, and an earlier version of it
was wrong in a way that hid inside the block's own justification.**

The block book has a rule: the specification is *"the sentence a term sheet would
contain"*, and every test expectation is derived from it rather than from the code.
That rule is what makes a block test worth something. Applying it honestly to this
block produces an uncomfortable result, which is the finding.

### What the term sheet actually says

For the variable periods (2 to 9) the term sheet writes one formula:

> Potential Cash Dividend Amount = **Nominal Amount × Days-in Cash Dividend Rate ×
> Days-in / Total Days**

and defines the two counts:

> **Days-in** — The total number of Scheduled Trading Days **during the relevant
> Calculation Period** on which the Closing Price of the Worst Performing Reference
> Asset is at or above its Floor Price

> **Total Days** — The total number of Scheduled Trading Days **in the relevant
> Calculation Period**, regardless of whether the Daily Callable Condition is
> satisfied

Stated as arithmetic, with nothing added:

```
rate = day_in_rate * min(days_in / total_days, 1)
```

That is the whole of the term sheet's variable-coupon rule.

### What the kernel computes

```
total  = max(total_fixings, 1)
unpaid = max(qualifying_fixings - already_paid_fixings, 0)
rate   = fixed_coupon + range_rate * min((unpaid + carried_memory) / total, 1)
```

### Line by line, every term accounted for

| term | in the term sheet? | what the document says |
|---|---|---|
| `range_rate` | **yes** | Day-in Cash Dividend Rate = `0.9642%` |
| `qualifying_fixings` | **yes** | Days-in — days in the period at or above the Floor Price |
| `total_fixings` | **yes** | Total Days — days in the period |
| `fixed_coupon` | period 1 only | Fixed Cash Dividend Rate = `0.9642%`, formula `Nominal × Fixed Rate` |
| `already_paid_fixings` | **no** | no such concept anywhere in the document |
| `carried_memory` | **no** | no such concept anywhere in the document |
| `max(total, 1)` | **no** | guard against dividing by zero |
| `max(qual − paid, 0)` | **no** | guard against a negative share |
| `min(share, 1)` | **no** | implied — Days-in ≤ Total Days by definition |

**So: four terms from the term sheet, and five that are not.** Two of the five are
defensive guards and cost nothing. **Two are not guards — `already_paid_fixings`
and `carried_memory` are a mechanism, and the mechanism is not in the contract.**

### Why this is not a pedantic point

Both suspect terms are **live on this deal**, not dormant:

- `coupon_memory` is written as `bool(features.get("memory_coupon", True))` at
  `payoff.py:347` and passed through at `payoff.py:619`. The default is **true**, and
  the shipped fixture sets it to `true` explicitly. `etl.py:410` sets it
  unconditionally.
- So on every valuation that does not go out of its way to turn it off, an unpaid
  day in period 3 is added to period 4's count, and the note eventually pays a coupon
  for days the contract says it does not owe.

The term sheet forecloses this in four words, twice: both counts are scoped
*"during the relevant Calculation Period"* / *"in the relevant Calculation Period"*.
There is no clause anywhere that lets a shortfall roll forward. **The document's word
"Memory" — which appears 82 times, and in the product's own name — means
something else entirely.** See section 7.

### Three sources, and the answer is no

This page previously stopped here and called the carry `ambiguous_in_source` —
*"the source does not say which of two readings is right"*. **That was a failure of
effort, not of the source.** The source says. It says it three times over, and one of
the three sources explicitly forbids the mechanism.

**1. The term sheet.** Thirteen pages, and nothing carries a shortfall forward. There
is exactly one phrase that looks like a near miss, and it is bounded:

> the Call Settlement Amount also includes any accrued but unpaid Potential Cash
> Dividend Amount calculated up to (and including) the Call Fixing Date

*"up to (and including) the Call Fixing Date"* is a **within-period** bound. It is the
`Days Elapsed / Total Days` pro-ration that the Fixed and Variable formulas already
implement, not a balance carried across a period boundary. The same wording recurs for
the final period. A carry would be described as a balance, and this is not.

**2. The platform's own documentation — and this is the decisive one.** A carry *is* a
real product. It is called "Memory Coupon", and it is documented in
`Introduction/Common_Features.md:25,128`,
`Products/Range_Accruals/RAKI_Enhancement.md:16-28` and
`Products/Range_Accruals/payoff/raki-enhancement.md:15-17`. **It is mutually
exclusive with Global KO** — all three say so.

This deal has `KIKOSelect.globalKO = true`. So the platform's own validation rule
excludes the feature from this product configuration. Not "the document is silent" —
**"you may not have both."**

**3. The payload.** No coupon-barrier field. No memory flag. No accrual-state field,
anywhere in `RGACCLKO` or `KIKOSelect`. There is nothing for the mechanism to read.

The only surviving source is
`Products/Range_Accruals/payoff/raki-plus-native-engine-methodology.md:30,52,88`,
which describes an "unpaid memory balance" and a `double unpaid_coupon` — and which
breaks its own rule at line 38 of the same file:

> Never fill the gap with a convenient default merely because it is easy to code.

### What this does to the evidence status

The book's own standard is that a specification must be checkable against a legal
document by a domain expert. This one is not, in its current form, and now we know
which way it fails. `spec_conformance` moves from `ambiguous_in_source` to
**`unsupported`**: the block faithfully implements a mechanism that this deal is
documented as **excluded from**.

That is a different claim, and a stronger one. `ambiguous_in_source` says *a reader
should look into this*; `unsupported` says *this is the wrong mechanism for this
product, and shipping it is a defect*. The ten passing tests are correct tests of a
real, implemented, live mechanism that should not be here.

**The most useful thing this page has to say is about its own method.** The first
three drafts of this section each had an available source that would have answered
the question, and each reached for a source that could not: a code comment, then
this book's own reading, then a label that described the absence of an answer as if
it were an answer. It took a line-by-line read of a document the repository already
contained to settle a question the repository had already declared open.

### The specification, restated honestly

Two specifications, and they are not both legitimate for this deal:

- **The contract's rule:** `rate = day_in_rate * min(days_in / total_days, 1)`,
  both counts within the period, plus `Nominal × Fixed Rate` for period 1.
- **The engine's rule:** the kernel as written, with the carry — the Memory Coupon
  product, which this deal is excluded from by the platform's own rules.

The block is a faithful implementation of the second, and the second is priced for
deals that have a Coupon Barrier. There is no version of this code that serves both
products without recording which one it is doing, and there is no field in this
payload that could tell it.

**The carry mechanism is not wrong. It is a product that this note did not buy.** The
honest reading of `memory_carry` in the registry is therefore not "this needs a data
contract" — it is "**this should be removed from the compiled graph**".

### Three words worth holding onto

Even for the engine's rule, three words carry the block:

- **"fixings"** — the share is a share of *days*, not of money. `unpaid` and
  `carried_memory` are counts. Never money, never rates.
- **"capped"** — the share cannot exceed 1, so a note can never earn more than the
  full range rate in a period no matter what arrives in memory.
- **"carried in from before"** — memory enters as an *addition to the count*,
  before the division. This is why memory works and why it is bounded.

## 3. Worked examples by hand

These are the derivations. If you disagree with any of them, the specification and
the code disagree, and that is worth finding out.

Take a period with 5 fixings of which 2 were already paid, a fixed rate of 0.005,
and a range rate of 0.010. So `total = 5`, `already_paid = 2`.

| Qualifying | Carried | Unpaid | Share | Rate | Why |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0/5 = 0 | **0.00500** | Nothing qualified; only the fixed rate. The two already-paid fixings must not produce a negative share. |
| 5 | 0 | 3 | 3/5 = 0.6 | **0.01100** | The ordinary case. Three fixings still earn, so 60% of the range rate. |
| 10 | 0 | 10 | min(10/5,1) = 1 | **0.01500** | The cap. More qualifying than the period has — cannot happen in the engine, but the block must still not overpay. |
| 1 | 2 | 1 | (1+2)/5 = 0.6 | **0.01100** | Memory. One fixing earned here plus two carried in gives the same result as earning three. |
| 1 | 0 | 0 | 0/5 = 0 | **0.00500** | The floor. Fewer fixings qualified than were already paid; the unpaid count floors at zero. |

Two degenerate cases, because real term sheets produce them:

- **`total_fixings = 0`.** The divisor is floored at 1 so this must not divide by
  zero. With nothing qualifying the rate is the fixed rate. With one fixing
  carried in, that single fixing earns the **full** range rate — an unavoidable
  consequence of dividing by 1.
  *Evidence note:* the example deal does **not** exercise this. Only the `PUT` and
  `FUNDING` jobs carry `N2 = [0, 0]`, and `payoff.py:117` discards both by taking
  `jobs[-1]` — the `COUPON` job, whose `N2` is `[20, 1, 21, 22, 21, 21, 22, 20,
  22, 19]`, with no zeros. An earlier version of this section claimed the legacy
  booking path supplies `N2 = 0`; that is true only of the two legs the pipeline
  throws away.
- **`fixed_coupon = 0`.** `payoff.py:170` hard-codes this for legacy-sourced
  coupons and never reads the term sheet's `fixCoupon` array, so on this path the
  block always collapses to `range_rate × share`.
  *This is not because the product has no fixed coupon.* The term sheet states a
  **Fixed Cash Dividend Rate of 0.9642%** — the same number as the Day-in rate —
  and the JSON carries a `fixCoupon` array for it, which is all zeros. The zero
  means the legacy engine routed the Period 1 fixed coupon through the accrual grid
  instead (section 7), not that no fixed rate was agreed.

## 4. Kernel

```cpp
// cpp/include/fina_risk/coupon.hpp:15-19
inline double period_rate(const CouponPeriodTerms& terms,
                          double qualifying_fixings,
                          double carried_memory) noexcept {
    const double total  = std::max(static_cast<double>(terms.total_fixings), 1.0);
    const double unpaid = std::max(qualifying_fixings - static_cast<double>(terms.already_paid_fixings), 0.0);
    return terms.fixed_coupon + terms.range_rate * std::min((unpaid + carried_memory) / total, 1.0);
}
```

Pure, header-visible, no state, no allocation, no I/O. Two inputs are scalars and
the third is a plain struct of numbers. This is why the block is testable at all.

## 5. What this block does not do

The most important section on this page. The concept "the coupon" is much bigger
than this block, and conflating them is how a PV gets multiplied by a notional
twice.

| Concern | Where it actually lives |
|---|---|
| Which days qualified | block `range_accrual` — `in_range`, `coupon.hpp:9`, counted by the caller at `engine.cpp:305` |
| Carrying the unpaid count forward | block `memory_carry` — `next_memory`, `coupon.hpp:21`, `engine.cpp:320` |
| The coupon barrier | the call site, `engine.cpp:307` — and see the call-bypass warning below |
| Knock-out, and which periods survive | the call site, `engine.cpp:269-278`, and the period clamp at `:293-294` |
| Memory on or off | the call site, `engine.cpp:308` |
| Discounting to today | block `payment_discount` — inlined at `engine.cpp:317,328,333` |
| Turning a rate into money | the call site, `engine.cpp:316` |
| Units | the call site, `engine.cpp:357` |

### The call site is part of the block's meaning

```cpp
// engine.cpp:307-310
const bool coupon_barrier_ok = period.coupon_barrier <= 0.0 || period_end_performance >= period.coupon_barrier;
const double carried = terms.coupon_memory ? state.unpaid_coupon : 0.0;
double rate = period.fixed_coupon;
if (coupon_barrier_ok) rate += period_rate(period, qualifying, carried) - period.fixed_coupon;
```

Three things a reader of the kernel alone would miss:

1. **The block is not always called.** If the period's coupon barrier failed, the
   rate stays at `fixed_coupon` and no range accrual is earned at all.
2. **When the barrier fails, the whole period is remembered.** `engine.cpp:320`
   sets the carry to the full `total_fixings`, not to a smaller number. Barrier
   failed, nothing earned, all of it carried forward.
3. **The `+= period_rate(...) - fixed_coupon` shape is an algebraically empty
   rearrangement.** It is a conditional written the long way round. Not a bug —
   but if you are reading the arithmetic to understand the formula, it will mislead
   you. The behaviour is: `rate = coupon_barrier_ok ? period_rate(...) : fixed_coupon`.

### The barrier gate is wrong for the call branch — it just never shows

`coupon_barrier_ok` is computed at `engine.cpp:307` and gates the **entire** rate at
`:310`, whether or not the note has been called. The term sheet says the opposite. For
the Period 1 fixed coupon:

> If the Daily Callable Condition is satisfied, the Potential Cash Dividend Amount
> will be calculated in accordance with the following formula, **regardless of
> whether the Closing Price of the Worst Performing Reference Asset is at or above
> its Barrier Price on the Call Fixing Date**

On a call, the barrier is **skipped entirely** and the amount is a straight
time-proration of the fixed rate. The kernel has no such branch. So if the coupon
barrier field were ever populated, the engine would return zero for a period the
term sheet says pays a pro-rated fixed amount.

It currently gets this right for the wrong reason, twice over:

- `coupon_barrier` is **never set**. `payoff.py:170-183` writes ten keys into each
  period and `coupon_barrier` is not one of them, so `payoff.py:517` substitutes
  `0.0`, and `coupon_barrier_ok` at `engine.cpp:307` is unconditionally `true`.
- On this deal the period-1 barrier is also *legitimately* satisfied, because the
  worst performer clears it comfortably (see section 7).

So the field is dead and its deadness currently produces the right answer. That is
the third instance of the pattern in this section: correctness that depends on a
field never being read. Fixing the field without fixing the gate would turn a
latent bug into a live one.

### The unit trap

`engine.cpp:316` turns the rate into money with `cash = notional * rate`, then
`engine.cpp:357` divides the notional back out and multiplies by
`coupon_quote_scale`. The result is a PV **per unit of notional, in quote-scale
units**. Never compare a PV from this system to another PV without checking the
unit first.

**The `× 10` is a price-quotation convention, and the code says so. Applying it to
one leg only is a confirmed defect.**

This section has now been corrected twice, and the second correction is the right
one. Version 1 of this page said the scale existed "because those term sheets state
rates in percent" — false. Version 2 said the ×10 might simply be wrong — also
not quite right, and it understated the problem. What the code actually says:

```python
# pricing.py:384-387
# Legacy coupon quotes are expressed in the instrument's ten-point price
# convention, while funding/option legs are normalized to notional.
quote_scale = float(deal.get("legacyCouponQuoteScale", 10.0))
quoted_pv = raw_pv / notional * quote_scale
```

**So the ×10 is a quotation unit, not a percent fix and not a coupon multiplier.**
Someone who knew the legacy system wrote that comment, and it is consistent with the
data: the term sheet's own `coupon_quote_scale` is absent, the JSON stores
`0.009642` as a decimal fraction, and a ten-point price quote is a real thing in
fixed-income convention. Question 1 in section 7 is therefore **narrower than this
page previously said**: the value `10.0` is probably right, and the comment is the
evidence.

### The defect is that only one of three legs gets it

Here is the whole PV, from `engine.cpp:352-386`:

| leg | line | scaling | declared unit |
|---|---|---|---|
| `coupon_pv` | `engine.cpp:357` | `coupon_pv_sum × quote_scale ÷ notional` | `currency_per_unit_notional_quote_scaled` |
| `funding_pv` | `engine.cpp:369` | `funding_pv_sum ÷ notional` | `currency_per_unit_notional` |
| `put_pv` | `engine.cpp:375` | `put_pv_sum ÷ notional` | `currency_per_unit_notional` |

```cpp
result.pv = funding_pv + coupon_pv - put_pv;   // engine.cpp:386
```

**Two legs in one unit are added to a third leg in another.** The total is not in
per-unit-of-notional, and it is not in ten-point quote. It is in no unit at all.

Stage 1 gave each leg a `unit` field, so the three rows above now say so
out loud (`engine.cpp:381-385`) — and `result.pv` at `:386` is still the sum of
three differently-scaled quantities. The tag is on the parts; it is not on the
sum. Anyone reading `pv` alone still cannot tell which number it is.

`fina_risk_cpp.cpp:955` does exactly the same thing — `out.pv = df - out.put +
out.coupon`, with the ×10 applied one line earlier at `:954`, and with no unit field
at all.

This is not a subtle units question. It is a sum that does not type-check, in the
production path, on every deal. And it is *not* the fault of the `10.0`:

- If the PV is **per unit of notional**, the answer is that the coupon leg should not
  be scaled at all, and `10.0` should be `1.0`.
- If the PV is **a ten-point quoted price**, then funding and put need the same ×10,
  and they do not have it.

Either way one of those two lines is wrong, and the codebase contains no test that
distinguishes them — because a PV is a single number and a wrong unit still
returns a plausible one.

**This one needs no knowledge of the deal to fix.** It is a units bug in three lines
of a pricing engine, and it is the highest-confidence defect in this book. Question 1
in section 7 is now only about which of the two conventions the legacy system uses.

## 6. Test

`modules/fina-risk/cpp/tests/coupon_strip_test.cpp`, registered with CTest as
`block/coupon_strip`. Ten cases, no framework, no JSON, no simulation, no market
data. Compiled against the headers only — deliberately **not** linked to the
pricing library, because a block test that pulls in the engine can no longer prove
anything about the block.

```
block/coupon_strip -- kernel fina::risk::fcn::period_rate (coupon.hpp)
  ok    no_fixings_in_range                0.0050000000
  ok    partial_qualification              0.0110000000
  ok    full_range_caps                    0.0150000000
  ok    memory_carried_in                  0.0110000000
  ok    already_paid_exceeds_qualifying    0.0050000000
  ok    zero_total_fixings_guard           0.0050000000
  ok    zero_total_with_memory_uses_one    0.0150000000
  ok    fractional_memory                  0.0087500000
  ok    legacy_fixed_coupon_is_zero        0.0050000000
  ok    zero_range_rate                    0.0015000000
10 checks, 0 failures
```

**How the expected values were obtained.** By hand, from the specification, using
the table in section 3. Not by running the kernel and writing down its output.
That is the difference between a test and a photograph. Every expected value in
the test file has a comment explaining the sentence it came from, so a reviewer
can check the reasoning without reading the kernel.

**No pinned value in the test came from a fixture.** The one case that used to
assert `0.00713` — the unsourced literal from
`fcn-terms-projection.example.json` — now uses `0.0015`, chosen precisely because
it is obviously arbitrary. A number with no deal behind it has no business being
pinned in a test, even as an innocent placeholder, because a reader cannot tell a
placeholder from a leak without checking.

**Why a tolerance.** The specification describes a real number; the kernel
computes a `double`; `0.005 + 0.010 * 0.6` is not exactly representable in binary.
The comparison is to `1e-12` absolute. This is also why the test must not be built
with `-ffast-math` — reassociation would move those last bits and convert a check
of the specification into a check of the compiler.

## 7. Evidence — the open problem

The arithmetic is settled. The inputs are not. Those are different questions, and
this block fails the second one — on two counts, plus a third about state.

This section is the longest on the page because it is where the block earns its
keep. A block whose inputs cannot be traced to a term sheet is a block nobody can
review, and this deal turned out to contain three separate kinds of that problem:
an unsourced field, an unverified units default, and a lifecycle snapshot with a
hole in it.

### What the chain looks like

The legacy term sheet field is `RGACCLKO.accruRate`, one rate per accrual period.
Tracing it forward:

1. `payoff.py:169` reads `rgacc.accruRate` into each period's `range_rate`.
   **This is the only place a rate enters the engine.** It never reads
   `terms["coupon"]["rate"]`.
2. `payoff.py:171` hard-codes `fixed_coupon = 0.0` for legacy-sourced coupons. So
   for this product family the block reduces to `range_rate × share`, and the fixed
   rate in the specification is dead on this path.
3. `engine.cpp:187-188` reads `range_rate` and `fixed_coupon` per period.
4. `engine.cpp:305` calls the block.

So the authoritative coupon rate is `RGACCLKO.accruRate`, and it is
`0.009642` for the example deal.

**And that number is now fully traced to the term sheet**, which closes the last
open item on the rate itself:

| Term sheet (line 101, 105) | Value | Form |
|---|---|---|
| Fixed Cash Dividend Rate | `0.9642%` | percent, as written |
| Day-in Cash Dividend Rate | `0.9642%` | percent, as written |
| `0.9642 ÷ 100` | `0.009642` | the decimal fraction the JSON stores |

One division, exact, no rounding. The term sheet states the rate **twice, under two
names, with the same value** — so a single per-period array is sufficient, but only
because the two clauses happen to agree. Had they differed, `accruRate` alone could
not represent the deal. That is worth knowing before treating one array as
structurally sufficient rather than accidentally sufficient.

### Why is `accruRate[0] = 0.0`? Because period 0 is a stub, not a settled period

`accruRate` and `lowRange` are the **only two arrays in the whole `RGACCLKO` block
whose index 0 is unique** — `accruRate = [0.0, 0.009642 × 9]` and
`lowRange = [0.0, 0.1 × 9]`. Every other array starts with a value that its
neighbours also use. So index 0 is not a data point in the series; it is something
else, and those two arrays are the only place it shows.

**An earlier version of this page got this wrong, twice.** It claimed the Fixed
coupon had been dropped, and then that `accruRate[0]` was zero because period 0 was
already fully paid (`N1[0] == N2[0] == 20`). Both are false, and the second is
falsified by its own neighbour: **JSON[1] is equally settled** (`N1 = N2 = 1`) **and
carries the full `0.009642`.** If "settled" meant "zero rate", index 1 would be zero
too.

The real reason is structural. **The term sheet has 9 calculation periods; the JSON
has 10.** Period 1 has been split in two, and index 0 is the piece that has no
term-sheet period of its own:

| JSON | end date | payment | `N2` | | term-sheet Period | end date | payment | Total Days |
|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-01 | **2026-06-03** | 1 | | **1** | 2026-06-01 | **2026-06-03** | 21 |
| 2 | 2026-07-01 | 2026-07-03 | 21 | | 2 | 2026-07-01 | 2026-07-03 | 21 |
| 3 | 2026-08-03 | 2026-08-05 | 22 | | 3 | 2026-08-03 | 2026-08-05 | 22 |
| 4 | 2026-09-01 | 2026-09-03 | 21 | | 4 | 2026-09-01 | 2026-09-03 | 21 |
| 5 | 2026-10-01 | 2026-10-05 | 21 | | 5 | 2026-10-01 | 2026-10-05 | 21 |
| 6 | 2026-11-02 | 2026-11-04 | 22 | | 6 | 2026-11-02 | 2026-11-04 | 22 |
| 7 | 2026-12-01 | 2026-12-03 | 20 | | 7 | 2026-12-01 | 2026-12-03 | 20 |
| 8 | 2027-01-04 | 2027-01-06 | 22 | | 8 | 2027-01-04 | 2027-01-06 | 22 |
| 9 | 2027-02-01 | 2027-02-03 | 19 | | 9 | 2027-02-01 | 2027-02-03 | 19 |
| **0** | 2026-05-29 | 2026-06-02 | 20 | | — | **no such period** | | |

**Periods 2–9 match the term sheet exactly on all three fields: end date, payment
date, and day count. 8 of 8.** JSON[1] carries Period 1's end date *and* its
03 Jun 2026 payment date exactly, with the 21 days split `20 + 1`. The payment-date
match is what settles it — 03 Jun 2026 is not a date the engine would invent. And
JSON[0] matches nothing, because it is not in the document.

**Why the split, and why the split date is 01 Jun.** The Callable Period runs
*"From (and including) 01 Jun 2026"*, which is both the **end of Period 1** and the
**first day on which the note can be called** (`GKODate[0] = 46174 = 2026-06-01`).
The legacy engine runs its accrual grid on a monthly grid and carves it at that
structural boundary. Period 1 straddles it, so it becomes a 20-day stub plus a
1-day chunk.

**And that is why the Fixed coupon is not lost.** The term sheet tests the Period 1
barrier on *the specified Calculation Period End Date* — which is 01 Jun 2026, the
end of JSON[1], not the end of JSON[0]:

> If the Closing Price of the Worst Performing Reference Asset on the specified
> Calculation Period End Date is at or above its Barrier Price, the Potential Cash
> Dividend Amount = Nominal Amount × Fixed Cash Dividend Rate

So the 1-day chunk is not a leftover. It **is** the observation period.

The arithmetic closes exactly. Under the legacy path `fixed_coupon = 0.0`:

| | rate earned | days |
|---|---|---|
| JSON[0], 20-day stub | 0 — no daily test exists on it | 20 |
| JSON[1], 1-day observation | `0.009642 × 1/1` = the **full** fixed rate | 1 |
| **Period 1 total** | `0.009642` = **exactly** `Nominal × Fixed Cash Dividend Rate` | 21 |

**It is correct — and it is correct by luck.** It works only because the observation
date happened to land on a 1-fixing chunk, where dividing by 1 hands over the whole
rate. Had the boundary fallen mid-period, JSON[1] would be several days long and the
engine would pay `0.009642 × n/n` — a silent pro-ration that the Fixed clause never
authorises. A test that passes for an arithmetic reason rather than a structural one
is a test that will not survive a change of dates.

Three further details confirm 01 Jun is a product-level boundary and not an
accident of this grid:

- **Only the `COUPON` job has an accrual grid at all.** The `PUT` and `FUNDING` jobs
  carry two placeholder rows each, both with `N2 = 0`, dated 2026-06-01 and
  2027-02-01. 2026-06-01 is the only interior date on either leg.
- **The one-day chunk is the shortest period in the array.** An earlier theory that
  the stub was "the short first period" is refuted by JSON[1] being 1 day — shorter
  than the stub's 20 — while carrying full `0.009642`.
- **The term sheet's own period 1 says 21 Total Days**, and `20 + 1 = 21`. The
  engine is not losing days; it is reporting them under two rows.

`accruRate[0] = 0.0` and `lowRange[0] = 0.0` are the engine declining to quote a
rate and a range for a chunk of time during which, per the deal, no rate is tested.
That is the right answer, for a reason that is entirely structural.

### Is `0.00713` a randomly generated sample value? Almost certainly

The obvious hypothesis is that `0.00713` is `0.009642` scaled by some share of
unpaid fixings, i.e. `0.009642 x (N2-N1)/N2 = 0.00713` for some period. That would
make it a derived quantity rather than an invention. It is not. The implied share
is `0.7394731`, and the per-period shares available in `Jobs[2]` are only three
distinct values:

| Period | N1 | N2 | (N2-N1)/N2 | x 0.009642 |
|---|---|---|---|---|
| 0-3 | = N2 | = N2 | 0 | 0 |
| 4 | 14 | 21 | 1/3 | 0.003214 |
| 5-9 | 0 | 19-22 | 1 | 0.009642 |

Brute-forcing every ordered ratio of every value in `N1`, `N2` and `fixingsDone`
reproduces nothing within 5e-6 of `0.00713`. So the derivation hypothesis is dead.

**But there is a much better explanation, and it is not a hand-typed literal.**
`0.00713` sits inside the interval `[0.006, 0.018]`, and that interval is the
coupon range this repository's own **synthetic deal generator** draws from:

| File | Line | What it does |
|---|---|---|
| `fina_risk/etl.py` | 159 | `coupon = round(rng.uniform(0.006, 0.018), 6)` |
| `fina_risk/benchmark_lanes.py` | 67 | same range, same purpose |
| `scripts/run_100k_rust_cpp.py` | 95 | same range, same purpose |
| `scripts/generate_benchmark.py` | 180 | same range, same purpose |

`0.00713` is reproducible as the **5th draw** of
`np.random.default_rng(42).uniform(0.006, 0.018)`. It is **not** reproducible at
this repository's own seed `20260909` (5th draw = `0.015135`).

**So: `0.00713` is very probably a generated sample value, not a negotiated rate and
not a derivation.** I am recording it as *almost certainly* rather than *certainly*
because I cannot prove which seed produced the fixture — the value is consistent
with a synthetic draw from the repo's own range, and inconsistent with every
derivation from the deal. The durable conclusion does not depend on settling it:
**`0.00713` carries no information about this note.** It is not evidence that a
second coupon rate was ever agreed, and no reconciliation should ever try to match a
PV to it.

### The finding that generalises is the field, not the number

So why does this page mention `0.00713` at all? Because the *literal* is fixture
noise and I over-weighted it. The durable finding is one field:

> **`economics.coupon_rate` is a trade-layer parameter with no counterpart in the
> source system, no kernel that reads it, and no validation that it means
> anything — yet the schema presents it in the canonical graph as though it were
> the coupon rate.**

`0.00713` is merely the symptom that made it visible. The full chain:

| Step | Where | What |
|---|---|---|
| 1 | `fcn-terms-projection.example.json:21` | `economics.coupon_rate: 0.00713` — hand-authored trade fixture |
| 2 | `payoff.py:218` | `coupon_rate = float(economics.get("coupon_rate", 0.0))` |
| 3 | `payoff.py:292`, `:423` | copied to `nodes[coupon_strip].config.rate` and `coupon.rate` |
| 4 | `payoff.py:440-446` | the `coupon_rate_note` divergence warning fires |
| — | — | **no step reads the term sheet for this value** |

Four checks establish that step 4 has no upstream:

- `0.00713` occurs **zero** times in the 162,687-byte term sheet, and zero times in
  the reformatted term sheet too.
- The term sheet has **no `coupon_rate` key and no `economics` block at all**, so
  the field a real rate would have to come from does not exist.
- There is **no number anywhere in the term sheet between 0.006 and 0.009** — not
  just no `0.00713`, nothing in that band to derive one from. The only decimals the
  document contains are `5e-05`, `0.0001`, `0.005`, `0.01`, `0.9642`, and a set of
  prices above 20.
- `0.00713` falls inside `[0.006, 0.018]`, the range this repository's synthetic
  deal generator draws coupons from (section above). It is consistent with a
  generated sample and inconsistent with every derivation from the deal.

The note the repository already writes reads like a choice between two legitimate
sources. It is not a choice:

> `coupon_rate_note`: *"semantic/compiled rate diverges from legacy RGACCLKO
> accruRate; engine periods carry the legacy per-period rate"*

**The warning can never fire from a real term sheet.** Its guard is
`if legacy and coupon_rate and period_rate and abs(...) > 1e-9`. With a real deal
and no declared `coupon_rate`, the honest default is `0.0`, the guard
short-circuits, and nothing is emitted. To make the divergence-detection feature
visible in a fixture, a number had to be invented — and the fixture now teaches
every reader that a semantic rate and a legacy rate legitimately differ, which is
the belief it was built to manufacture.

And the field is inert besides: **the C++ engine never reads `coupon.rate`.**
Across the whole canonical-terms compiler it reads exactly five `fcn_terms` keys —
`currency`, `notional`, `performance_indicator`, `coupon_quote_scale`,
`memory_ko_mode` — and the only other occurrence of the word "coupon" is a leg
label in the result.

### The word "Memory" means two different things, and the code has both

The product is called **Memory US Stocks ELIs**. The word appears 82 times in the
term sheet. The block book calls this block a *memory* block. And the code has
**four different fields** whose names all contain the word.

They are two unrelated mechanisms, and the term sheet only describes one of them.

**Mechanism A — the contract's memory: a per-asset termination latch.**

> **Memory Event** — A Memory Event in respect of a Reference Asset occurs on a Call
> Fixing Date if the Closing Price of the Reference Asset on such Call Fixing Date is
> **at or above its Call Price**.

> **Daily Callable Condition** — If **each** of the Reference Asset in the Reference
> Basket has become a Memorised Reference Asset on a Call Fixing Date, the Daily
> Callable Condition is satisfied and the Memory US Stocks ELIs will be terminated on
> such Call Fixing Date.

That is the whole of it, and it has nothing to do with coupons. Each share is
**stamped** the first time it trades at or above 110%. The stamp is **permanent**.
When every share has been stamped, the note dies. The coupon plays no part.

**Mechanism B — the engine's memory: an unpaid-day carry.** `carried_memory` in
`coupon.hpp:18`, `state.unpaid_coupon` in `engine.cpp:320`, `coupon_memory` in
`terms.hpp:102`. A day that earned nothing is added to the next period's count.

**Neither name is wrong. Together they are a trap**, because a reader who sees
`memory_ko` and `coupon_memory` in the same struct reasonably assumes one is a
variant of the other.

| | the contract's memory | the engine's memory |
|---|---|---|
| what is remembered | *which shares have hit 110%* | *how many days earned nothing* |
| where it lives | `barriers.memory_ko` | `coupon_memory` |
| effect | ends the note | raises a later coupon |
| in this term sheet? | **yes**, it is the product | **no** |

### And on this deal the two flags are set exactly backwards

The shipped reference fixture for this note, `fcn-terms-projection.example.json`,
declares:

```json
"memory_coupon": true,
"memory_ko": false,
"ko_enabled": false
```

Read that against the contract:

| the contract requires | the fixture sets | effect |
|---|---|---|
| a sticky per-asset latch (Memory Event) | `memory_ko: false` | the latch is **off** |
| a callable note, callable every day to expiry | `ko_enabled: false` | the call is **off** |
| no cross-period coupon carry | `memory_coupon: true` | the carry is **on** |

**The two flags the term sheet describes are off. The one it does not describe is
on.** The deal data disagrees with the fixture, too — `KIKOSelect` carries
`globalKO: true`, `GKOLocked: [true, false]`, and a `GKODate` of `46174`
(2026-06-01), which is one share already stamped and the callable period open. The
call is real in the source data and switched off in the graph built from it.

`payoff.py:281` reads `features.get("memory_ko", False)` and `payoff.py:279` reads
`features.get("ko_enabled", True)`, so the code's *defaults* are the opposite way
round from the fixture. That is worth saying plainly: **whether the production path
prices this note as callable depends on which pipeline populated `features`, and I
have verified the fixture, not the live call.** But the fixture is the artefact the
schema ships and that a reader trusts, and it teaches the opposite of the contract.

### What the engine does with the latch when it is on

`engine.cpp:243-260` implements mechanism A properly, and it is the best code in
this file:

```cpp
// engine.cpp:255-260
if (terms.barriers.memory_ko) {
    if (terms.barriers.local_enabled && compare(performance, terms.barriers.local_barrier, terms.barriers.local_operator)) state.local_memory_locks[underlying] = 1U;
    if (terms.barriers.global_enabled && compare(performance, terms.barriers.global_barrier, terms.barriers.global_operator)) state.global_memory_locks[underlying] = 1U;
    all_local_memory = all_local_memory && state.local_memory_locks[underlying] != 0U;
    all_global_memory = all_global_memory && state.global_memory_locks[underlying] != 0U;
}
```

Latches set, never cleared, AND-ed across the basket. That is the contract, exactly.

**But it is gated behind a flag that also has to be right.** `local_enabled` is
derived at `payoff.py:596` as `any(n["kind"] == "local_ko_gate" for n in nodes)` —
and `compile_payoff_graph` **never emits a `local_ko_gate` node**, so
`local_enabled` is permanently `false`. The contract's call is a per-asset mechanism
(the global AND of per-asset latches), so it routes through the *global* gate; that
part is fine. But it means the contract's call can only work if `global_enabled` is
also true, and the fixture sets it false.

**One flag away from correct, and the flag is wrong.** `engine.cpp:125-126` even
refuses to run a memory KO that has not declared its mode:

```cpp
// engine.cpp:144-146
if (fcn.value("memory_ko", false) && text(fcn, "memory_ko_mode") != "per_underlying_ever") {
    return {{}, EvidenceStatus::ambiguous, "memory_ko requires explicit memory_ko_mode=per_underlying_ever"};
}
```

The guard is good. It has simply never been triggered, because the flag it guards is
never set.

### The other lane computed the call correctly, and then threw it away

**This defect is fixed; the record of it is kept because the shape is instructive.**

`pricing.py:304-321` is a faithful, vectorised implementation of the contract's
Daily Callable Condition — per-asset lock, sticky, AND-ed, with the path-level
state copy that two underlyings sharing a latch state correctly calls for.

And then, a few lines into the coupon loop, this:

```python
# pricing.py:327, as it stood
amount = np.where(call_date <= end_step, amount, amount)
```

**Both branches were `amount`.** The whole computed call schedule was multiplied by
a mask that is identically one. A called note kept accruing and paying coupons for
every remaining period. `np.where` with two identical branches is the shape of a
line someone disabled rather than deleted, and the twenty lines of correct latch
logic above it were the fossil.

Stage 1 replaced it with the elapsed-fraction form the term sheet actually specifies
(`pricing.py:364-366`), and left the old line in a comment at `:358-363`:

```python
# pricing.py:364-366
span = max(end_step - this_begin + 1, 1)
elapsed = np.clip(call_date - this_begin + 1, 0, span)
amount = amount * (elapsed / span)
```

A period that ended before the call pays in full; the period containing the call
pays only the fixings up to and including the call; a period starting after the
call pays nothing. That is the contract sentence, and it took a test to find —
the old line was not wrong in a way that arithmetic comparison would notice.

**So both lanes were wrong, in opposite directions, about the same feature:**

| lane | the call | the note is priced as |
|---|---|---|
| `engine.cpp` (canonical, production) | enabled, but at a **100% barrier** | a call that never fires |
| `pricing.py` (legacy) | computed, then discarded | **always paid to maturity** |

The first row is not the graph switching the call off. It is the same
boolean-as-a-level bug as in `fina-core/payoff.py`, reaching the canonical lane
through the compiled graph: `enabled` is `True` by default, and the barrier beside
it was `float(features.get("ko_enabled") or ...)`, which is `float(True) == 1.0`.
A 100% daily call on a worst-of basket is a call that essentially never fires, so
the production lane also priced the note as uncallable -- by a different mechanism
and with a plausible-looking node config saying `"enabled": true`.

Both are now fixed, and the same property is asserted in both: the barrier is
1.10 whether or not the call is enabled, and the flag lives only in `enabled`.

Neither prices a daily-callable memory note. And because they are separate
implementations, no test comparing them can catch either — a difference is
*expected* between lanes, so a 10x or whole-life difference reads as noise.

### Fixed: what the mask should have been, and what it is worth

The term sheet pays, on a call, "any accrued but unpaid Potential Cash Dividend
Amount calculated **up to (and including) the Call Fixing Date**". That is a
pro-rata, not a switch, and it has three cases:

| the call falls | the period pays |
|---|---|
| after the period ended | all of it |
| inside the period | the fixings up to and including the call, pro rata |
| before the period began | nothing |

So the fix needs to know where each period *begins*, which the loop did not track.
`end_step` is the step nearest the period's `endDate`; the next period begins at
`end_step + 1`. The tracking has to be hoisted above the `unpaid <= 0` `continue`,
because a period with nothing owed is skipped and still advances the window.

```python
# pricing.py:364-366
span = max(end_step - this_begin + 1, 1)
elapsed = np.clip(call_date - this_begin + 1, 0, span)
amount = amount * (elapsed / span)
```

`clip` to `0 .. span` is what makes the three cases above fall out for free, and
what makes a never-called path (`call_date` pinned at `steps`) pay in full without
a special case.

**What it is worth, on the shipped fixture, 30,000 paths, seed 1729:**

| | coupon leg |
|---|---|
| before (mask of ones) | 0.509887 |
| after (contract pro-rata) | **0.316356** |
| | **-38.0%** |

The reason is not subtle, and it is the reason this is a defect rather than a
tuning question:

| period ends | share of fixings actually paid | P(called by then) |
|---|---|---|
| 1 | 100% | 0% |
| 2 | 89.8% | 23.6% |
| 3 | 66.7% | 41.7% |
| 4 | 53.6% | 50.8% |
| 5 | 46.0% | 57.0% |
| 6 | 41.0% | 61.0% |

**61% of paths on this deal are called by expiry.** The old number paid the entire
coupon schedule on 61% of the note population — notes that no longer existed. The
call is not a rare event on a 110% call barrier with the worst-of starting at
99.4% of initial; it is the modal outcome.

Period 1 is 100% because no path can be called before the first period ends, and
that is a useful sanity handle: if the first period ever truncates, the call
schedule is wrong, not the pro-rata.

I recomputed the whole leg independently before accepting the new number, rather
than reading it back out of the function under test: capture the three arguments
`_coupon_pv` was given, rebuild the latch and the accrual from the barrier rule and
the term-sheet fields, and compare. It reproduced 0.316356 to 1e-9. A Monte-Carlo
figure that is only ever checked against itself is not a check.

`test_coupon_leg_uses_unpaid_counts_and_payment_lag` had `0.48 < coupon < 0.54` —
a band, and a band centred on 0.509887, the *untruncated* value. It was recorded
from the output of the code that contained the bug. It is now `0.30 < coupon <
0.34`, and a second test asserts the *shape* of the truncation rather than the
total, so that reverting the fix fails whatever the PV happens to be.

### The quote scale is not a fixture problem. It reaches a real deal.

- **`coupon_quote_scale: 10.0` is a code default, and the real term sheet does not
  supply one.** `legacyCouponQuoteScale` occurs **zero** times in the 162,687-byte
  term sheet. `payoff.py:455` therefore takes its literal fallback:

  ```python
  "coupon_quote_scale": float(legacy_facts.get("legacy_coupon_quote_scale")
                              or terms.get("coupon", {}).get("coupon_quote_scale")
                              or 10.0),
  ```

  So **every real deal that does not name the field is priced with a ×10 coupon
  leg.** This is not confined to hand-authored examples, which is what an earlier
  version of this page claimed. It is the default on the production path.

- **The one place the C++ author set the field deliberately, they set it to 1.0.**
  `engine.cpp:202-205` handles a request with no lifecycle schedule and writes
  `terms.coupon_quote_scale = 1.0;` under the comment *"Its coupon is explicitly
  zero."* The neutral value, written on purpose, is `1.0` — not `10.0`. That is
  weak but real evidence against `10.0` being correct.

- **Two C++ engines in the same binary read two different fields with two different
  defaults.** `fina_risk_core` compiles both:

  | | reads | field | default |
  |---|---|---|---|
  | `engine.cpp:125` | compiled terms | `fcn_terms.coupon_quote_scale` | `1.0` |
  | `fina_risk_cpp.cpp:591,954` | the **raw deal** | `legacyCouponQuoteScale` | **`10.0`** |

  Whenever `fcn_terms.coupon_quote_scale` is absent, these two engines return coupon
  legs that differ by a factor of ten for the same deal and the same paths. A parity
  or differential test that compares them will report a clean 10x coupon mismatch
  and nothing else — and the most natural reading of that result is "the paths
  differ", when the cause is a units default.

- **The Python oracle defaults differently again.** `fcn_reference.py:118` uses
  `terms.get("coupon_quote_scale", 1.0)` — `1.0`. It only agrees with the production
  path because `payoff.py` happens to write the key explicitly. The agreement is
  accidental, not enforced by any test.

I am not asserting that `10.0` is wrong. I am asserting three narrower things that
the previous version of this page got wrong or omitted:

1. the "it is a percent conversion" justification is **false** (section 5),
2. the value is **not** confined to fixtures — it is the real-deal default, and
3. three code paths in this repository disagree about what the default is.

Only someone who knows the legacy booking convention can settle the value. But the
*disagreement between the three defaults* is a defect this repository can fix on its
own, without knowing anything about the deal.

### And the fixture's `source_ref.job_ids: [0, 1, 2]` is misleading

The legacy reader takes `jobs[-1]` unconditionally (`payoff.py:117`) — the last job,
no selection logic. `0.009642` is picked up because Job 2 happens to be last, not
because it was chosen. Jobs 0 and 1, which have no coupon at all, are silently
discarded. Their placeholder rows are the visible symptom: each carries `N2 = 0`
and a date of 2026-06-01 or 2027-02-01, while only the `COUPON` job has a real
10-row accrual grid.

### One more spec gap: the term sheet requires rounding, the kernel does none

> The Potential Cash Dividend Amount will be rounded to the nearest 0.01, with 0.005
> or above being rounded upwards

`engine.cpp:316` computes `cash = notional * rate` and stops. There is no rounding
anywhere in `engine.cpp` — no `round`, no `floor`, no quantisation to cents. On a
50,000 notional at 0.009642 the raw figure is `482.1000`, so this deal happens to
round to itself. It is still a genuine spec difference, and it will surface as
pennies per period per path on any deal where the raw figure is not already a
multiple of 0.01. At 1,000,000 simulated paths that is a systematic, non-zero
difference in the mean, not noise.

**The exact formula is now known, and it is not the obvious one.** The platform
implements the sentence as

```
CashFlow[i] = Round(Denomination × PayRate[i], 2) × (Notional / Denomination)
```

— `MurexPlaybook/Introduction/Flex_Development.md:161`,
`Products/Range_Accruals/RakiPlus_MemRakiPlus.md:100`,
`Products/Range_Accruals/payoff/raki-plus.md:64`.

**Rounding happens per denomination and is then scaled, which is not the same as
rounding the total**, and the difference is not academic:

| | raw per ELI | per-ELI rounding | × 5 |
|---|---|---|---|
| this deal, one period | 96.420 | 96.42 | **482.10** |
| a period paying 96.425 | 96.425 | 96.43 | **482.15** |
| rounding the total instead | — | — | 482.13 (482.125 → 482.13) |

`KIKOSelect.denomination` is `10000` in this payload, which is the term sheet's
Nominal Amount per ELI, and `notional` is `50000`, so the scaling factor is exactly
5. The full-period coupon reconciles both ways: `50000 × 0.009642 = 482.10`, and
`Round(10000 × 0.009642, 2) × 5 = 96.42 × 5 = 482.10`.

**This is no longer an open question, and it is the cheapest conformance win in the
repository**: the term sheet requires it twice and explicitly, the platform's exact
implementation is documented, the field it needs is already in the payload, and
neither lane does it. It was previously listed as "a four-line change, pending a
product decision". There is no product decision left.

Two smaller conformance notes from the same document, recorded so they are not
rediscovered later:

- **The barrier and the floor are the same level with the same test, and mean
  different things.** Period 1 sets a Barrier of 10% and writes `N/A` for the floor;
  periods 2–9 write `N/A` for the barrier and set a Floor of 10%. Both are the
  worst-performer test at the same 10% level (`lowRange = 0.1` throughout). A
  **barrier** is tested once, on the period end date, and is a cliff — the whole
  period or nothing. A **floor** is tested daily and ramps — `days-in / total days`.
  They are not interchangeable, and the term sheet's `N/A` cells are what say which
  one applies to each period.
- **A knocked-in, memorised asset stays in the basket for the knock-in test.** *"if
  a Reference Asset becomes a Memorised Reference Asset, such Reference Asset remains
  as part of the Reference Basket for the purposes of determining whether a Knock-in
  Event has occurred."* This confirms the graph edge
  `worst_of_performance → knock_in_gate` is correct, and rules out the tempting
  optimisation of removing called assets from the basket.

### Why this is worth stopping for

- **The rate itself is settled.** `RGACCLKO.accruRate` is the only rate in the source
  document, and it traces to `0.9642% ÷ 100` exactly. The rate question is closed.
- **The quote scale is not.** It is the real-deal default, three code paths disagree
  on it, and a wrong value scales the whole coupon leg by ten. This one can move a
  production PV.
- **The example fixtures are what a new reader trusts first.** They are
  schema-validated, internally consistent, and reference a real 162 KB source
  document. A reader has no way to tell which numbers in them are traced and which
  were typed or generated, because nothing records the difference. That is the
  actual defect, and `0.00713` is just where it became visible.
- **The block test cannot catch any of it.** The test asserts the arithmetic
  against the specification and never looks at a deal. This is the whole reason
  `spec_conformance` and `deal_evidence` are separate fields.

### Status — downgraded, and the downgrade is the finding

| Axis | was | is now |
|---|---|---|
| `spec_conformance` | `implemented_and_evidenced` | **`unsupported`** — was `ambiguous_in_source`, which was itself a correction |
| `deal_evidence` | `unresolved` | **`partial`** — rate traced exactly; accrual fraction **not derivable**; quote scale unresolved |
| `lifecycle_state` | `unresolved` | **`unresolved`** — proposed axis, and the finding is much larger than first recorded |

**The downgrade, twice.** The ten tests pass, and they are good tests: hand-derived,
no framework, no market data, not linked to the engine, never compiled with
`-ffast-math`. What they establish is that the kernel does what *this page's
specification* says.

And section 2 shows that half of that specification is a mechanism the platform
forbids for this product configuration. `carried_memory` and `already_paid_fixings`
are live, they change the PV, and the term sheet scopes both of its counts to a
single period. So the label is **`unsupported`**, taken from the same vocabulary as
`fina_risk::EvidenceStatus` and meaning *the block does not implement the
specification — it implements a different one, and this deal is excluded from that
one.*

`ambiguous_in_source` was an intermediate label and it was **too generous**. It said
the source does not resolve the question. The source resolves it three times over.
Recording it as unresolved recorded *our* uncertainty as the *document's* silence,
which is the one thing this book's evidence rules exist to prevent.

**It is still not a claim that the kernel is badly written.** It is a well-built,
well-tested implementation of a real product — the Memory Coupon — that this deal is
documented as excluded from. The defect is that **this code path serves both
products, nothing records which one it is pricing, and the payload carries no field
that could.** Recording `implemented_and_evidenced` here was the single most
misleading thing this book has done; it is left in the table above rather than
deleted, because a reader who trusted it deserves to see where it came from.

### The status of the whole deal, in one table

| # | finding | axis | live? | whose call |
|---|---|---|---|---|
| 1 | the call is switched off in the graph | spec + deal | **yes, on the fixture** | product / code |
| 2 | `pricing.py` discards the call it computes | spec | **yes** | ours — **fixed in stage 1** |
| 3 | coupon carry on, contract latch off | spec | **yes** | product — **now provably ours to remove** |
| 4 | coupon leg ×10, other two legs not | spec | **yes** | ours — three lines |
| 5 | no 0.01 rounding | spec | **yes** | ours — **formula now known, no decision left** |
| 6 | barrier gate ignores the call branch | spec | dormant | product |
| 7 | `coupon.rate` unsourced, unread | deal | no | ours — delete it |
| 8 | 7 unpaid fixings, empty memory | lifecycle | **yes** | **reframed** — see below, the memory is not the problem |
| 9 | `alreadyKnockIn` contradicts itself | deal | **yes** | data |
| 10 | `legacyCouponQuoteScale` absent | deal | **yes** | legacy convention |
| 11 | accrual factor is the complement of the documented one | spec | **yes** | **data — blocked** |
| 12 | `pricing.py:348` multiplies by exactly 1.0 | code | **yes** | ours — delete the line |
| 13 | the fixture holds two as-of dates | lifecycle | **yes** | **the extraction job** |
| 14 | `fixCoupon` is additive, so Fixed/Variable is unmodellable | deal | **yes** | the legacy system, too |

**Seven of the fourteen are ours to fix without asking anyone**, and two of the
remaining seven are blocked on data rather than on judgement — which is a different
and more useful thing to be.

### The third axis: `lifecycle_state`

**This section was wrong about what it was describing, and the correction makes the
finding larger, not smaller.**

It previously said: the last fixing is 17 days before the evaluation date, 7 fixings
of Period 4 sit in between as unpaid, and the memory that would carry them is empty.
That reads like a lifecycle subtlety — a chain that ought to have state and does not.

**There is no chain.** The memory is not a stale state, it is the wrong mechanism
altogether (section 2). An empty memory here is not a missing value; it is a
**correct** empty value, because there is nothing to remember.

What is actually wrong is one level up, and it is a fixture-integrity defect. The
payload contains **two different as-of dates** and the engine mixes them:

| timestamp | value | what it dates |
|---|---|---|
| `createdDatetime` | 2026-04-27 | booking |
| `lastFixingDate` | 2026-08-21 (`46255`) | the last fixing |
| `updatedDatetime` | 2026-08-21 | the deal block |
| `docUpdatedOn`, `extractedSystemDate` | 2026-08-23 | extraction |
| `marketData.evaluationDate` | **2026-09-07** (`46272`) | **the pricing date** |
| `coreVersion` | **2026-09-07** | the engine build |

Four timestamps agree on 21–23 August. Two agree on 7 September. Both lanes discount
from `market.evaluation_date` and read a deal block frozen 15 days earlier. Three
consequences follow directly, and each is checkable:

- **CP4 ended 2026-09-01, six days *before* the evaluation date, yet `N1[4] = 14` of
  21.** Frozen at the August snapshot.
- **CP5 is four sessions underway as of 2026-09-07, yet `N1[5] = 0`.**
- **`GKOLocked = [true, false]` and `GKODate = [46174, 0]` cannot be verified.** If
  AMZN crossed 286.00 on any session in the gap, the note was terminated, and the
  payload would still report `status: LIVE`. The two independent confirmations of
  the flag are consistent with each other — ADBE is above 263.967 and AMZN is below
  286.00 — but consistency is not verification, and the latch is the single most
  load-bearing state in the deal.

**This cannot be fixed by choosing a snapshot, and it cannot be caught by a test.** The
owner is the extraction job. It is recorded here so that every number in this
repository that mixes the two dates is *known* to be provisional — **including the
0.316356 coupon-leg figure produced by stage-1 fix 2**, which is right about the
code and unknown about the data.

The axis is still needed, for the same reason, with a sharper question:

- `spec_conformance` — does the block do what the sentence says?
- `deal_evidence` — can every input be traced to a term sheet or a real system?
- `lifecycle_state` — **is this file internally consistent about when it is?**

- `spec_conformance` — does the block do what the sentence says?
- `deal_evidence` — can every input be traced to a term sheet or a real system?
- `lifecycle_state` — was the engine handed a complete state, or a reconstructed one?

Related, and the same axis: `alreadyKnockIn` contradicts itself across the three
legs. Job 0 (`PUT`) says `false`; jobs 1 (`FUNDING`) and 2 (`COUPON`) say `true`. The
term sheet sets the knock-in observation at the **Final Fixing Date only**
(2027-02-01), which had not occurred at evaluation, so it cannot have knocked in. The
pipeline hand-enters `already_knock_in: false`, contradicting two of the three legs
it claims to read.

### The questions that remain

**One is answered, and it was the cheapest one to answer.**

1. ~~**Should the coupon amount be rounded to 0.01?**~~ **Yes, and the formula is
   known.** The term sheet requires it twice, explicitly. The platform implements it
   as `Round(Denomination × PayRate, 2) × (Notional / Denomination)`, `denomination`
   is `10000` in this payload, and neither lane rounds. Four lines in each lane and a
   test case here. **No product decision was ever required** — the question was
   "yes" the moment the sentence was read, and the only thing missing was the
   formula, which was in the platform documentation all along.
2. **Is `coupon_quote_scale: 10.0` the real booking convention?** Still the
   highest-value open question, because it is the *production* default, not a fixture
   artefact. Only someone who knows the legacy system can answer it. It is a
   **ten-point price quotation** convention, not a percent conversion — so the
   remaining question is narrow: is it the convention the legacy system *booked* by?
3. **Should `coupon.rate` exist in the compiled graph at all?** A field that no
   kernel reads, that has no counterpart in the source system, and whose only
   populated instance in this repository is a generated sample, is a trap with a
   schema wrapped around it. My recommendation is to remove it rather than
   reconcile it — there is nothing to reconcile *to*.
4. **Which fixture numbers are traced, typed, and generated?** Nothing in the
   examples records this, and it is the root cause of findings 7 and 10. A
   `.meta.json` beside each fixture, listing the source field for every pinned
   number, would have made `0.00713` and the `10.0` self-evident on sight — and it
   would have surfaced the two as-of dates in finding 13 immediately.

**And two are now blocking, both on data, neither on judgement:**

5. **What field does the legacy system populate for the in-range day count?** This
   blocks `range_accrual` completely. Not a code question.
6. **Who owns the `termsheet1` fixture, and can they explain the 15-day as-of
   mismatch?** The `RGACCLKO` accrual grid, the `GKOLocked` latch and
   `alreadyKnockIn` all come from the same extraction, and all three are
   self-inconsistent.

I am not answering 2, 3, 5 or 6. They are questions about the deal, the booking
convention and the data, and none is derivable from the code. Until they are answered
this block stays `partial` on deal evidence and `unresolved` on lifecycle, and that
is the correct state to be in rather than a discomforting one.

## 8. The accrual factor — a defect no amount of testing can find

Added after the review. This is the most important finding on the page, and the
reason it is a *finding* rather than a bug is that it is **not** in the kernel.

The kernel is fine. `period_rate` takes a count of qualifying observations and
divides it by the total; `engine.cpp:305` passes a genuine pathwise count. **The two
legacy lanes do not call the kernel, and they inline a different expression:**

| lane | site | expression |
|---|---|---|
| `pricing.py` | `:333,342` | `accrual_fraction = max(N2 - N1, 0) / max(N2, 1)` |
| `fina_risk_cpp.cpp` | `:557-559` | `coupon += 10.0 * rate * max(N2 - N1, 0) / max(N2, 1) * df` |
| `engine.cpp` | `:286,291` | `period_rate(period, qualifying, carried)` — **correct** |

The documented accrual factor is `AccruFactor = N1 / N2`, with `N1` the number of
days the accrual condition is met and `N2` the total days in the period. It is stated
that way in **twelve** platform documents.

**But `N1` in this payload is not that.** It is identical to `fixingsDone` in all nine
rows — so it is days **elapsed**. And there is no in-range day count anywhere:

| period | end | `N1` | `N2` | `fixingsDone` | shipped fraction | what should happen |
|---|---|---|---|---|---|---|
| CP1 | 2026-06-01 | 1 | 1 | 1 | **0.00** | a historical fact: 482.10 was paid |
| CP2 | 2026-07-01 | 21 | 21 | 21 | **0.00** | a historical fact: 482.10 was paid |
| CP3 | 2026-08-03 | 22 | 22 | 22 | **0.00** | a historical fact: 482.10 was paid |
| CP4 | 2026-09-01 | 14 | 21 | 14 | 0.333 | in-range days / 21 |
| CP5–CP9 | future | 0 | 21…19 | 0 | **1.00** | in-range days / N2, per path |

**Three already-paid coupons are valued at zero. Five future coupons are valued at
certainty, so the 10% floor is never tested on a single simulated path.** The
range-accrual feature is absent from the entire forward-looking part of the note.

- Undiscounted cash on a 50,000 notional at 0.009642: **2,571.20 shipped** against
  **1,767.70** under the documented reading. +45.5%.
- At PV level, 30,000 paths, seed 1729: coupon leg **0.316356 → 0.353528** (+11.8%),
  total PV **1.279426 → 1.316598** (+2.9%).

### Why the obvious fix is also wrong

Changing `(N2-N1)/N2` to `N1/N2` is **not a fix**, because `N1` does not mean what
the documentation says. Neither lane can compute the correct answer from this
payload, and for the three elapsed periods the correct answer is a **historical
fact** — the amount actually paid on 2026-06-03, 2026-07-03 and 2026-08-05, 482.10
each, which is 2.9% of notional and is currently valued at nothing. The record does
not hold it.

So the open question is **what the legacy system populates**, and it is a data
question. `range_accrual` is recorded as `blocked_on_data` in the registry, and this
is why: a block whose output is absent from its input has no correct implementation,
only a plausible one.

### And a no-op two lines away

`pricing.py:348`:

```python
# pricing.py:348
amount *= np.minimum(unpaid_fraction / np.maximum(accrual_fraction, 1e-12), 1.0)
```

`accrual_fraction` (`:342`) and `unpaid_fraction` (`:346`) hold **the same
expression**, so this quotient is exactly `1.0` for every period that survives the
guard — and the `max(…, 1e-12)` branch is unreachable for the same reason. Verified
numerically, not by inspection.

This is the **second** instance of the same pattern stage 1 removed at
`pricing.py:358-363`, where `np.where(call_date <= end_step, amount, amount)` had two
identical branches. The signature is *a line that was disabled rather than deleted*,
and it now appears twice in one function. That is worth more than either instance: a
pattern that recurs inside a single function was not a one-off oversight, it was a
habit.

## 9. What to read next

- `range_accrual` — the predicate that decides which days qualify. Smaller than
  this block and the natural second one, but note the trap in its registry entry:
  it is a predicate, and the *counting* is the caller's job, so its test must not
  assert a count.
- `memory_carry` — writes the value this block reads as `carried_memory`, and
  together with `coupon_strip` it forms the carry mechanism. **Read its registry
  entry before reading its kernel**: the mechanism is a real product (Memory Coupon)
  that this deal is *excluded from*, three sources agree it is absent, and the
  fixture propagates the invention into 2000 of 2000 synthetic instruments. The
  recommendation is removal, not reconciliation. The two warnings this page used to
  give — "the term sheet does not describe it" and "the state it needs is missing" —
  were both weaker than the truth: it is not undescribed, it is **forbidden here**,
  and the state is not missing, there is **no such state**.
- [../02-why-there-are-lanes.md](../02-why-there-are-lanes.md) — why this repository
  has five implementations of one payoff, and why that is why findings 1 and 2 in
  section 7 could both be true at once.
- [../03-where-each-block-lives.md](../03-where-each-block-lives.md) — the same
  question asked per block: which lane implements it, and where do the lanes
  disagree. Read `payment_discount` there before trusting any PV in this repository
  that came from the compiled lane.
