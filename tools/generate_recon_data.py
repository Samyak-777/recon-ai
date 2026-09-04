"""
ReconAI — Synthetic Financial Data Generator
Generates 150+ realistic Razorpay-shaped transactions with known variances
for demonstrating the reconciliation engine.
"""
import random
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict

# --- MDR rates by payment method (realistic Indian gateway rates) ---
MDR_RATES = {
    "upi": 0.0,       # UPI has zero MDR in India
    "card": 0.02,      # 2% for domestic cards
    "netbanking": 0.018, # 1.8% for netbanking
    "wallet": 0.019,   # 1.9% for wallets
    "intl_card": 0.035, # 3.5% for international cards
}

GST_RATE = 0.18  # 18% GST on MDR
PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet", "intl_card"]
PAYMENT_METHOD_WEIGHTS = [0.40, 0.30, 0.15, 0.10, 0.05]

# Variance injection rates
ROUNDING_VARIANCE_RATE = 0.05    # 5% of transactions
CROSS_PERIOD_REFUND_RATE = 0.04  # 4% appear as cross-period refunds
FEE_ANOMALY_RATE = 0.02          # 2% have unexpected fee differences
MISSING_SETTLEMENT_RATE = 0.02   # 2% missing from settlement
DUPLICATE_ENTRY_RATE = 0.01      # 1% duplicated entries


def _gen_id(prefix: str, idx: int) -> str:
    """Generate a deterministic Razorpay-like ID."""
    h = hashlib.md5(f"{prefix}_{idx}".encode()).hexdigest()[:14]
    return f"{prefix}_{h}"


def _gen_utr(idx: int) -> str:
    """Generate a bank UTR."""
    return f"UTR{random.randint(100000000000, 999999999999)}"


