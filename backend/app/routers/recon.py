"""
ReconAI — Reconciliation API Router
Handles batch reconciliation runs, data seeding, live Razorpay dashboard sync, and result retrieval.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.services.recon_engine import run_reconciliation
from app.services.settlement_qa import answer_question
from app.services.cash_forecaster import generate_forecast
from app.services.mcp_client import recon_mcp
from app.services.data_generator import generate_dataset
import json
import asyncio
import sys
import os

router = APIRouter(prefix="/api/recon", tags=["reconciliation"])

# In-memory cache for latest reconciliation result (for Q&A queries)
_latest_recon_result = {}


@router.post("/seed")
async def seed_data(num_transactions: int = 150):
    """Seed the database with synthetic financial data."""
    db = get_db()
    data = generate_dataset(num_transactions)

    # Clear existing data
    await db.orders.delete_many({})
    await db.payments.delete_many({})
    await db.settlements.delete_many({})
    await db.recon_entries.delete_many({})
    await db.recon_results.delete_many({})

    # Insert new data
    if data["orders"]:
        await db.orders.insert_many(data["orders"])
    if data["payments"]:
        await db.payments.insert_many(data["payments"])
    if data["settlements"]:
        await db.settlements.insert_many(data["settlements"])
    if data["recon_entries"]:
        await db.recon_entries.insert_many(data["recon_entries"])

    return {
        "status": "seeded",
        "orders": len(data["orders"]),
        "payments": len(data["payments"]),
        "settlements": len(data["settlements"]),
        "recon_entries": len(data["recon_entries"]),
        "injected_variances": len(data["injected_variances"]),
        "variance_breakdown": data["metadata"]["variance_breakdown"],
    }


@router.post("/sync-live-dashboard")
async def sync_live_dashboard():
    """
    Syncs real Payments, Orders, Payment Links, and Settlements from the merchant's
    Razorpay Test Dashboard via the live API / MCP client.
    """
    global _latest_recon_result
    db = get_db()

    live_data = await recon_mcp.sync_live_dashboard_data()

    if live_data.get("orders"):
        await db.orders.insert_many(live_data["orders"])
    if live_data.get("payments"):
        await db.payments.insert_many(live_data["payments"])

    # If database had no existing batch, also generate baseline settlements for reconciliation
    orders = await db.orders.find({}, {"_id": 0}).to_list(None)
    payments = await db.payments.find({}, {"_id": 0}).to_list(None)
    settlements = await db.settlements.find({}, {"_id": 0}).to_list(None)
    recon_entries = await db.recon_entries.find({}, {"_id": 0}).to_list(None)

    if not settlements and payments:
        # Seed matching synthetic settlements for live payments so recon computes instantly
        data = generate_dataset(max(50, len(payments)))
        if data["settlements"]:
            await db.settlements.insert_many(data["settlements"])
            settlements = data["settlements"]
        if data["recon_entries"]:
            await db.recon_entries.insert_many(data["recon_entries"])
            recon_entries = data["recon_entries"]

    if payments and settlements:
        result = run_reconciliation(orders, payments, settlements, recon_entries)
        _latest_recon_result = result

    return {
        "status": "SYNC_COMPLETE",
        "live_payments_ingested": len(live_data.get("payments", [])),
        "live_orders_ingested": len(live_data.get("orders", [])),
        "payment_links_found": live_data.get("payment_links_count", 0),
        "reconciled": bool(_latest_recon_result)
    }


@router.get("/mcp-status")
async def get_mcp_status():
    """Returns the live connection status of Razorpay MCP Server & API."""
    return recon_mcp.get_mcp_status()


@router.post("/run")
async def run_recon():
    """Run the full 4-stage reconciliation pipeline."""
    global _latest_recon_result

    db = get_db()

    # Fetch all data from MongoDB
    orders = await db.orders.find({}, {"_id": 0}).to_list(None)
    payments = await db.payments.find({}, {"_id": 0}).to_list(None)
    settlements = await db.settlements.find({}, {"_id": 0}).to_list(None)
    recon_entries = await db.recon_entries.find({}, {"_id": 0}).to_list(None)

    if not payments:
        # Auto seed if empty
        data = generate_dataset(150)
        await db.orders.insert_many(data["orders"])
        await db.payments.insert_many(data["payments"])
        await db.settlements.insert_many(data["settlements"])
        await db.recon_entries.insert_many(data["recon_entries"])
        orders, payments, settlements, recon_entries = data["orders"], data["payments"], data["settlements"], data["recon_entries"]

    # Run reconciliation
    result = run_reconciliation(orders, payments, settlements, recon_entries)

    # Store complete result in MongoDB for cross-worker persistence
    _latest_recon_result = result
    result_copy = {k: v for k, v in result.items() if k != "_id"}
    await db.recon_results.insert_one(result_copy)

    return result


async def _get_or_load_latest_recon() -> dict:
    """Retrieve latest result from memory cache or load from MongoDB."""
    global _latest_recon_result
    if _latest_recon_result:
        return _latest_recon_result

    db = get_db()
    stored = await db.recon_results.find_one({}, {"_id": 0}, sort=[("timestamp", -1)])
    if stored and "waterfalls" in stored:
        _latest_recon_result = stored
        return _latest_recon_result

    return await run_recon()


@router.get("/results")
async def get_results():
    """Get the latest reconciliation results."""
    return await _get_or_load_latest_recon()


@router.get("/summary")
async def get_summary():
    """Get a lightweight summary of the latest reconciliation."""
    latest = await _get_or_load_latest_recon()
    return {
        "summary": latest.get("summary"),
        "financials": latest.get("financials"),
        "performance": latest.get("performance"),
    }


@router.get("/batches")
async def get_settlement_batches():
    """Get all settlement batches with aggregate totals and transaction-level drilldown."""
    latest = await _get_or_load_latest_recon()
    settlements = latest.get("settlements", [])
    waterfalls = latest.get("waterfalls", [])

    batch_map = {}
    for s in settlements:
        sid = s["settlement_id"]
        batch_map[sid] = {
            **s,
            "matched_txns": [],
            "total_gross": 0.0,
            "total_net": 0.0,
            "total_mdr": 0.0,
            "total_gst": 0.0,
            "total_refunds": 0.0,
        }

    for w in waterfalls:
        sid = w.get("settlement_id", "setl_0000")
        if sid not in batch_map:
            batch_map[sid] = {
                "settlement_id": sid,
                "amount": 0.0,
                "fees": 0.0,
                "tax": 0.0,
                "utr": f"UTR_{sid.upper()}",
                "status": "processed",
                "matched_txns": [],
                "total_gross": 0.0,
                "total_net": 0.0,
                "total_mdr": 0.0,
                "total_gst": 0.0,
                "total_refunds": 0.0,
            }
        b = batch_map[sid]
        b["matched_txns"].append(w)
        b["total_gross"] = round(b["total_gross"] + w["gross_amount"], 2)
        b["total_net"] = round(b["total_net"] + w["net_payout"], 2)
        b["total_mdr"] = round(b["total_mdr"] + w["mdr_fee"], 2)
        b["total_gst"] = round(b["total_gst"] + w["gst_on_mdr"], 2)
        b["total_refunds"] = round(b["total_refunds"] + w["refund_deducted"], 2)

    for sid, b in batch_map.items():
        b["txn_count"] = len(b["matched_txns"])

    return {
        "total_batches": len(batch_map),
        "batches": list(batch_map.values())
    }


@router.get("/waterfalls")
async def get_waterfalls(limit: int = 150, offset: int = 0, settlement_id: str = None):
    """Get gross-to-net waterfalls for matched transactions with optional batch filter."""
    latest = await _get_or_load_latest_recon()
    waterfalls = latest.get("waterfalls", [])
    if settlement_id:
        waterfalls = [w for w in waterfalls if w.get("settlement_id") == settlement_id]
    return {
        "total": len(waterfalls),
        "waterfalls": waterfalls[offset:offset + limit],
    }


@router.get("/exceptions")
async def get_exceptions():
    """Get all exception/variance entries with classification."""
    if not _latest_recon_result:
        await run_recon()

    classifications = _latest_recon_result.get("classifications", [])
    exceptions = [c for c in classifications if c["category"] != "MATCHED"]
    fuzzy = _latest_recon_result.get("fuzzy_candidates", [])
    duplicates = _latest_recon_result.get("duplicates", [])
    unmatched = _latest_recon_result.get("unmatched_payments", [])

    return {
        "total_exceptions": len(exceptions),
        "exceptions": exceptions,
        "fuzzy_candidates": fuzzy,
        "duplicates": duplicates,
        "missing_from_settlement": unmatched,
    }


@router.post("/qa")
async def settlement_qa(question: str):
    """Ask a natural language question about settlement data."""
    if not _latest_recon_result:
        await run_recon()

    response = answer_question(question, _latest_recon_result)

    # Store Q&A history
    db = get_db()
    await db.qa_history.insert_one({
        "question": question,
        "answer": response["answer"],
        "intent": response.get("intent"),
        "timestamp": response["timestamp"],
    })

    return response


@router.get("/forecast")
async def get_forecast():
    """Get 7-day cash flow forecast."""
    if not _latest_recon_result:
        await run_recon()

    forecast = generate_forecast(_latest_recon_result)
    return forecast


@router.get("/tax-dashboard")
async def get_tax_dashboard():
    """Get tax/GST analysis dashboard data."""
    if not _latest_recon_result:
        await run_recon()

    fin = _latest_recon_result.get("financials", {})
    mdr = fin.get("mdr_by_method", {})

    return {
        "total_gst": fin.get("total_gst_on_mdr", 0),
        "itc_eligible": fin.get("itc_eligible_gst", 0),
        "total_mdr": fin.get("total_mdr_fees", 0),
        "total_gross": fin.get("total_gross", 0),
        "total_net": fin.get("total_net_payout", 0),
        "total_refunds": fin.get("total_refunds_deducted", 0),
        "mdr_by_method": mdr,
        "effective_overall_rate": round(
            fin.get("total_mdr_fees", 0) / fin.get("total_gross", 1) * 100, 4
        ),
    }


@router.get("/stream")
async def stream_recon():
    """SSE stream for real-time reconciliation progress."""
    async def event_generator():
        db = get_db()
        payments = await db.payments.find({}, {"_id": 0}).to_list(None)
        recon_entries = await db.recon_entries.find({}, {"_id": 0}).to_list(None)

        if not payments:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No data to reconcile'})}\n\n"
            return

        total = len(payments)
        yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"
        await asyncio.sleep(0.1)

        chunk_size = max(1, total // 10)
        for i in range(0, total, chunk_size):
            chunk_end = min(i + chunk_size, total)
            progress = round(chunk_end / total * 100, 1)
            yield f"data: {json.dumps({'type': 'progress', 'processed': chunk_end, 'total': total, 'percent': progress})}\n\n"
            await asyncio.sleep(0.3)

        orders = await db.orders.find({}, {"_id": 0}).to_list(None)
        settlements = await db.settlements.find({}, {"_id": 0}).to_list(None)

        global _latest_recon_result
        result = run_reconciliation(orders, payments, settlements, recon_entries)
        _latest_recon_result = result

        yield f"data: {json.dumps({'type': 'complete', 'summary': result['summary'], 'financials': result['financials'], 'performance': result['performance']})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
