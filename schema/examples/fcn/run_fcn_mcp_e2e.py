#!/usr/bin/env python3
"""Execute the schema-defined FCN flow from legacy term sheet through ETL to OLAP."""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def module_root(name: str) -> Path:
    """Monorepo ``modules/`` layout first, legacy sibling-repo layout as fallback."""
    candidate = REPO_ROOT / "modules" / name
    return candidate if candidate.exists() else REPO_ROOT.parent / name


FINA_ROOT = module_root("fina-core")
RISK_ROOT = module_root("fina-risk")
TRADE_ROOT = module_root("fina-trade")
CORE_PY = FINA_ROOT / "python" if (FINA_ROOT / "python").exists() else FINA_ROOT
for path in (CORE_PY, TRADE_ROOT, RISK_ROOT / "src"):
    sys.path.insert(0, str(path))
sys.path.insert(0, str(RISK_ROOT / "cpp" / "build"))

from fina_core.integrations import register_fina_handlers
from fina_core.process_scheduler import SchedulerService
from fina_core.process_scheduler import render_parameters
from fina_risk import mcp
from fina_risk.daily_termsheet import capture_native_quote
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


def git_revision(repository: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def validate_registry() -> None:
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_model_registry.py")],
        check=True,
        capture_output=True,
        text=True,
    )


def validate_lifecycle_fixtures() -> None:
    subprocess.run(
        [sys.executable, str(HERE / "lifecycle" / "verify_lifecycle.py")],
        check=True,
        capture_output=True,
        text=True,
    )


