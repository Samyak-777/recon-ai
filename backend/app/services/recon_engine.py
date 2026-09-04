"""
ReconAI — Core Reconciliation Engine
4-Stage Pipeline: Exact Match → Net-to-Gross Unpack → Variance Classify → Fuzzy Match
All financial logic is DETERMINISTIC. LLMs are only used for fuzzy matching proposals.
"""
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from app.config import settings

# ─────────────────────────────────────────────
# STAGE 1: Exact Matching (Deterministic)
# ─────────────────────────────────────────────

def exact_match(payments: List[Dict], recon_entries: List[Dict]) -> Dict:
    """
    Match recon entries to payments by entity_id == payment_id.
    Returns matched, unmatched_recon, and unmatched_payments.
    """
    payment_map = {p["payment_id"]: p for p in payments}
    recon_by_entity = {}
    duplicates = []

    for entry in recon_entries:
        eid = entry["entity_id"]
        if eid in recon_by_entity:
            duplicates.append(entry)
        else:
            recon_by_entity[eid] = entry

    matched = []
    unmatched_recon = []
    unmatched_payments = []

    for eid, recon in recon_by_entity.items():
        if eid in payment_map:
            matched.append({
                "payment": payment_map[eid],
                "recon": recon,
                "match_type": "EXACT_ID",
            })
        else:
            unmatched_recon.append(recon)

    matched_ids = {m["payment"]["payment_id"] for m in matched}
    for pid, p in payment_map.items():
        if pid not in matched_ids and pid not in recon_by_entity:
            unmatched_payments.append(p)

    return {
        "matched": matched,
        "unmatched_recon": unmatched_recon,
        "unmatched_payments": unmatched_payments,
        "duplicates": duplicates,
    }


# ─────────────────────────────────────────────
# STAGE 2: Net-to-Gross Unpacker (Deterministic)
# ─────────────────────────────────────────────

def unpack_net_to_gross(payment: Dict, recon: Dict) -> Dict:
    """
    For a matched pair, compute the full gross-to-net waterfall.
    Returns the waterfall breakdown and any ITC-eligible amounts.
    """
    gross = payment["amount"]
    method = payment.get("method", "card")
    expected_mdr_rate = {
        "upi": 0.0, "card": 0.02, "netbanking": 0.018,
        "wallet": 0.019, "intl_card": 0.035
    }.get(method, 0.02)

    expected_mdr = round(gross * expected_mdr_rate, 2)
    expected_gst = round(expected_mdr * settings.GST_RATE, 2)
    expected_net = round(gross - expected_mdr - expected_gst, 2)

    actual_fee = recon.get("fee", payment.get("fee", 0))
    actual_tax = recon.get("tax", payment.get("tax", 0))
    actual_amount = recon.get("amount", gross)
    actual_net = round(actual_amount - actual_fee - actual_tax, 2)

    # Detect refund component
    refund_amount = 0
    if actual_amount < gross:
        refund_amount = round(gross - actual_amount, 2)

    waterfall = {
        "payment_id": payment["payment_id"],
        "order_id": payment.get("order_id"),
        "method": method,
        "gross_amount": gross,
        "mdr_fee": actual_fee,
        "mdr_rate_expected": expected_mdr_rate,
        "mdr_rate_actual": round(actual_fee / gross, 4) if gross > 0 else 0,
        "gst_on_mdr": actual_tax,
        "gst_rate": settings.GST_RATE,
        "itc_eligible_gst": actual_tax,  # All GST on MDR is ITC-eligible
        "refund_deducted": refund_amount,
        "net_payout": actual_net,
        "expected_net": expected_net,
        "net_variance": round(actual_net - expected_net, 2),
        "waterfall_steps": [
            {"label": "Gross Amount", "amount": gross, "type": "credit"},
            {"label": f"MDR Fee ({method})", "amount": -actual_fee, "type": "debit"},
            {"label": "GST on MDR (18%)", "amount": -actual_tax, "type": "debit"},
        ]
    }

    if refund_amount > 0:
        waterfall["waterfall_steps"].append(
            {"label": "Refund Deducted", "amount": -refund_amount, "type": "debit"}
        )

    waterfall["waterfall_steps"].append(
        {"label": "Net Payout", "amount": actual_net, "type": "net"}
    )

    return waterfall


# ─────────────────────────────────────────────
# STAGE 3: Variance Classification (Deterministic)
# ─────────────────────────────────────────────

