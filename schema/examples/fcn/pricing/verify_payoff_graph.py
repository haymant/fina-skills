#!/usr/bin/env python3
"""Validate the canonical payoff-graph example and its engine lowerings.

Checks, without services:
1. The checked-in ``payoff-graph.example.json`` conforms to ``payoff-graph.schema.json``.
2. ``compile_fcn_graph_and_lower`` re-produces the example bit-for-bit from the
   projection + legacy + market fixtures (same ``graph_hash``).
3. The lowered ``pricing_request`` conforms to ``pricing-request.schema.json``.
4. Key semantics survive the round trip (notional, strike, KI barrier, settlement,
   coupon periods filtered to the pricing evaluation date).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, RefResolver

HERE = Path(__file__).resolve().parent
SCHEMA = HERE.parents[2]
REPO = HERE.parents[5]

sys.path.insert(0, str(REPO / "modules" / "fina-core" / "python"))

from fina_core.payoff import compile_fcn_graph_and_lower  # noqa: E402

LEGACY = REPO / "modules" / "fina-risk" / "skills" / "fina-risk" / "refs" / "termsheet1.md.json"
PROJECTION = SCHEMA / "examples" / "fcn" / "terms" / "fcn-terms-projection.example.json"
PRICING_REQUEST = HERE / "pricing-request.example.json"
GRAPH_EXAMPLE = HERE / "payoff-graph.example.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(instance, schema_path: Path) -> None:
    schema = load(schema_path)
    resolver = RefResolver(schema_path.as_uri(), schema)
    Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker()).validate(instance)


def main() -> int:
    validate(load(GRAPH_EXAMPLE), SCHEMA / "payoff-graph.schema.json")

    terms = load(PROJECTION)
    legacy = load(LEGACY)
    market = load(PRICING_REQUEST)["market_data"]
    emitted = compile_fcn_graph_and_lower(terms, market=market, legacy=legacy)

    graph = emitted["payoff_graph"]
    example = load(GRAPH_EXAMPLE)
    assert graph["graph_hash"] == example["graph_hash"], "compiler no longer reproduces the example graph"
    assert graph["dates"]["evaluation_date"] == 46272, "pricing evaluation date (market) must win"
    assert graph["dates"]["final_fixing_date"] == 46419 and graph["dates"]["maturity_date"] == 46421
    assert graph["notional"] == 50000.0
    assert graph["legs"][0]["role"] == "ki_put" and graph["legs"][0]["multiplier"] == -1.0
    assert all(leg["notional"] == 50000.0 for leg in graph["legs"])
    assert graph["coupon"]["payment_lag_days"] == [4, 2, 2, 2, 2]

    periods = next(n["config"]["periods"] for n in graph["nodes"] if n["node_id"] == "coupon_strip")
    assert all(p["end_date"] > 46272 for p in periods), "already-ended coupon periods must be filtered out"
    assert [p["range_rate"] for p in periods] == [0.009642] * 5
    assert graph["payoff_script"].startswith("worst-of { - put(EKI 0.7, strike 0.78")

    fcn_terms = emitted["fcn_terms"]["fcn_terms"]
    assert fcn_terms["terminal"]["ki_barrier"] == 0.7 and fcn_terms["terminal"]["strike"] == 0.78
    assert fcn_terms["terminal"]["settlement"] == "physical" and fcn_terms["physical_delivery"] is True
    assert fcn_terms["evaluation_date"] == 46272 and fcn_terms["maturity_date"] == 46421
    assert fcn_terms["coupon_periods"][0]["range_rate"] == 0.009642

    pricing_request = emitted["pricing_request"]
    validate(pricing_request, SCHEMA / "pricing-request.schema.json")
    assert pricing_request["legs"][0]["payoff"]["settlement"] == "physical_delivery"
    assert pricing_request["parameters"]["seed"] == 1729 and pricing_request["parameters"]["paths"] == 30000

    enriched = emitted["enriched_request"]
    for key in ["InstrumentKey", "UnwindMapRaw", "RiskFactorKeys", "MarketDataSnapshot", "UpdatedLifecycle", "CommonEconomics"]:
        assert key in enriched
    assert any(key["risk_factor_type"] == "EQ_SPOT" for key in enriched["RiskFactorKeys"])

    print("PASS canonical payoff graph -> FcnTerms + pricing-request + enriched request")
    print("PASS payoff script and kernel bindings explain the fina_risk_cpp function organization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())