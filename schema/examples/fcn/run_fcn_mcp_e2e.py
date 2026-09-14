#!/usr/bin/env python3
"""Run the FCN sample through the local FinA scheduler and real pricer MCP tool."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
FINA_ROOT = REPO_ROOT.parent / "FinA"
RISK_ROOT = REPO_ROOT.parent / "fina-risk"
TRADE_ROOT = REPO_ROOT.parent / "fina-trade"
for path in (FINA_ROOT / "python", TRADE_ROOT, RISK_ROOT / "src"):
    sys.path.insert(0, str(path))

from fina_core.integrations import register_fina_handlers
from fina_core.process_scheduler import SchedulerService
from fina_risk import mcp
from fina_trade import TradeRepository


def unwrap_tool_result(value: Any) -> dict[str, Any]:
    """Normalize FastMCP direct-call results without hiding tool errors."""
    if isinstance(value, dict):
        return value
    structured = getattr(value, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    if isinstance(value, tuple) and value:
        return unwrap_tool_result(value[0])
    if isinstance(value, list):
        for item in value:
            text = getattr(item, "text", None)
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, dict):
                    return parsed
            candidate = getattr(item, "model_dump", lambda: None)()
            if isinstance(candidate, dict) and isinstance(candidate.get("structuredContent"), dict):
                return candidate["structuredContent"]
    raise TypeError(f"unexpected MCP result type: {type(value).__name__}: {value!r}")


def call_pricer(request: dict[str, Any], paths: int, seed: int) -> dict[str, Any]:
    async def invoke() -> Any:
        return await mcp.call_tool(
            "pricing_and_sensitivity",
            {"request": request, "paths": paths, "seed": seed},
        )

    return unwrap_tool_result(asyncio.run(invoke()))


def run(termsheet_path: Path, paths: int, seed: int) -> dict[str, Any]:
    request = json.loads(termsheet_path.read_text(encoding="utf-8"))
    scheduler = SchedulerService()
    trades = TradeRepository()
    pricing_calls: list[dict[str, Any]] = []

    def pricing_tool(payload: dict[str, Any]) -> dict[str, Any]:
        pricing_calls.append(payload)
        request_without_event = {k: v for k, v in payload.items() if k != "lifecycle_event"}
        result = call_pricer(request_without_event, paths=paths, seed=seed)
        return {
            "PV": result["base"]["valuation"]["pv"],
            "PV_currency": result["base"]["valuation"].get("currency", "USD"),
            "price_pct_of_notional": result["base"]["valuation"].get("price_pct_of_notional"),
            "RiskCube": result["risk_representation"],
            "mcp_tool": "pricing_and_sensitivity",
        }

    def grouped_olap(payload: dict[str, Any]) -> dict[str, Any]:
        quote = payload["latest_reprice"]["quote"]
        cells = quote.get("RiskCube", {}).get("long", [])
        deltas = [float(cell.get("value", 0.0)) for cell in cells if str(cell.get("greek", "")).upper() == "DELTA"]
        return {
            "group_by": "product_type",
            "rows": [{"product_type": "ELIFCN_KI", "trade_count": len(payload["trades"]), "avg_delta": sum(deltas) / len(deltas) if deltas else 0.0}],
            "source": "reprice.RiskCube.long[greek=DELTA]",
        }

    register_fina_handlers(
        scheduler,
        pricing_callable=pricing_tool,
        trade_repository=trades,
        olap_callable=grouped_olap,
    )
    trade_id = "FCN-TERMSHEET1-E2E"
    definition = {
        "api_version": "fina/v1",
        "kind": "FinaProcess",
        "metadata": {"name": "termsheet1-fcn-rfq-to-risk"},
        "parameters": {"pricing_request": request, "trade_id": trade_id, "correlation_id": "termsheet1-fcn-e2e"},
        "threads": [
            {"name": "quote", "handler": "fina-pricer.pricing_and_sensitivity", "parameters": {"trade_id": trade_id}},
            {"name": "register_trade", "handler": "fina-trade.register", "depends_on": ["quote"], "parameters": {"trade": {"trade_id": trade_id, "instrument_id": "ELIFCN_KI_FINA1", "product_type": "ELIFCN_KI", "notional": 1000000.0, "currency": "USD", "status": "LIVE"}}},
            {"name": "amend", "handler": "fina-trade.amend", "depends_on": ["register_trade"], "parameters": {"trade_id": trade_id, "changes": {"observation_date": "2026-10-14"}, "reason": "termsheet1-fcn-e2e"}},
            {"name": "reprice", "handler": "fina-pricer.pricing_and_sensitivity", "triggered_by": "trade.lifecycle.amended", "parameters": {"trade_id": trade_id}},
            {"name": "olap", "handler": "fina-olap.group_sensitivities", "depends_on": ["reprice"]},
        ],
        "subscriptions": [{"topic": "trade.lifecycle.amended", "handler": "fina-pricer.pricing_and_sensitivity", "start_thread": "reprice"}],
    }
    process = scheduler.create_process(definition)
    if process.state != "FINISHED" or trade_id not in trades.trades:
        snapshot = scheduler.snapshot(process.id)[0]
        summary = {"state": snapshot["state"], "threads": [{"name": t["name"], "state": t["state"], "error": t["error"]} for t in snapshot["threads"]]}
        raise RuntimeError(json.dumps({"snapshot": summary, "pricing_calls": len(pricing_calls), "trade_events": trades.events}, indent=2, default=str))
    trade = trades.get(trade_id)
    olap = scheduler.result(process.id, "olap")
    events = [event["topic"] for event in trades.events]
    assert process.state == "FINISHED", scheduler.snapshot(process.id)[0]
    assert len(pricing_calls) == 2, f"expected 2 real MCP pricing calls, got {len(pricing_calls)}"
    assert trade["status"] == "AMENDED", trade
    assert "trade.lifecycle.amended" in events, events
    assert scheduler.result(process.id, "reprice")
    assert olap["rows"][0]["trade_count"] == 1, olap
    return {"process_id": process.id, "process_state": process.state, "pricing_calls": len(pricing_calls), "trade_status": trade["status"], "events": events, "olap": olap, "mcp_tool": "pricing_and_sensitivity", "sample": "ELIFCN_KI_FINA1"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--termsheet", type=Path, default=HERE / "termsheet1.fcn.sample.json")
    parser.add_argument("--paths", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(run(args.termsheet, args.paths, args.seed), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
