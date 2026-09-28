# Glossary

The vocabulary you need before the block pages make sense. No code in this file.
Every term is defined the way a structurer would use it, not the way a
mathematician would define it.

Read this once. Skip it afterwards.

---

## The instrument

**Structured product.** A note issued to an investor whose payoff is *built* from
standard pieces — a loan that repays principal, plus an option that pays if
something goes wrong, plus a coupon that pays if nothing goes wrong — rather than
a single monolithic payoff. This codebase prices one family of these: **FCN**,
"fixed coupon note", a range-accrual note on a basket of shares.

**Basket.** The set of shares the note is written on. Two shares, five shares,
ten — the note references a specific combination.

**Worst-of (WPS, "worst performer").** The single share in the basket that
performed *worst* over the life of the note. Every barrier, range, and payoff in
these notes is measured against the worst performer, not against the average. This
is the single most important convention in the whole codebase: if you understand
nothing else, understand that **the product only ever looks at the worst
performer of the basket.**

**Reference price / initial fixing.** The price of each share on the start date.
Performance is always measured *relative to this*, not in absolute terms. A share
at 100 that goes to 70 has performed at 0.70. A share at 200 that goes to 140 has
also performed at 0.70.

**Fixing.** One observation of the basket on one day. "5 fixings in the period"
means 5 days on which the basket was measured. The count of fixings is a
*count*, never a rate — this distinction causes real confusion and is worth
holding onto.

**Accrual period.** A stretch of time between coupon dates, e.g. one quarter.
Each period has its own number of fixings and pays its own coupon.

---

## The payoff pieces

**Coupon.** The periodic payment. In a *range-accrual* coupon, the payment depends
on how the worst performer behaved during the period.

**Range.** A band of performance, e.g. 80% to 100% of the reference price. A
*fixing* is **in range** if the worst performer sat inside the band that day.

**The band can be one-sided.** The example deal has no upper bound at all: the term
sheet writes "N/A" in that column, and the only live bound is a 10% floor. So do not
assume a range has two ends. A missing upper bound reaches the code as the sentinel
`999.99`, which means "no upper bound" in this legacy system and which the current
pipeline passes through as an ordinary number.

**Range accrual.** Counting the days the worst performer was in range, and paying
proportionally. No in-range days, no coupon. All days in range, full coupon.

**Fixed rate.** A rate paid regardless of performance, before the range part is
added.

Careful with this one. A term sheet can and does agree a real fixed rate — the
example deal has a **Fixed Cash Dividend Rate of 0.9642%**, the same as its day-in
rate. A zero fixed rate in this codebase usually does **not** mean "no fixed rate was
agreed". It usually means the legacy engine routed the fixed coupon through the
accrual grid instead of through the dedicated field, and left that field at zero. See
[blocks/coupon-strip.md](blocks/coupon-strip.md) section 3.

**Range rate.** The rate that is earned in proportion to the in-range days. This
is the part that varies.

**Memory — and this word means two unrelated things.** Read carefully, because
getting them backwards is the single most expensive confusion in this codebase, and
because the product is *named* after one of them.

**1. The contract's memory: a termination latch.** Each share is permanently
*stamped* the first time it trades at or above the call price (110%). When every
share has been stamped, the note is called and dies. The coupons play no part. This
is what "Memory" means in the term sheet, 82 times, and in the product's own name.

**2. The engine's memory: an unpaid-coupon carry.** If a period earns no coupon, the
unpaid days are added to the next period's count, so a bad period is not simply
lost. This is what the block book calls "memory carry", and it is what
`coupon_memory` and `carried_memory` mean in the code.

| | contract's memory | engine's memory |
|---|---|---|
| what is remembered | which shares hit 110% | how many days earned nothing |
| what it does | ends the note | raises a later coupon |
| in the term sheet? | **yes** | **no** — and forbidden here |
| its real name | "Memory" (in the product name) | "Memory Coupon" (a different product) |

**Neither of these was mysterious. Mechanism 2 is a real platform product**,
documented in the MurexPlaybook, and this repository implements it correctly. **The
defect is narrower and more embarrassing than a misreading: the platform's own
documentation says Memory Coupon is mutually exclusive with Global KO, and the
example deal has Global KO.** A carry also needs a separate Coupon Barrier field to
read, and the payload has none. So the deal's fixture sets the two mechanisms exactly
backwards — latch off, carry on — and a third flag, `unpaidPeriodRule`, propagates the
carry into 2000 of 2000 synthetic benchmark instruments with no consumer anywhere.

The glossary entry below describes mechanism 2, because that is what the code
implements. It is a description of a product this note did not buy.

**Accrual factor.** The share of a period's days on which the coupon is earned, as a
number between 0 and 1. The platform's formula is `N1 / N2`, where `N1` counts the
days *in range* and `N2` the days in the period. **Both legacy lanes compute
`(N2 - N1) / N2` instead**, which is the complement — and the payload's `N1` is days
*elapsed*, not days in range, so neither expression is right. See
[blocks/coupon-strip.md](blocks/coupon-strip.md) section 8.

