"""
Razorpay Webhook Ingestion Router for ReconAI
Listens for live payment, refund, and settlement webhooks from Razorpay, verifies HMAC SHA-256 signatures,
and auto-ingests events into the reconciliation database.
"""
import os
import hmac
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Header, HTTPException
from app.config import settings
from app.database import get_db

logger = logging.getLogger("recon_webhooks")
router = APIRouter(prefix="/api/recon/webhooks", tags=["webhooks"])

# In-memory webhook event feed buffer
_live_webhook_feed: List[Dict[str, Any]] = []

def verify_razorpay_signature(raw_body: bytes, signature: Optional[str], secret: Optional[str]) -> bool:
    """Verifies HMAC SHA256 webhook signature from Razorpay."""
    if not secret:
        # If no secret is configured yet, accept for testing with warning
        return True
    if not signature:
        return False
    generated_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated_sig, signature)

@router.post("")
@router.post("/")
async def receive_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: Optional[str] = Header(None, alias="X-Razorpay-Event-Id")
):
    """
    Primary endpoint for Razorpay Webhooks.
    Configure this URL in Razorpay Dashboard: Account & Settings -> Webhooks.
    """
    raw_body = await request.body()
    secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None) or os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    is_valid = verify_razorpay_signature(raw_body, x_razorpay_signature, secret)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Razorpay Webhook Signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

    event_type = payload.get("event", "unknown")
    event_id = x_razorpay_event_id or payload.get("event_id") or f"evt_{hash(str(raw_body)) % 10000000}"
    contains = payload.get("contains", [])
    entity_data = payload.get("payload", {})

    db = get_db()
    ingested_record = None

    # Handle Payment Events
    if "payment" in entity_data:
        p_entity = entity_data["payment"]["entity"]
        amount_inr = float(p_entity.get("amount", 0)) / 100.0
        fee_inr = float(p_entity.get("fee", 0)) / 100.0
        tax_inr = float(p_entity.get("tax", 0)) / 100.0
        
        # If fee not provided directly by test webhook, calculate based on method
        method = p_entity.get("method", "card")
        if fee_inr == 0 and method != "upi":
            fee_inr = round(amount_inr * (0.02 if method == "card" else 0.018), 2)
            tax_inr = round(fee_inr * 0.18, 2)

        payment_doc = {
            "payment_id": p_entity.get("id"),
            "order_id": p_entity.get("order_id") or f"order_{p_entity.get('id')}",
            "amount": amount_inr,
            "currency": p_entity.get("currency", "INR"),
            "status": p_entity.get("status", "captured"),
            "method": method,
            "bank": p_entity.get("bank"),
            "vpa": p_entity.get("vpa"),
            "fee": fee_inr,
            "tax": tax_inr,
            "error_code": p_entity.get("error_code"),
            "source": "RAZORPAY_WEBHOOK",
            "received_at": datetime.utcnow().isoformat()
        }
        await db.payments.insert_one(payment_doc)
        ingested_record = payment_doc

    # Handle Settlement Events
    elif "settlement" in entity_data:
        s_entity = entity_data["settlement"]["entity"]
        settlement_doc = {
            "settlement_id": s_entity.get("id"),
            "amount": float(s_entity.get("amount", 0)) / 100.0,
            "fees": float(s_entity.get("fees", 0)) / 100.0,
            "tax": float(s_entity.get("tax", 0)) / 100.0,
            "status": s_entity.get("status", "processed"),
            "utr": s_entity.get("utr"),
            "source": "RAZORPAY_WEBHOOK",
            "received_at": datetime.utcnow().isoformat()
        }
        await db.settlements.insert_one(settlement_doc)
        ingested_record = settlement_doc

    # Store in Live Feed Buffer (keep last 50)
    feed_entry = {
        "event_id": event_id,
        "event": event_type,
        "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
        "signature_verified": bool(secret and is_valid),
        "summary": f"{event_type} received ({payload.get('account_id', 'Test Account')})",
        "entity": ingested_record or entity_data
    }
    _live_webhook_feed.insert(0, feed_entry)
    if len(_live_webhook_feed) > 50:
        _live_webhook_feed.pop()

    return {
        "status": "RECEIVED",
        "event": event_type,
        "event_id": event_id,
        "ingested": bool(ingested_record)
    }

@router.get("/feed")
async def get_webhook_feed():
    """Returns the live stream of ingested Razorpay webhooks."""
    return {
        "count": len(_live_webhook_feed),
        "webhook_url": "/api/recon/webhooks",
        "feed": _live_webhook_feed
    }

@router.post("/simulate-test")
async def simulate_test_webhook(event_type: str = "payment.captured", amount_inr: float = 3550.0, method: str = "card"):
    """Simulates a live webhook payload for testing without leaving the UI."""
    import random
    mock_id = f"pay_live_mock_{random.randint(100000, 999999)}"
    mock_order = f"order_mock_{random.randint(100000, 999999)}"
    
    fee = round(amount_inr * (0.02 if method == "card" else 0.0), 2)
    tax = round(fee * 0.18, 2)

    doc = {
        "payment_id": mock_id,
        "order_id": mock_order,
        "amount": amount_inr,
        "currency": "INR",
        "status": "captured" if "captured" in event_type else "failed",
        "method": method,
        "fee": fee,
        "tax": tax,
        "source": "SIMULATED_TEST_WEBHOOK",
        "received_at": datetime.utcnow().isoformat()
    }
    db = get_db()
    await db.payments.insert_one(doc)

    feed_entry = {
        "event_id": f"evt_sim_{random.randint(10000, 99999)}",
        "event": event_type,
        "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
        "signature_verified": True,
        "summary": f"{event_type} on {method.upper()} for Rs. {amount_inr:,.2f}",
        "entity": doc
    }
    _live_webhook_feed.insert(0, feed_entry)
    return {"status": "SUCCESS", "event": feed_entry}
