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

    # Store result
    _latest_recon_result = result
    await db.recon_results.insert_one({
        "run_id": result["run_id"],
        "timestamp": result["timestamp"],
        "summary": result["summary"],
        "financials": result["financials"],
        "performance": result["performance"],
    })

    return result


@router.get("/results")
async def get_results():
    """Get the latest reconciliation results."""
    if not _latest_recon_result:
        # Run automatically if no result cached yet
        return await run_recon()
    return _latest_recon_result


@router.get("/summary")
async def get_summary():
    """Get a lightweight summary of the latest reconciliation."""
    if not _latest_recon_result:
        await run_recon()
    return {
        "summary": _latest_recon_result.get("summary"),
        "financials": _latest_recon_result.get("financials"),
        "performance": _latest_recon_result.get("performance"),
    }


@router.get("/waterfalls")
async def get_waterfalls(limit: int = 20, offset: int = 0):
    """Get gross-to-net waterfalls for matched transactions."""
    if not _latest_recon_result:
        await run_recon()
    waterfalls = _latest_recon_result.get("waterfalls", [])
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
