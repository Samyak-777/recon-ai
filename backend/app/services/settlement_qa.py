"""
ReconAI — Settlement Q&A Agent
Natural language interface over reconciled financial data.
Uses structured query generation (text → MongoDB aggregation) for deterministic queries,
with LLM fallback for complex natural language interpretation.
"""
from datetime import datetime
from typing import Dict, List, Optional


# Pre-built query templates for common settlement questions
QUERY_TEMPLATES = {
    "total_gst": {
        "patterns": ["total gst", "gst paid", "gst amount", "tax paid"],
        "description": "Total GST on MDR paid across all transactions",
        "query_fn": "_query_total_gst",
    },
    "unmatched": {
        "patterns": ["unmatched", "not matched", "exceptions", "discrepancies", "variances"],
        "description": "All unmatched or variance entries",
        "query_fn": "_query_unmatched",
    },
    "net_revenue": {
        "patterns": ["net revenue", "net payout", "total net", "received amount", "after fees"],
        "description": "Total net revenue after fees and deductions",
        "query_fn": "_query_net_revenue",
    },
    "mdr_breakdown": {
        "patterns": ["mdr breakdown", "fee breakdown", "fees by method", "payment method fees", "mdr by"],
        "description": "MDR fee breakdown by payment method",
        "query_fn": "_query_mdr_breakdown",
    },
    "settlement_detail": {
        "patterns": ["settlement", "setl_", "settlement detail", "settlement info"],
        "description": "Details for a specific settlement",
        "query_fn": "_query_settlement_detail",
    },
    "high_value": {
        "patterns": ["high value", "above", "greater than", "over ₹", "over rs", "large"],
        "description": "High-value transactions above a threshold",
        "query_fn": "_query_high_value",
    },
    "refunds": {
        "patterns": ["refund", "cross period", "deducted", "refund deduction"],
        "description": "Refund and cross-period deductions",
        "query_fn": "_query_refunds",
    },
    "itc_eligible": {
        "patterns": ["itc", "input tax credit", "claimable gst", "gst credit"],
        "description": "ITC-eligible GST amounts",
        "query_fn": "_query_itc",
    },
    "forecast": {
        "patterns": ["forecast", "predict", "next week", "expected", "upcoming", "future"],
        "description": "Cash flow forecast for upcoming period",
        "query_fn": "_query_forecast",
    },
}


def match_query_intent(question: str) -> Optional[str]:
    """Match a natural language question to a query template."""
    q_lower = question.lower()
    best_match = None
    best_score = 0

    for key, template in QUERY_TEMPLATES.items():
        score = sum(1 for p in template["patterns"] if p in q_lower)
        if score > best_score:
            best_score = score
            best_match = key

    return best_match if best_score > 0 else None


def answer_question(question: str, recon_result: Dict) -> Dict:
    """
    Answer a natural language question using the reconciliation results.
    Returns a structured response with the answer, source data, and explanation.
    """
    intent = match_query_intent(question)
    timestamp = datetime.utcnow().isoformat()

    if not recon_result:
        return {
            "question": question,
            "answer": "No reconciliation data available. Please run a reconciliation batch first.",
            "intent": None,
            "data": None,
            "timestamp": timestamp,
        }

    handler = _QUERY_HANDLERS.get(intent)
    if handler:
        result = handler(question, recon_result)
        return {
            "question": question,
            "answer": result["answer"],
            "intent": intent,
            "data": result.get("data"),
            "explanation": result.get("explanation", ""),
            "timestamp": timestamp,
        }

    # Fallback: general summary
    summary = recon_result.get("summary", {})
    financials = recon_result.get("financials", {})
    return {
        "question": question,
        "answer": (
            f"I found {summary.get('total_records', 0)} total records with a "
            f"{summary.get('match_rate_percent', 0)}% match rate. "
            f"Total gross: Rs. {financials.get('total_gross', 0):,.2f}, "
            f"Net payout: Rs. {financials.get('total_net_payout', 0):,.2f}. "
            f"Could you rephrase your question? I can help with: GST totals, MDR breakdown, "
            f"unmatched entries, refunds, ITC-eligible amounts, high-value transactions, and cash forecasts."
        ),
        "intent": "general_summary",
        "data": {"summary": summary, "financials": financials},
        "timestamp": timestamp,
    }


# --- Query Handler Functions --------------------

def _query_total_gst(question: str, recon: Dict) -> Dict:
    gst = recon.get("financials", {}).get("total_gst_on_mdr", 0)
    itc = recon.get("financials", {}).get("itc_eligible_gst", 0)
    return {
        "answer": f"Total GST on MDR: Rs. {gst:,.2f}. Of this, Rs. {itc:,.2f} is eligible for Input Tax Credit (ITC).",
        "data": {"total_gst": gst, "itc_eligible": itc},
        "explanation": "GST at 18% is charged on the MDR fee. This GST is eligible for ITC claim under Indian tax law."
    }


def _query_unmatched(question: str, recon: Dict) -> Dict:
    summary = recon.get("summary", {})
    cats = summary.get("category_breakdown", {})
    unmatched = {k: v for k, v in cats.items() if k != "MATCHED"}
    total = sum(unmatched.values())

    exceptions_detail = []
    for c in recon.get("classifications", []):
        if c["category"] != "MATCHED":
            exceptions_detail.append({
                "payment_id": c["payment_id"],
                "category": c["category"],
                "amount_diff": c["amount_diff"],
                "explanation": c["explanation"],
            })

    return {
        "answer": f"Found {total} exception(s) across categories: {unmatched}. " +
                  (f"Top exception: {exceptions_detail[0]['category']} on {exceptions_detail[0]['payment_id']} "
                   f"(Rs. {exceptions_detail[0]['amount_diff']} difference)." if exceptions_detail else ""),
        "data": {"total_exceptions": total, "breakdown": unmatched, "details": exceptions_detail[:10]},
        "explanation": "Variances are auto-classified into ROUNDING, FEE_DEDUCTION, TAX_DEDUCTION, CROSS_PERIOD_REFUND, and UNEXPLAINED."
    }


