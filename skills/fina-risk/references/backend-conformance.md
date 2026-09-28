# Backend conformance

For each product-family fixture compare oracle and compiled outputs across lifecycle dates, barriers, fixings, corporate actions, PV/cashflows, and sensitivities. Store tolerances and model version beside the fixture. A mismatch is a semantic or implementation defect until explained.

## Coupon as-of convention (termsheet1 fixture)

The fixture's coupon leg follows two conventions that a conforming backend must reproduce (block-book block `coupon_strip`, corrections 7 and 8):

1. **An owed period is counted in full.** `N1` (fixings done) is a status marker, not an amount share. A period with any outstanding fixing (`N1 < N2`) pays the whole periodic coupon even when only part of it was fixed by the as-of snapshot — the in-flight 1-Sep period (end 2026-09-01, payment 03-Sep, `N1=14/N2=21`) is fixed-but-unpaid at the 07-Sep evaluation and counts the full `0.9642%`, not `(21-14)/21`. Settled rows (`N1 == N2`) are "already paid, forgotten in the pricing request" and owe nothing.
2. **The callable gate truncates coupons, not just the put.** A period that ended before the call pays in full; the period containing the call pays the fixings up to and including the call (`span`/`elapsed` pro-rata); a period starting after the call pays nothing. Both legacy lanes (`pricing.py`, `fina_risk_cpp.cpp` `price_fixture`) apply it and agree to ~0.1% (coupon 0.380634 vs 0.381160 at 30k paths, seed 1729); the coupon is expressed in the legacy ten-point quote scale (`×10`) while funding/put legs are per-unit.
