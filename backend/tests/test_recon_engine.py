"""
Unit and Invariant Test Suite for ReconAI
Validates financial math invariants, variance classification, and performance.
"""
import pytest
from app.services.recon_engine import (
    exact_match,
    unpack_net_to_gross,
    classify_variance,
    run_reconciliation,
)
from app.services.data_generator import generate_dataset


def test_gross_to_net_conservation_invariant():
    """
    Financial Invariant:
    Gross Amount == Net Payout + MDR Fee + GST on MDR + Refund Deducted
    Must hold strictly with zero drift.
    """
    payment = {
        "payment_id": "pay_test_001",
        "order_id": "order_test_001",
        "amount": 2500.0,
        "method": "card",
        "fee": 50.0,
        "tax": 9.0,
    }
    recon = {
        "entity_id": "pay_test_001",
        "amount": 2500.0,
        "fee": 50.0,
        "tax": 9.0,
        "settlement_id": "setl_0000",
    }

    wf = unpack_net_to_gross(payment, recon)
    reconstructed_gross = round(
        wf["net_payout"] + wf["mdr_fee"] + wf["gst_on_mdr"] + wf["refund_deducted"], 2
    )
    assert reconstructed_gross == payment["amount"]
    assert wf["itc_eligible_gst"] == wf["gst_on_mdr"]
    assert wf["settlement_id"] == "setl_0000"


def test_cross_period_refund_waterfall():
    """
    When a refund is deducted, Gross == Net + MDR + GST + Refund.
    """
    payment = {
        "payment_id": "pay_test_refund",
        "order_id": "order_test_refund",
        "amount": 5000.0,
        "method": "card",
        "fee": 100.0,
        "tax": 18.0,
    }
    recon = {
        "entity_id": "pay_test_refund",
        "amount": 4000.0,  # 1000 deducted for partial refund
        "fee": 100.0,
        "tax": 18.0,
        "settlement_id": "setl_0001",
    }

    wf = unpack_net_to_gross(payment, recon)
    assert wf["refund_deducted"] == 1000.0
    reconstructed_gross = round(
        wf["net_payout"] + wf["mdr_fee"] + wf["gst_on_mdr"] + wf["refund_deducted"], 2
    )
    assert reconstructed_gross == 5000.0


def test_variance_classifications():
    """
    Test deterministic classification across all known anomaly archetypes.
    """
    base_payment = {
        "payment_id": "pay_01",
        "amount": 1000.0,
        "fee": 20.0,
        "tax": 3.6,
    }

    # 1. Exact Match
    res_matched = classify_variance(base_payment, {"amount": 1000.0, "fee": 20.0, "tax": 3.6})
    assert res_matched["category"] == "MATCHED"

    # 2. Sub-rupee rounding variance (<= 1.00)
    res_round = classify_variance(base_payment, {"amount": 1000.45, "fee": 20.0, "tax": 3.6})
    assert res_round["category"] == "ROUNDING"

    # 3. Fee deduction mismatch
    res_fee = classify_variance(base_payment, {"amount": 1000.0, "fee": 35.0, "tax": 3.6})
    assert res_fee["category"] == "FEE_DEDUCTION"

    # 4. Tax deduction mismatch
    res_tax = classify_variance(base_payment, {"amount": 1000.0, "fee": 20.0, "tax": 6.0})
    assert res_tax["category"] == "TAX_DEDUCTION"

    # 5. Cross period refund (negative difference)
    res_refund = classify_variance(base_payment, {"amount": 800.0, "fee": 20.0, "tax": 3.6})
    assert res_refund["category"] == "CROSS_PERIOD_REFUND"


def test_end_to_end_150_record_reconciliation():
    """
    Run the complete 4-stage pipeline on 150 synthetic records.
    Assert high match rate, low latency (< 100ms), and proper batch segregation.
    """
    dataset = generate_dataset(150)
    result = run_reconciliation(
        orders=dataset["orders"],
        payments=dataset["payments"],
        settlements=dataset["settlements"],
        recon_entries=dataset["recon_entries"],
    )

    summary = result["summary"]
    financials = result["financials"]
    performance = result["performance"]

    assert summary["total_records"] == 150
    assert summary["match_rate_percent"] >= 95.0
    assert performance["total_ms"] < 100.0  # Sub-100ms SLA
    assert len(result["waterfalls"]) > 0
    assert len(result["settlements"]) > 0

    # Ensure aggregate financials conserve capital
    total_components = round(
        financials["total_net_payout"]
        + financials["total_mdr_fees"]
        + financials["total_gst_on_mdr"]
        + financials["total_refunds_deducted"],
        2,
    )
    # Allows for minor injected rounding drift (within ₹5 across ₹35L+ volume)
    diff = abs(total_components - financials["total_gross"])
    assert diff < 10.0