def classify_variance(payment: Dict, recon: Dict) -> Dict:
    """
    Classify the type of variance between payment and recon entry.
    Categories: MATCHED, ROUNDING, FEE_DEDUCTION, TAX_DEDUCTION,
                CROSS_PERIOD_REFUND, UNEXPLAINED
    """
    amount_diff = round(recon.get("amount", 0) - payment["amount"], 2)
    fee_diff = round(recon.get("fee", 0) - payment.get("fee", 0), 2)
    tax_diff = round(recon.get("tax", 0) - payment.get("tax", 0), 2)

    result = {
        "payment_id": payment["payment_id"],
        "amount_diff": amount_diff,
        "fee_diff": fee_diff,
        "tax_diff": tax_diff,
        "status": "MATCHED",
        "category": "MATCHED",
        "confidence": 1.0,
        "explanation": "",
    }

    # Perfect match
    if amount_diff == 0 and fee_diff == 0 and tax_diff == 0:
        result["explanation"] = "All fields match exactly."
        return result

    # Sub-rupee rounding
    if abs(amount_diff) <= settings.ROUNDING_TOLERANCE and fee_diff == 0 and tax_diff == 0:
        result["status"] = "VARIANCE"
        result["category"] = "ROUNDING"
        result["confidence"] = 0.98
        result["explanation"] = f"Sub-rupee rounding difference of Rs. {amount_diff}. Within Rs. {settings.ROUNDING_TOLERANCE} tolerance."
        return result

    # Fee deduction anomaly (MDR rate mismatch)
    if amount_diff == 0 and fee_diff != 0:
        result["status"] = "VARIANCE"
        result["category"] = "FEE_DEDUCTION"
        result["confidence"] = 0.90
        result["explanation"] = f"MDR fee differs by Rs. {fee_diff}. Possible promotional/negotiated rate difference."
        return result

    # Tax deduction anomaly
    if amount_diff == 0 and tax_diff != 0:
        result["status"] = "VARIANCE"
        result["category"] = "TAX_DEDUCTION"
        result["confidence"] = 0.90
        result["explanation"] = f"GST on MDR differs by Rs. {tax_diff}. Possible tax calculation rounding."
        return result

    # Cross-period refund (amount in recon is less than payment, suggesting refund netted)
    if amount_diff < 0 and abs(amount_diff) > settings.ROUNDING_TOLERANCE:
        result["status"] = "VARIANCE"
        result["category"] = "CROSS_PERIOD_REFUND"
        result["confidence"] = 0.85
        result["explanation"] = f"Recon amount Rs. {abs(amount_diff)} less than payment. Likely cross-period refund deducted from settlement."
        return result

    # Unexplained
    result["status"] = "VARIANCE"
    result["category"] = "UNEXPLAINED"
    result["confidence"] = 0.50
    result["explanation"] = f"Unclassified variance: amount_diff=Rs. {amount_diff}, fee_diff=Rs. {fee_diff}, tax_diff=Rs. {tax_diff}. Requires AI analysis or manual review."
    return result


# ─────────────────────────────────────────────
# STAGE 4: Fuzzy Matching (AI-Assisted)
# ─────────────────────────────────────────────

def fuzzy_match_candidates(
    unmatched_recon: List[Dict],
    unmatched_payments: List[Dict],
) -> List[Dict]:
    """
    For entries that couldn't be matched by ID, attempt fuzzy matching
    using amount proximity, date proximity, and method heuristics.
    Returns candidate matches with confidence scores.
    
    NOTE: This is a DETERMINISTIC heuristic fuzzy matcher.
    In production, an LLM would be used for the final 'UNEXPLAINED' entries.
    """
    candidates = []

    for recon in unmatched_recon:
        best_match = None
        best_score = 0.0

        for payment in unmatched_payments:
            score = 0.0

            # Amount similarity (weight: 0.5)
            amount_diff = abs(recon.get("amount", 0) - payment["amount"])
            if amount_diff == 0:
                score += 0.5
            elif amount_diff < 1.0:
                score += 0.45
            elif amount_diff < 10.0:
                score += 0.3
            elif amount_diff < 100.0:
                score += 0.1

            # Date proximity (weight: 0.3)
            try:
                recon_date = datetime.fromisoformat(recon.get("created_at", ""))
                pay_date = datetime.fromisoformat(payment.get("created_at", ""))
                day_diff = abs((recon_date - pay_date).days)
                if day_diff == 0:
                    score += 0.3
                elif day_diff <= 1:
                    score += 0.25
                elif day_diff <= 3:
                    score += 0.15
                elif day_diff <= 7:
                    score += 0.05
            except (ValueError, TypeError):
                pass

            # Settlement batch match (weight: 0.2)
            if recon.get("settlement_id") == payment.get("settlement_id"):
                score += 0.2

            if score > best_score:
                best_score = score
                best_match = payment

        if best_match and best_score >= settings.FUZZY_MATCH_REVIEW_THRESHOLD:
            status = "AUTO_MATCHED" if best_score >= settings.FUZZY_MATCH_CONFIDENCE_THRESHOLD else "REVIEW_NEEDED"
            candidates.append({
                "recon_entry": recon,
                "candidate_payment": best_match,
                "confidence": round(best_score, 3),
                "status": status,
                "match_type": "FUZZY",
            })

    return candidates


# ─────────────────────────────────────────────
# FULL PIPELINE ORCHESTRATOR
# ─────────────────────────────────────────────