def generate_dataset(num_transactions: int = 150, seed: int = 42) -> Dict:
    """
    Generate a complete synthetic dataset:
    - orders: merchant-side order records
    - payments: gateway-side payment records (with fees, tax)
    - settlements: batched settlement records
    - recon_entries: per-transaction settlement recon entries
    - injected_variances: ground truth for testing
    """
    random.seed(seed)

    orders = []
    payments = []
    recon_entries = []
    settlements_map = {}  # settlement_id -> settlement data
    injected_variances = []

    base_date = datetime(2026, 8, 1, 10, 0, 0)
    settlement_batch_size = 25  # Group ~25 payments per settlement

    for i in range(num_transactions):
        order_id = _gen_id("order", i)
        payment_id = _gen_id("pay", i)
        created_at = base_date + timedelta(
            days=i // 5,
            hours=random.randint(0, 12),
            minutes=random.randint(0, 59)
        )

        # Random amount between ₹100 and ₹50,000
        amount = round(random.uniform(100, 50000), 2)
        method = random.choices(PAYMENT_METHODS, PAYMENT_METHOD_WEIGHTS)[0]

        # Calculate fees
        mdr_rate = MDR_RATES[method]
        mdr_fee = round(amount * mdr_rate, 2)
        gst_on_mdr = round(mdr_fee * GST_RATE, 2)
        net_amount = round(amount - mdr_fee - gst_on_mdr, 2)

        # Determine settlement batch
        batch_idx = i // settlement_batch_size
        settlement_id = _gen_id("setl", batch_idx)
        settlement_date = created_at + timedelta(days=random.choice([1, 2, 3]))

        # --- Build Order ---
        order = {
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "status": "paid",
            "receipt": f"rcpt_{i+1:04d}",
            "created_at": created_at.isoformat(),
            "notes": {"product": random.choice(["Widget", "Gadget", "Service", "Plan", "Subscription"])}
        }

        # --- Build Payment ---
        payment = {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "method": method,
            "status": "captured",
            "fee": mdr_fee,
            "tax": gst_on_mdr,
            "settlement_id": settlement_id,
            "created_at": created_at.isoformat(),
            "captured_at": (created_at + timedelta(seconds=random.randint(1, 60))).isoformat(),
        }

        # --- Build Recon Entry (settlement-side) ---
        recon_amount = amount
        recon_fee = mdr_fee
        recon_tax = gst_on_mdr
        variance_type = None

        # --- INJECT VARIANCES ---
        rand_val = random.random()

        if rand_val < ROUNDING_VARIANCE_RATE:
            # Sub-rupee rounding difference
            rounding_diff = round(random.uniform(-0.99, 0.99), 2)
            if rounding_diff == 0:
                rounding_diff = 0.01
            recon_amount = round(amount + rounding_diff, 2)
            variance_type = "ROUNDING"
            injected_variances.append({
                "payment_id": payment_id,
                "type": "ROUNDING",
                "expected": amount,
                "actual": recon_amount,
                "diff": rounding_diff
            })

        elif rand_val < ROUNDING_VARIANCE_RATE + FEE_ANOMALY_RATE:
            # Fee doesn't match expected MDR rate (e.g., promotional rate)
            recon_fee = round(mdr_fee * random.uniform(0.5, 1.5), 2)
            variance_type = "FEE_ANOMALY"
            injected_variances.append({
                "payment_id": payment_id,
                "type": "FEE_ANOMALY",
                "expected_fee": mdr_fee,
                "actual_fee": recon_fee,
                "diff": round(recon_fee - mdr_fee, 2)
            })

        elif rand_val < ROUNDING_VARIANCE_RATE + FEE_ANOMALY_RATE + CROSS_PERIOD_REFUND_RATE:
            # Cross-period refund: refund appears in different settlement
            refund_amount = round(amount * random.uniform(0.3, 1.0), 2)
            variance_type = "CROSS_PERIOD_REFUND"
            # The recon entry will show a deduction
            recon_amount = round(amount - refund_amount, 2)
            injected_variances.append({
                "payment_id": payment_id,
                "type": "CROSS_PERIOD_REFUND",
                "original_amount": amount,
                "refund_amount": refund_amount,
                "net_in_recon": recon_amount
            })

        elif rand_val < ROUNDING_VARIANCE_RATE + FEE_ANOMALY_RATE + CROSS_PERIOD_REFUND_RATE + MISSING_SETTLEMENT_RATE:
            # Missing from settlement entirely
            variance_type = "MISSING"
            injected_variances.append({
                "payment_id": payment_id,
                "type": "MISSING",
                "amount": amount
            })
            # Skip creating recon entry
            orders.append(order)
            payments.append(payment)

            # Still add to settlement totals
            if settlement_id not in settlements_map:
                settlements_map[settlement_id] = {
                    "settlement_id": settlement_id,
                    "amount": 0,
                    "fees": 0,
                    "tax": 0,
                    "utr": _gen_utr(batch_idx),
                    "status": "processed",
                    "created_at": settlement_date.isoformat(),
                    "count": 0
                }
            continue

        elif rand_val < ROUNDING_VARIANCE_RATE + FEE_ANOMALY_RATE + CROSS_PERIOD_REFUND_RATE + MISSING_SETTLEMENT_RATE + DUPLICATE_ENTRY_RATE:
            # Duplicate entry in recon
            variance_type = "DUPLICATE"
            injected_variances.append({
                "payment_id": payment_id,
                "type": "DUPLICATE",
                "amount": amount
            })

        recon_entry = {
            "entity_id": payment_id,
            "type": "payment",
            "amount": recon_amount,
            "fee": recon_fee,
            "tax": recon_tax,
            "settlement_id": settlement_id,
            "created_at": created_at.isoformat(),
            "settled_at": settlement_date.isoformat(),
        }

        orders.append(order)
        payments.append(payment)
        recon_entries.append(recon_entry)

        # Add duplicate if flagged
        if variance_type == "DUPLICATE":
            dup_entry = recon_entry.copy()
            dup_entry["_duplicate"] = True
            recon_entries.append(dup_entry)

        # Accumulate settlement batch totals
        if settlement_id not in settlements_map:
            settlements_map[settlement_id] = {
                "settlement_id": settlement_id,
                "amount": 0,
                "fees": 0,
                "tax": 0,
                "utr": _gen_utr(batch_idx),
                "status": "processed",
                "created_at": settlement_date.isoformat(),
                "count": 0
            }
        s = settlements_map[settlement_id]
        s["amount"] = round(s["amount"] + (recon_amount - recon_fee - recon_tax), 2)
        s["fees"] = round(s["fees"] + recon_fee, 2)
        s["tax"] = round(s["tax"] + recon_tax, 2)
        s["count"] += 1

    settlements = list(settlements_map.values())

    return {
        "orders": orders,
        "payments": payments,
        "settlements": settlements,
        "recon_entries": recon_entries,
        "injected_variances": injected_variances,
        "metadata": {
            "total_orders": len(orders),
            "total_payments": len(payments),
            "total_settlements": len(settlements),
            "total_recon_entries": len(recon_entries),
            "total_injected_variances": len(injected_variances),
            "variance_breakdown": {},
            "generated_at": datetime.utcnow().isoformat(),
        }
    }


def save_dataset(path: str = "synthetic_data.json", num: int = 150):
    """Generate and save dataset to JSON file."""
    data = generate_dataset(num)
    
    # Count variance types
    breakdown = {}
    for v in data["injected_variances"]:
        t = v["type"]
        breakdown[t] = breakdown.get(t, 0) + 1
    data["metadata"]["variance_breakdown"] = breakdown

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"[DataGen] Generated {num} transactions -> {path}")
    print(f"  Orders:     {data['metadata']['total_orders']}")
    print(f"  Payments:   {data['metadata']['total_payments']}")
    print(f"  Settlements: {data['metadata']['total_settlements']}")
    print(f"  Recon Entries: {data['metadata']['total_recon_entries']}")
    print(f"  Variances:  {data['metadata']['total_injected_variances']}")
    print(f"  Breakdown:  {breakdown}")
    return data


if __name__ == "__main__":
    save_dataset()