**Carry (memory carry).** The engine-side mechanism above: unpaid days rolled into
the next period. On or off per note, and on by default in this codebase — which is
what makes it dangerous, since "on by default" is indistinguishable from "in the
contract" unless you go looking.

**Unpaid fixings.** The count of fixings that qualified but have not yet been
paid, carried forward while memory is on. **This is a count of days, not a
money amount and not a rate.** Confusing it with either is the most common
misreading of the coupon block.

**Principal return / notional return.** Repayment of the original investment at
maturity. A fixed rate, unrelated to performance.

---

## The triggers

**Knock-in (KI).** A barrier that, once crossed, switches on an option the
investor would not otherwise have. The note is "knocked in" when the worst
performer trades at or below the knock-in barrier.

**Barrier.** A price level that switches a feature on or off. `0.70` means "70% of
the reference price".

**European knock-in (EKI).** The barrier is checked **only on the final fixing
date** — the last day. Not during the life of the note.

**Knock-out (KO).** A barrier that ends the note early. "Call" is a common name
for it.

**Global KO.** The note is knocked out when **every** share in the basket is
above the barrier. This is a joint condition, so it is sensitive to how the
shares move *together* — which is what correlation measures.

**Local KO.** The note is knocked out when **any single** share breaches its own
barrier.

**Same-day KO precedence.** When the local and global KO both trigger on the same
day, which one is recorded as having fired. This is a *policy* choice, and it is
currently hard-coded rather than configured — see the open questions in
[coupon-strip.md](blocks/coupon-strip.md).

**Coupon barrier.** A separate, lower barrier. If the worst performer finishes the
period below it, the period earns only the fixed rate and earns no range accrual
at all, and the whole period is remembered as unpaid.

**Barrier and floor are the same level doing different jobs, and the difference is
worth holding onto.** Both ask the same question — is the worst performer at or
above 10%? — but they ask it on a different schedule:

| | tested | result |
|---|---|---|
| **Barrier** | once, on the period end date | a cliff: the whole period pays, or none of it |
| **Floor** | every day of the period | a ramp: you earn `days that qualified / days in the period` |

So "no floor applies" and "no barrier applies" are not the same sentence. The first
means nothing is counted daily. The second means nothing is tested at the end. The
example deal uses the barrier for period 1 and the floor for periods 2–9, at the
same 10% level, and the term sheet writes "N/A" in the unused column each time.

**On a call, the coupon barrier is skipped.** If the note is called early, the term
sheet pays a time-prorated fixed amount *without* testing the barrier at all. The
kernel has no such branch — it gates the whole rate on the barrier whether or not
the note was called. That is currently harmless only because nothing ever sets the
barrier field, so it is a defect waiting for the field to be filled in.

---

## The numbers

**Notional.** The size of the trade, e.g. 50,000. Legs are computed *per unit of
notional*, so the notional is used for scaling and then divided back out.

**PV (present value).** What the note is worth today: the expected value of all its
future cash flows, discounted. In this codebase the legs are per-unit-notional, so
a PV of 1.23 means 1.23 per unit of notional — **always check the unit before
comparing a PV to anything**, including to another PV.

**Path.** One simulated possible future of the basket, day by day, for every
share. A pricing run is many thousands of paths; the PV is the average over them.

**Path cube.** The stored array of all paths, shape (paths × days × shares). The
pricing engine is handed a finished cube and does not generate it — which is why
the model layer and the payoff layer can be checked separately, and why a
suspicious PV usually has to be split into "is the cube right?" and "is the
payoff right?" before you can look at it.

**Simulation.** Inventing the paths, from a volatility and a correlation
assumption. Not the same thing as pricing.

**Kernel.** The small function that actually computes one thing. If a block has a
kernel, that function can be called on its own with no simulation, no market data,
and no server. That is the property this book depends on.

**Block.** One payoff-graph piece with a defined input, a defined output, and a
kernel. Nine of the thirteen catalogue blocks have one — sitting on eight distinct
functions, because two of the settlement blocks share a single function. Two more
map onto a function that only does part of the job, and two have no kernel at all.

**Evidence status.** The label on how much is actually known about a block. The
scale is borrowed from `fina_risk::EvidenceStatus` so there is one vocabulary:
`implemented_and_evidenced`, `partial`, `unsupported`, `ambiguous_in_source`,
`unresolved`. These are honest labels, not grades — `unresolved` on a real block is
the correct state, and is better than a green tick that nobody can defend.

---

## The three layers

**Model layer.** Shared across products: which numerical method, which
calibration, which evidence is required before a result may be published. A
violation or correlation assumption lives here.

**Template layer.** The *topology* — which blocks exist and how they are wired.
Shared by every trade of the same structural type. This is what the "target DAG"
diagrams in [../../SKILL.md](../../SKILL.md) draw.

**Trade layer.** One deal: which blocks are switched on, what the barriers and
rates are, and what has already happened to the note. A trade is a *binding*, not
a new model and not a new template.

The rule that follows: **a different barrier, rate, strike, schedule, or basket
member is trade data and never justifies a new model or a new template.** Only a
new block kind earns a new template.

The target-topology diagrams referred to throughout this book are in
[../../SKILL.md](../../SKILL.md).
