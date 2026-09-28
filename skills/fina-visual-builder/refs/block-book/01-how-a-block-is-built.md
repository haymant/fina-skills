# How a block is built, tested, and evidenced

Read this once, before [blocks/coupon-strip.md](blocks/coupon-strip.md). It
describes the method; that page is one block worked through it.

## Why the method exists

This codebase arrived at a block catalogue of 13 kinds that does not describe its
own code. Measured against the C++ kernel, the 13 kinds resolve to 9 distinct
functions:

- **9 block kinds** have a clean, standalone, pure kernel — sitting on 8
  functions, because `cash_settlement` and `physical_delivery_settlement` are one
  function.
- **2 block kinds** (`local_ko_gate`, `global_ko_gate`) map to a function that
  does only part of the work.
- **2 block kinds** (`worst_of_performance`, `payment_discount`) have no kernel at
  all — they are inlined in the pricing loop.

That mismatch is why the blocks are hard to follow. There was nothing stable to
hold onto. The method below is what makes a block stable: a named specification,
a named function, and a test derived from the first and running against the
second.

## The six stages

### 1. Concept

Write one paragraph with no jargon: what does this piece of the payoff *do*, in
terms a structurer would use? If you cannot, you do not yet understand the block
well enough to test it, and that is worth discovering before writing code.

### 2. Specification

Write the sentence a **term sheet** would contain. One sentence. This is the most
important line in the whole process, because it is the only thing that is
independent of the implementation.

A good specification can be checked by a domain expert reading a legal document.
It contains no function names, no code, and no reference to how the code is
organised. If you find yourself writing "the loop over observations", you have
described the implementation, not the specification.

### 3. Registry entry

Write the concept and specification into
[registry/blocks.yaml](registry/blocks.yaml) as a structured record: the typed
input ports, the typed output ports, the state read and written, the kernel
symbol, and — importantly — **what is not in scope**.

The "not in scope" list is the part that prevents the most common failure. A block
is smaller than the concept it is named after. "The coupon" is not one block; it
is a predicate that decides which days qualify, an arithmetic that turns a count
into a rate, a memory step that carries the count forward, and a set of caller
policies about barriers, knock-out, and units. Naming only the arithmetic and
leaving the rest implicit is how a reader ends up multiplying a rate by a notional
twice.

### 4. Kernel

Point at the function. If there is not one, that is a finding, not an obstacle —
see *When a block has no kernel* below.

### 5. Test

Write assertions whose expected values you derived **by hand from the
specification**.

This is the discipline the whole book rests on. There is a tempting way to write
these tests: run the kernel on some inputs, print what comes out, and paste those
numbers into the test. That test passes today and forever, and it detects nothing
at all — including the case where the kernel is wrong. It is a photograph of the
implementation, not a check of the specification.

The correct order is: write the sentence, work out by hand on paper what the
answer must be for a handful of cases, *then* run the test. When it passes you
have learned something, because you could have been wrong.

Good cases to include, in roughly this order:

- **the ordinary case** — a realistic period, a realistic number of fixings
- **the cap** — more qualifying than possible; verify it does not overpay
- **the floor** — fewer qualifying than already paid; verify no negative share
- **the degenerate input** — zero fixings, empty input, boundary value
- **the degenerate configuration** — the feature switched off, so the block
  collapses to something simple
- **the boundary of the range test** — exactly at the barrier, not near it

Compare to a tolerance, not to exact equality. The specification describes a real
number; the kernel computes a `double`. For this reason the test must not be
compiled with `-ffast-math`: a compiler free to reassociate the arithmetic moves
the last bits and silently turns a check of the specification into a check of the
compiler.

### 6. Evidence

Now the hard question, and the one that is always skipped: **can this block's real
inputs be traced to a real deal?**

Trace the value all the way. For a coupon rate that means: which field of which
term sheet, through which transformations, into which kernel argument. If the
chain has a break — a value that is written somewhere, read nowhere, or written in
two places with two different values — then the block's arithmetic may be perfect
and the number in front of you still wrong.

Record this on independent axes, because they fail independently:

| Axis | Question | Vocabulary |
|---|---|---|
| `spec_conformance` | Does the kernel implement the specification? | `implemented_and_evidenced`, `unsupported`, `ambiguous_in_source`, `unresolved` |
| `deal_evidence` | Can the real inputs be traced to a deal? | same vocabulary |
| `lifecycle_state` | **Is the source file internally consistent about when it is?** | `complete`, `stale`, `unresolved` |

A block can be fully tested against its spec and still have unresolved deal
evidence. `coupon_strip` is exactly that case, and conflating the two would have
hidden a live problem behind ten green test cases.

**The third axis was added because the first two ran out of vocabulary.** Neither
"does it match the spec" nor "can I trace the inputs" can express *"this JSON file
contains two different as-of dates and the engine reads both"*. That is not a code
defect and not a traceability break; it is a **data-integrity** defect, and it
invalidates every number derived from the file while leaving the code untouched. A
file can be perfectly traceable — every field maps to a real source — and still be
the wrong file. Check it by reading its *timestamps*, not its contents.