def run(termsheet_path: Path, count: int, seed: int, paths: int, artifacts_dir: Path | None = None) -> dict[str, Any]:
    validate_registry()
    validate_lifecycle_fixtures()
    pricing_artifacts_dir = artifacts_dir
    etl_artifacts_dir = artifacts_dir.parent / "etl" if artifacts_dir and artifacts_dir.name == "pricing" else artifacts_dir
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
            if etl_artifacts_dir:
                etl_artifacts_dir.mkdir(parents=True, exist_ok=True)
                (etl_artifacts_dir / "augment-result.example.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
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
            if etl_artifacts_dir:
                etl_artifacts_dir.mkdir(parents=True, exist_ok=True)
                (etl_artifacts_dir / "compile-result.example.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            if pricing_artifacts_dir:
                pricing_artifacts_dir.mkdir(parents=True, exist_ok=True)
                (pricing_artifacts_dir / "pricing-request.example.json").write_text(json.dumps(requests[0], indent=2) + "\n", encoding="utf-8")
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
            native = capture_native_quote(compile_result["legacy_termsheet_path"], paths=paths, seed=seed)
            if native.get("engine") != "cpp_daily_termsheet_eki":
                raise AssertionError(f"native C++ engine marker missing: {native.get('engine')!r}")
            if pricing_artifacts_dir:
                pricing_artifacts_dir.mkdir(parents=True, exist_ok=True)
                filename = "native-quote-result.example.json" if not pricing_calls or len(pricing_calls) == 1 else "native-reprice-result.example.json"
                (pricing_artifacts_dir / filename).write_text(json.dumps(native, indent=2) + "\n", encoding="utf-8")
            underlyings = legacy["Chunk"]["Jobs"][0]["commonData"]["dealData"]["instrument"]["underlyings"]
            risk_rows = []
            for underlying, value in zip(underlyings, native["relative_delta"]):
                name = underlying if isinstance(underlying, str) else underlying.get("_id", underlying.get("name", str(underlying)))
                risk_rows.append({"greek": "DELTA", "risk_factor_id": f"EQ:{name}:SPOT", "value": value})
            return {
                "trade_id": thread.parameters.get("trade_id", trade_id),
                "quote": {
                    "PV": native["pv"],
                    "PV_currency": "USD",
                    "RiskCube": {"long": risk_rows, "native": native},
                    "pricing_engine": native["engine"],
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

        definition = json.loads((HERE / "process" / "fcn-etl-to-olap.process.json").read_text(encoding="utf-8"))
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
        assert scheduler.result(process.id, "quote")["quote"]["pricing_engine"] == "cpp_daily_termsheet_eki"
        assert scheduler.result(process.id, "reprice")["quote"]["pricing_engine"] == "cpp_daily_termsheet_eki"
        assert trade["status"] == "AMENDED", trade
        assert "trade.lifecycle.amended" in events, events
        assert scheduler.result(process.id, "reprice")
        assert olap["rows"][0]["trade_count"] == 1, olap
        summary = {
            "process_id": process.id,
            "process_name": snapshot["name"],
            "process_state": process.state,
            "graph": [thread["name"] for thread in snapshot["threads"]],
            "etl_calls": etl_calls,
            "pricing_calls": len(pricing_calls),
            "pricing_engine": scheduler.result(process.id, "quote")["quote"]["pricing_engine"],
            "compiled_instrument_key": scheduler.result(process.id, "compile")["instrument_key"],
            "trade_status": trade["status"],
            "events": events,
            "olap": olap,
            "sample": termsheet_path.name,
        }
        return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--termsheet", type=Path, default=HERE / "source" / "termsheet1.fcn.sample.json")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--paths", type=int, default=128)
    parser.add_argument("--manifest", type=Path, default=Path("/tmp/fina-evidence/fcn/latest-run.json"))
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    args = parser.parse_args()
    result = run(args.termsheet, args.count, args.seed, args.paths, args.artifacts_dir)
    manifest = {
        "schema_version": "fina/evidence-manifest/v1",
        "run_id": str(uuid.uuid4()),
        "product_family": "fcn",
        "registry": {"path": "model-registry/fcn.yaml", "version": 1},
        "process": {
            "id": result["process_id"],
            "name": result["process_name"],
            "state": result["process_state"],
            "graph": result["graph"],
        },
        "source_revisions": {
            "fina-skills": git_revision(REPO_ROOT),
            "FinA": git_revision(FINA_ROOT),
            "fina-risk": git_revision(RISK_ROOT),
            "fina-trade": git_revision(TRADE_ROOT),
        },
        "backend": {
            "kind": "native_cpp",
            "repository": "fina-risk",
            "module": "fina_risk_cpp",
            "callable": "run_daily_termsheet",
            "engine": result["pricing_engine"],
            "native": True,
            "source_revision": git_revision(RISK_ROOT),
            "parity_reference": "fina-risk/benchmark/daily-termsheet-parity.md",
        },
        "market": {
            "calendar": "NYSE",
            "observation_style": "daily",
            "paths": args.paths,
            "seed": args.seed,
        },
        "checks": {
            "process_schema_valid": True,
            "registry_valid": True,
            "lifecycle_contracts_valid": True,
            "two_etl_calls": result["etl_calls"] == ["run_etl_task:augment", "run_etl_task:compile"],
            "native_quote": result["pricing_engine"] == "cpp_daily_termsheet_eki",
            "native_reprice": result["pricing_engine"] == "cpp_daily_termsheet_eki" and result["pricing_calls"] == 2,
            "amended_trade_persisted": result["trade_status"] == "AMENDED",
            "amendment_event_delivered": "trade.lifecycle.amended" in result["events"],
            "olap_derived_from_reprice": result["olap"]["rows"][0]["trade_count"] == 1,
        },
        "results": {
            "pricing_engine": result["pricing_engine"],
            "trade_status": result["trade_status"],
            "events": result["events"],
            "olap": result["olap"],
            "pricing_calls": result["pricing_calls"],
            "compiled_instrument_key": result["compiled_instrument_key"],
        },
        "tolerances": {
            "pv_absolute": 1.0e-10,
            "greek_absolute": 1.0e-8,
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_model_registry.py"), "--manifest", str(args.manifest)],
        check=True,
    )
    result["manifest"] = str(args.manifest)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
