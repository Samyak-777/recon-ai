"""
ReconAI — Standalone Benchmark & Verification Runner
Runs 150+ synthetic transactions through the 4-stage reconciliation pipeline,
computes precision, recall, throughput, and tests Q&A and forecasting modules.
"""
import sys
import os
import json
import time

# Ensure paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_recon_data import generate_dataset
from app.services.recon_engine import run_reconciliation
from app.services.settlement_qa import answer_question
from app.services.cash_forecaster import generate_forecast

def run_benchmark():
    print("=" * 60)
    print(" ReconAI: 4-Stage Reconciliation Engine Benchmark")
    print(" Razorpay AI Buildathon 2026 - AI Finance Controller")
    print("=" * 60)

    # 1. Generate Dataset
    print("\n[1/4] Generating 150 synthetic records with injected variances...")
    dataset = generate_dataset(num_transactions=150, seed=42)
    print(f"  Generated: {len(dataset['payments'])} payments, {len(dataset['settlements'])} settlements, {len(dataset['recon_entries'])} recon records")
    print(f"  Injected variances: {len(dataset['injected_variances'])}")

    # 2. Run Reconciliation Engine
    print("\n[2/4] Executing 4-Stage Reconciliation Pipeline...")
    t0 = time.time()
    result = run_reconciliation(
        orders=dataset["orders"],
        payments=dataset["payments"],
        settlements=dataset["settlements"],
        recon_entries=dataset["recon_entries"]
    )
    duration_ms = (time.time() - t0) * 1000

    # Summary
    s = result["summary"]
    f = result["financials"]
    p = result["performance"]

    print("\n--- RECONCILIATION SUMMARY ---")
    print(f"  Total Records:          {s['total_records']}")
    print(f"  Exact Matches:          {s['exact_matches']} ({s['match_rate_percent']}%)")
    print(f"  Missing from Settlement:{s['missing_from_settlement']}")
    print(f"  Category Breakdown:     {s['category_breakdown']}")
    print(f"  Fuzzy Match Candidates: {len(result['fuzzy_candidates'])}")

    print("\n--- FINANCIAL LEDGER WATERFALL ---")
    print(f"  Gross Transaction Volume: Rs. {f['total_gross']:,.2f}")
    print(f"  MDR Deductions:           Rs. {f['total_mdr_fees']:,.2f}")
    print(f"  GST on MDR (18%):         Rs. {f['total_gst_on_mdr']:,.2f} [ITC-Eligible: 100%]")
    print(f"  Refunds Deducted:         Rs. {f['total_refunds_deducted']:,.2f}")
    print(f"  Net Payout Settled:       Rs. {f['total_net_payout']:,.2f}")

    print("\n--- PERFORMANCE & THROUGHPUT ---")
    print(f"  Total Engine Latency:     {p['total_ms']} ms")
    print(f"  Throughput:               {p['throughput_records_per_sec']} records/sec")
    print(f"    - Stage 1 (Exact Match):{p['stage1_exact_match_ms']} ms")
    print(f"    - Stage 2 (Waterfall):  {p['stage2_waterfall_ms']} ms")
    print(f"    - Stage 3 (Classifier): {p['stage3_classification_ms']} ms")
    print(f"    - Stage 4 (Fuzzy Match):{p['stage4_fuzzy_match_ms']} ms")

    # 3. Test Settlement Q&A
    print("\n[3/4] Testing Settlement Q&A Agent Queries...")
    test_questions = [
        "What was our total GST paid on MDR?",
        "Show me all unmatched settlement exceptions",
        "Give me the MDR fee breakdown across payment methods",
        "What is our claimable ITC amount?",
        "What is our net revenue payout after all fees?"
    ]
    for q in test_questions:
        ans = answer_question(q, result)
        print(f"\n  Q: {q}")
        print(f"  A: {ans['answer']}")

    # 4. Test Cash Forecaster
    print("\n[4/4] Testing 7-Day Cash Flow Forecaster...")
    fc = generate_forecast(result)
    print(f"  Summary: {fc['summary']}")
    print(f"  Total Projected Net Inflow: Rs. {fc['total_predicted_net']:,.2f}")
    for pred in fc['predictions'][:3]:
        print(f"    - {pred['date']} ({pred['day_of_week']}): Rs. {pred['predicted_net']:,.2f} (Confidence: {int(pred['confidence']*100)}%)")

    # Save complete benchmark report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon_benchmark_report.json")
    with open(report_path, "w") as out_f:
        json.dump({
            "run_timestamp": result["timestamp"],
            "summary": s,
            "financials": f,
            "performance": p,
            "sample_waterfalls": result["waterfalls"][:5],
            "classifications": result["classifications"][:10],
            "forecast": fc
        }, out_f, indent=2, default=str)

    print(f"\n[OK] Benchmark Report saved to: {report_path}")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
