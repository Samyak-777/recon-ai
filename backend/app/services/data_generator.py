"""
ReconAI Data Generator Service
"""
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict

MDR_RATES = {
    "upi": 0.0,
    "card": 0.02,
    "netbanking": 0.018,
    "wallet": 0.019,
    "intl_card": 0.035,
}

GST_RATE = 0.18
PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet", "intl_card"]
PAYMENT_METHOD_WEIGHTS = [0.40, 0.30, 0.15, 0.10, 0.05]

ROUNDING_VARIANCE_RATE = 0.05
CROSS_PERIOD_REFUND_RATE = 0.04
FEE_ANOMALY_RATE = 0.02
MISSING_SETTLEMENT_RATE = 0.02
DUPLICATE_ENTRY_RATE = 0.01


def _gen_id(prefix: str, idx: int) -> str:
    h = hashlib.md5(f"{prefix}_{idx}".encode()).hexdigest()[:14]
    return f"{prefix}_{h}"


def _gen_utr(idx: int) -> str:
    return f"UTR{random.randint(100000000000, 999999999999)}"


def generate_dataset(num_transactions: int = 150, seed: int = 42) -> Dict:
    random.seed(seed)

    orders = []
    payments = []
    recon_entries = []
    settlements_map = {}
    injected_variances = []

    base_date = datetime(2026, 8, 1, 10, 0, 0)
    settlement_batch_size = 25

    for i in range(num_transactions):
        order_id = _gen_id("order", i)
        payment_id = _gen_id("pay", i)
        created_at = base_date + timedelta(
            days=i // 5,
            hours=random.randint(0, 12),
            minutes=random.randint(0, 59)
        )

        amount = round(random.uniform(100, 50000), 2)
        method = random.choices(PAYMENT_METHODS, PAYMENT_METHOD_WEIGHTS)[0]

        mdr_rate = MDR_RATES[method]
        mdr_fee = round(amount * mdr_rate, 2)
        gst_on_mdr = round(mdr_fee * GST_RATE, 2)
        net_amount = round(amount - mdr_fee - gst_on_mdr, 2)

        batch_idx = i // settlement_batch_size
        settlement_id = _gen_id("setl", batch_idx)
        settlement_date = created_at + timedelta(days=random.choice([1, 2, 3]))

        order = {
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "status": "paid",
            "receipt": f"rcpt_{i+1:04d}",
            "created_at": created_at.isoformat(),
            "notes": {"product": random.choice(["Widget", "Gadget", "Service", "Plan", "Subscription"])}
        }

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

        recon_amount = amount
        recon_fee = mdr_fee
        recon_tax = gst_on_mdr
        variance_type = None

        rand_val = random.random()

        if rand_val < ROUNDING_VARIANCE_RATE:
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
            refund_amount = round(amount * random.uniform(0.3, 1.0), 2)
            variance_type = "CROSS_PERIOD_REFUND"
            recon_amount = round(amount - refund_amount, 2)
            injected_variances.append({
                "payment_id": payment_id,
                "type": "CROSS_PERIOD_REFUND",
                "original_amount": amount,
                "refund_amount": refund_amount,
                "net_in_recon": recon_amount
            })

        elif rand_val < ROUNDING_VARIANCE_RATE + FEE_ANOMALY_RATE + CROSS_PERIOD_REFUND_RATE + MISSING_SETTLEMENT_RATE:
            variance_type = "MISSING"
            injected_variances.append({
                "payment_id": payment_id,
                "type": "MISSING",
                "amount": amount
            })
            orders.append(order)
            payments.append(payment)

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

        if variance_type == "DUPLICATE":
            dup_entry = recon_entry.copy()
            dup_entry["_duplicate"] = True
            recon_entries.append(dup_entry)

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

    breakdown = {}
    for v in injected_variances:
        t = v["type"]
        breakdown[t] = breakdown.get(t, 0) + 1

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
            "variance_breakdown": breakdown,
            "generated_at": datetime.now().isoformat(),
        }
    }