**When the source is a legal document, the same discipline applies to your own
reading of it.** `coupon_strip`'s specification was once recorded as
`ambiguous_in_source` when the term sheet's silence on a carry was mistaken for an
open question. The term sheet was not silent: it scoped both of its counts to a
single period, and the platform's own product documentation went further and
*forbade* the mechanism for this configuration. **`ambiguous_in_source` is a claim
about a document, and it is the easiest claim in this method to make by accident.**
Before you record it, go and look.

When the chain breaks, the output is not a fix. It is **a question, written down,
for someone who can answer it** — and the block is marked `unresolved` until they
do. A block book that reports only green results is worse than no block book,
because it tells you where to stop looking.

## When a block has no kernel

**Four of the 13 blocks** have no standalone function, and they are the four to read
first. `worst_of_performance` is the worst case: **nineteen inline sites across six
lanes**, two of which compute a different quantity, and two more inside the *same*
function about fifty lines apart with different side effects.

(The count "twice" appears in an earlier version of this page, and it counted
`engine.cpp` alone. A block's footprint is a property of the repository, not of the
file that happens to hold one copy of it.)

You cannot test an inlined expression without a kernel to call. So the honest
options are:

1. **Extract it.** Pull the expression into a named pure function, call it from
   both sites, and test that. This is the right fix, and it is small — a
   five-line function. It is *not* a refactor of the pricing loop.
2. **Record it as untestable** and carry the gap visibly, so nobody builds an
   assumption on top of it.

The wrong option is to write a test that reconstructs the expression in the test
file. That tests the test's copy, not the product.

Extracting a kernel is always safe when the function is pure, and the
extract-then-test order matters: extract, confirm the existing pricing tests still
pass unchanged, and only then write the new block test. The existing tests are
what tell you the extraction did not change a number.

## Why the registry has to be the source, not a summary

The failure mode this method exists to prevent: the block catalogue, the kernel
bindings, and the diagrams each describe the blocks independently, and drift.

That drift is already in the repository, and it was fixed by stage 1. `local_ko_gate`
is listed in the schema's kind enum, listed in the kernel bindings, and drawn in the
target diagram — and the emitter could never produce it, so a feature flag derived
from its presence was permanently `false` for **every deal in the system**, including
the ones that had a local call. A reader of the diagram would reasonably conclude the
block was available, and would have been wrong.

**The emitter is the authority on what a diagram can show.** An entry in a kind enum
is a claim about a vocabulary, and a vocabulary can outrun its producer. When a
catalogue, a binding, and a diagram all agree and the producer disagrees, check the
producer first: it is the only one of the four that runs.

The fix is structural rather than editorial. If the palette, the kernel bindings,
the diagrams, and the tests are all *generated* from one registry, then a block
cannot be advertised without a kernel and a test, because there is nowhere else to
write it down. That is the only version of this that survives contact with a
deadline.

## How this book cites code, and how that is kept true

A book about code that cites code by line number has a maintenance problem, and
this one had it badly. An audit of all 122 code citations found **39 that pointed
at the wrong line** — not all off by a line or two:

These four are kept **as they were written**, so the record survives. Do not
re-pin them; a citation that is still wrong is a different mistake from one
that has been quietly corrected.

| cited as written | what is actually there | what it claimed |
|---|---|---|
| `fina_risk_cpp.cpp:613-624` | `:613` is the `steady_clock` tutorial comment | the global-KO test the book quotes at length |
| `engine.cpp:301` | the invalid-fixing guard | the `state.unpaid_coupon` write |
| `daily_termsheet.py:267` | the global-KO test | the discount-rate read |
| `payoff.py:542` | a blank line | where `local_enabled` is derived |

The reason none of this was noticed is that the surrounding prose keeps reading
correctly long after the line number stops being true. Nobody re-reads a claim
they have already read three times.

The fix is mechanical and it is now enforced:

1. **Every code block that quotes source carries a `file:line-range` header** as
   its first line, and the quoted text is **verbatim** — not tidied, not renamed,
   not reflowed past recognition. An earlier draft of this page quoted the
   mechanism-A latch with `performance` shortened to `perf` and `underlying` to
   `u`; presented as a quotation, that is a fabrication, and nobody had noticed.
   Abridged quotes say so, in the header and in the prose.
2. **A checker verifies every one of those headers against the tree.** It
   whitespace-normalises both sides, so rewrapping a long line is fine, and it
   fails if a quoted line is not inside the cited range. A block whose header
   does not parse as a citation is skipped rather than trusted, so adding a quote
   without a header is visible as a drop in the checked count.
3. **Line numbers elsewhere in the prose are pinned to the tree as it stands**,
   and drift there is a known open cost. When the engine changes, the blocks
   fail loudly; the parenthetical citations need an audit. That asymmetry is
   deliberate: the claims worth checking are the ones a reader can act on.

The rule for anyone adding to this book: **if you are going to quote a line,
cite it in a way that can be checked.** A quotation without a checkable header
is an assertion about code that only the author can verify, and the author has
already been wrong 39 times.

## What this method does not do

It does not validate the **model layer** — volatility, correlation, simulation. The
block tests start from a path cube and are silent about how it was produced. So a
green block suite and a wrong PV can coexist, and when they do, the problem is
upstream of everything in this book.

The rule that follows: **when a PV looks wrong, split the question in two before
looking at any code.** Is the cube right? Then: is the payoff right? The block
book answers only the second question, and it answers it well.
