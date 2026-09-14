#!/usr/bin/env python3
"""Execute the schema-defined FCN flow from legacy term sheet through ETL to OLAP."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
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
from fina_core.process_scheduler import render_parameters
from fina_risk import mcp
from fina_trade import TradeRepository


def unwrap(value: Any) -> dict[str, Any]:
    """Decode the installed FastMCP direct-call result into a JSON object."""
    if isinstance(value, dict):
        return value
    if isinstance(value, tuple) and value:
        return unwrap(value[0])
    structured = getattr(value, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
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
            dumped = getattr(item, "model_dump", lambda: None)()
            if isinstance(dumped, dict) and isinstance(dumped.get("structuredContent"), dict):
                return dumped["structuredContent"]
    raise TypeError(f"unexpected MCP result type: {type(value).__name__}")


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async def invoke() -> Any:
        return await mcp.call_tool(name, arguments)

    return unwrap(asyncio.run(invoke()))


def run(termsheet_path: Path, count: int, seed: int, paths: int) -> dict[str, Any]:
    scheduler = SchedulerService()
    trades = TradeRepository()
    etl_calls: list[str] = []
    pricing_calls: list[str] = []
    trade_id = "FCN-TERMSHEET1-ETL-E2E"
    instrument_id = "ELIFCN_KI_TERMSHEET1"

    with tempfile.TemporaryDirectory(prefix="fina-fcn-etl-") as work:
        work_dir = Path(work)

        def augment(thread: Any, runtime: SchedulerService) -> dict[str, Any]:
            etl_calls.append("run_etl_task:augment")
            result = call_tool(
                "run_etl_task",
                {"mode": "augment", "termsheet": str(termsheet_path), "count": count, "seed": seed},
            )
            variants = result.get("instruments", [])
            if len(variants) != count:
                raise AssertionError(f"ETL augment returned {len(variants)} variants, expected {count}")
            return {"status": "ok", "mode": "augment", "count": len(variants), "variants": variants}

        def compile_requests(thread: Any, runtime: SchedulerService) -> dict[str, Any]:
            etl_calls.append("run_etl_task:compile")
            variants = runtime.result(thread.process_id, "augment")["variants"]
            # Feed the actual augmented output into the next MCP ETL stage.
            variant_path = work_dir / "augmented-termsheet.json"
            variant_path.write_text(json.dumps(variants[0]), encoding="utf-8")
            result = call_tool(
                "run_etl_task",
                {"mode": "compile", "termsheet": str(variant_path), "count": 1, "seed": seed, "validate": True},
            )
            requests = result.get("requests", [])
            if len(requests) != 1:
                raise AssertionError(f"ETL compile returned {len(requests)} requests")
            return {
                "status": "ok",
                "mode": "compile",
                "count": 1,
                "requests": requests,
                "legacy_termsheet_path": str(variant_path),
                "instrument_key": requests[0]["instrument_key"],
            }

        def pricing(thread: Any, runtime: SchedulerService) -> dict[str, Any]:
            pricing_calls.append("pricing_and_sensitivity")
            compile_result = runtime.result(thread.process_id, "compile")
            legacy = json.loads(Path(compile_result["legacy_termsheet_path"]).read_text(encoding="utf-8"))
            result = call_tool(
                "pricing_and_sensitivity",
                {"request": legacy, "paths": paths, "seed": seed},
            )
            return {
                "trade_id": thread.parameters.get("trade_id", trade_id),
                "quote": {
                    "PV": result["base"]["valuation"]["pv"],
                    "PV_currency": result["base"]["valuation"].get("currency", "USD"),
                    "RiskCube": result["risk_representation"],
                    "mcp_tool": "pricing_and_sensitivity",
                    "instrument_key": compile_result["instrument_key"],
                },
                "trigger": thread.parameters.get("event"),
            }

        def grouped_olap(payload: dict[str, Any]) -> dict[str, Any]:
            quote = payload["latest_reprice"]["quote"]
            rows = quote.get("RiskCube", {}).get("long", [])
            deltas = [float(row.get("value", 0.0)) for row in rows if str(row.get("greek", "")).upper() == "DELTA"]
            return {
                "group_by": "product_type",
                "rows": [{
                    "product_type": "ELIFCN_KI",
                    "trade_count": len(payload["trades"]),
                    "avg_delta": sum(deltas) / len(deltas) if deltas else 0.0,
                }],
                "source": "reprice.RiskCube.long[greek=DELTA]",
            }

        register_fina_handlers(
            scheduler,
            pricing_callable=lambda _: {"status": "placeholder"},
            trade_repository=trades,
            olap_callable=grouped_olap,
        )
        # Replace only the pricing adapter with the MCP-backed implementation;
        # trade, lifecycle, subscription, and OLAP adapters remain canonical.
        scheduler.register_handler("fina-pricer.pricing_and_sensitivity", pricing)
        scheduler.register_handler("fina-etl.augment_termsheet", augment)
        scheduler.register_handler("fina-etl.compile_pricing_requests", compile_requests)

        definition = json.loads((HERE / "fcn-etl-to-olap.process.json").read_text(encoding="utf-8"))
        definition = render_parameters(
            definition,
            {
                "termsheet_path": str(termsheet_path),
                "count": count,
                "seed": seed,
                "paths": paths,
                "correlation_id": "termsheet1-fcn-etl-e2e",
                "trade_id": trade_id,
                "instrument_id": instrument_id,
            },
        )
        process = scheduler.create_process(definition)
        snapshot = scheduler.snapshot(process.id)[0]
        if process.state != "FINISHED" or trade_id not in trades.trades:
            summary = {"state": snapshot["state"], "threads": [{"name": t["name"], "state": t["state"], "error": t["error"]} for t in snapshot["threads"]]}
            raise RuntimeError(json.dumps({"snapshot": summary, "etl_calls": etl_calls, "pricing_calls": pricing_calls}, indent=2, default=str))
        trade = trades.get(trade_id)
        olap = scheduler.result(process.id, "olap")
        events = [event["topic"] for event in trades.events]
        assert len(etl_calls) == 2, etl_calls
        assert etl_calls == ["run_etl_task:augment", "run_etl_task:compile"], etl_calls
        assert len(pricing_calls) == 2, pricing_calls
        assert trade["status"] == "AMENDED", trade
        assert "trade.lifecycle.amended" in events, events
        assert scheduler.result(process.id, "reprice")
        assert olap["rows"][0]["trade_count"] == 1, olap
        return {
            "process_id": process.id,
            "process_name": snapshot["name"],
            "process_state": process.state,
            "graph": [thread["name"] for thread in snapshot["threads"]],
            "etl_calls": etl_calls,
            "pricing_calls": len(pricing_calls),
            "compiled_instrument_key": scheduler.result(process.id, "compile")["instrument_key"],
            "trade_status": trade["status"],
            "events": events,
            "olap": olap,
            "sample": termsheet_path.name,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--termsheet", type=Path, default=HERE / "termsheet1.fcn.sample.json")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--paths", type=int, default=128)
    args = parser.parse_args()
    print(json.dumps(run(args.termsheet, args.count, args.seed, args.paths), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