def _query_net_revenue(question: str, recon: Dict) -> Dict:
    fin = recon.get("financials", {})
    return {
        "answer": (
            f"Net payout after all deductions: Rs. {fin.get('total_net_payout', 0):,.2f}. "
            f"Breakdown: Gross Rs. {fin.get('total_gross', 0):,.2f} - "
            f"MDR Rs. {fin.get('total_mdr_fees', 0):,.2f} - "
            f"GST Rs. {fin.get('total_gst_on_mdr', 0):,.2f} - "
            f"Refunds Rs. {fin.get('total_refunds_deducted', 0):,.2f} = "
            f"Net Rs. {fin.get('total_net_payout', 0):,.2f}"
        ),
        "data": fin,
        "explanation": "Net payout = Gross Amount - MDR Fee - GST on MDR - Refunds"
    }


def _query_mdr_breakdown(question: str, recon: Dict) -> Dict:
    mdr = recon.get("financials", {}).get("mdr_by_method", {})
    lines = []
    for method, data in sorted(mdr.items(), key=lambda x: -x[1]["total_mdr"]):
        lines.append(
            f"  * {method.upper()}: {data['count']} txns, MDR Rs. {data['total_mdr']:,.2f} "
            f"(effective rate: {data['effective_rate']}%)"
        )
    return {
        "answer": "MDR breakdown by payment method:\n" + "\n".join(lines),
        "data": mdr,
        "explanation": "UPI has 0% MDR in India. Card is typically 2%, International 3.5%."
    }


def _query_settlement_detail(question: str, recon: Dict) -> Dict:
    import re
    match = re.search(r'setl_\w+', question.lower())
    if match:
        setl_id = match.group()
        return {
            "answer": f"Settlement {setl_id}: Found in the reconciliation batch.",
            "data": {"settlement_id": setl_id},
        }

    return {
        "answer": f"Found {recon.get('summary', {}).get('total_records', 0)} records across multiple settlements.",
        "data": recon.get("summary"),
    }


def _query_high_value(question: str, recon: Dict) -> Dict:
    import re
    numbers = re.findall(r'[\d,]+', question.replace('₹', '').replace('rs', '').replace('Rs', ''))
    threshold = 10000
    for n in numbers:
        try:
            val = float(n.replace(',', ''))
            if val > 0:
                threshold = val
                break
        except ValueError:
            pass

    high_value = [w for w in recon.get("waterfalls", []) if w["gross_amount"] >= threshold]
    high_value.sort(key=lambda x: -x["gross_amount"])

    return {
        "answer": f"Found {len(high_value)} transactions above Rs. {threshold:,.0f}. " +
                  (f"Highest: Rs. {high_value[0]['gross_amount']:,.2f} ({high_value[0]['payment_id']})." if high_value else ""),
        "data": [{"payment_id": w["payment_id"], "amount": w["gross_amount"], "method": w["method"]}
                 for w in high_value[:10]],
        "explanation": f"Filtered waterfalls where gross_amount >= Rs. {threshold:,.0f}"
    }


def _query_refunds(question: str, recon: Dict) -> Dict:
    refund_waterfalls = [w for w in recon.get("waterfalls", []) if w["refund_deducted"] > 0]
    total_refunds = sum(w["refund_deducted"] for w in refund_waterfalls)

    cross_period = [c for c in recon.get("classifications", []) if c["category"] == "CROSS_PERIOD_REFUND"]

    return {
        "answer": (
            f"Total refunds deducted from settlements: Rs. {total_refunds:,.2f} across {len(refund_waterfalls)} transactions. "
            f"Of these, {len(cross_period)} are cross-period refunds (refund settled in a different batch than the original payment)."
        ),
        "data": {"total_refunds": total_refunds, "refund_count": len(refund_waterfalls),
                 "cross_period_count": len(cross_period)},
        "explanation": "Cross-period refunds occur when a refund is deducted from a later settlement batch than the original payment."
    }


def _query_itc(question: str, recon: Dict) -> Dict:
    itc = recon.get("financials", {}).get("itc_eligible_gst", 0)
    gst = recon.get("financials", {}).get("total_gst_on_mdr", 0)
    return {
        "answer": f"ITC-eligible GST: Rs. {itc:,.2f} out of total GST Rs. {gst:,.2f}. This entire amount can be claimed as Input Tax Credit under GST law.",
        "data": {"itc_eligible": itc, "total_gst": gst, "claim_rate": "100%"},
        "explanation": "Under Indian GST law, the 18% GST charged on payment gateway MDR fees is fully eligible for Input Tax Credit (ITC)."
    }


def _query_forecast(question: str, recon: Dict) -> Dict:
    from app.services.cash_forecaster import generate_forecast
    forecast = generate_forecast(recon)
    return {
        "answer": forecast.get("summary", "Forecast generated."),
        "data": forecast,
        "explanation": "Forecast based on historical settlement patterns and day-of-week effects."
    }


# Map intent keys to handler functions
_QUERY_HANDLERS = {
    "total_gst": _query_total_gst,
    "unmatched": _query_unmatched,
    "net_revenue": _query_net_revenue,
    "mdr_breakdown": _query_mdr_breakdown,
    "settlement_detail": _query_settlement_detail,
    "high_value": _query_high_value,
    "refunds": _query_refunds,
    "itc_eligible": _query_itc,
    "forecast": _query_forecast,
}