def run_reconciliation(
    orders: List[Dict],
    payments: List[Dict],
    settlements: List[Dict],
    recon_entries: List[Dict],
) -> Dict:
    """
    Run the complete 4-stage reconciliation pipeline.
    Returns comprehensive results with timing and accuracy metrics.
    """
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()

    # STAGE 1: Exact matching
    stage1_start = time.time()
    match_result = exact_match(payments, recon_entries)
    stage1_ms = round((time.time() - stage1_start) * 1000, 2)

    # STAGE 2: Net-to-Gross waterfall for all matches
    stage2_start = time.time()
    waterfalls = []
    for m in match_result["matched"]:
        wf = unpack_net_to_gross(m["payment"], m["recon"])
        waterfalls.append(wf)
    stage2_ms = round((time.time() - stage2_start) * 1000, 2)

    # STAGE 3: Variance classification for all matches
    stage3_start = time.time()
    classifications = []
    for m in match_result["matched"]:
        vc = classify_variance(m["payment"], m["recon"])
        classifications.append(vc)
    stage3_ms = round((time.time() - stage3_start) * 1000, 2)

    # STAGE 4: Fuzzy matching for unmatched entries
    stage4_start = time.time()
    fuzzy_candidates = fuzzy_match_candidates(
        match_result["unmatched_recon"],
        match_result["unmatched_payments"]
    )
    stage4_ms = round((time.time() - stage4_start) * 1000, 2)

    total_ms = round((time.time() - start_time) * 1000, 2)

    # --- Compute Summary Metrics ---
    total_records = len(payments)
    exact_matches = len(match_result["matched"])
    duplicates = len(match_result["duplicates"])
    missing_from_recon = len(match_result["unmatched_payments"])
    unmatched_recon_count = len(match_result["unmatched_recon"])
    fuzzy_auto = sum(1 for c in fuzzy_candidates if c["status"] == "AUTO_MATCHED")
    fuzzy_review = sum(1 for c in fuzzy_candidates if c["status"] == "REVIEW_NEEDED")

    # Category breakdown
    category_counts = {}
    for c in classifications:
        cat = c["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    match_rate = round((exact_matches / total_records) * 100, 2) if total_records > 0 else 0

    # Aggregate financials
    total_gross = sum(w["gross_amount"] for w in waterfalls)
    total_mdr = sum(w["mdr_fee"] for w in waterfalls)
    total_gst = sum(w["gst_on_mdr"] for w in waterfalls)
    total_itc = sum(w["itc_eligible_gst"] for w in waterfalls)
    total_refunds = sum(w["refund_deducted"] for w in waterfalls)
    total_net = sum(w["net_payout"] for w in waterfalls)

    # MDR breakdown by method
    mdr_by_method = {}
    for w in waterfalls:
        method = w["method"]
        if method not in mdr_by_method:
            mdr_by_method[method] = {"count": 0, "total_mdr": 0, "total_gross": 0, "total_gst": 0}
        mdr_by_method[method]["count"] += 1
        mdr_by_method[method]["total_mdr"] = round(mdr_by_method[method]["total_mdr"] + w["mdr_fee"], 2)
        mdr_by_method[method]["total_gross"] = round(mdr_by_method[method]["total_gross"] + w["gross_amount"], 2)
        mdr_by_method[method]["total_gst"] = round(mdr_by_method[method]["total_gst"] + w["gst_on_mdr"], 2)

    for method, data in mdr_by_method.items():
        data["effective_rate"] = round(data["total_mdr"] / data["total_gross"] * 100, 4) if data["total_gross"] > 0 else 0

    return {
        "run_id": f"recon_{int(time.time())}",
        "timestamp": timestamp,
        "summary": {
            "total_records": total_records,
            "exact_matches": exact_matches,
            "match_rate_percent": match_rate,
            "duplicates_found": duplicates,
            "missing_from_settlement": missing_from_recon,
            "unmatched_recon_entries": unmatched_recon_count,
            "fuzzy_auto_matched": fuzzy_auto,
            "fuzzy_review_needed": fuzzy_review,
            "category_breakdown": category_counts,
        },
        "financials": {
            "total_gross": round(total_gross, 2),
            "total_mdr_fees": round(total_mdr, 2),
            "total_gst_on_mdr": round(total_gst, 2),
            "itc_eligible_gst": round(total_itc, 2),
            "total_refunds_deducted": round(total_refunds, 2),
            "total_net_payout": round(total_net, 2),
            "mdr_by_method": mdr_by_method,
        },
        "performance": {
            "total_ms": total_ms,
            "stage1_exact_match_ms": stage1_ms,
            "stage2_waterfall_ms": stage2_ms,
            "stage3_classification_ms": stage3_ms,
            "stage4_fuzzy_match_ms": stage4_ms,
            "throughput_records_per_sec": round(total_records / (total_ms / 1000), 1) if total_ms > 0 else 0,
        },
        "waterfalls": waterfalls,
        "classifications": classifications,
        "fuzzy_candidates": fuzzy_candidates,
        "duplicates": match_result["duplicates"],
        "unmatched_payments": match_result["unmatched_payments"],
    }
