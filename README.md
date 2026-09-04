# 🏦 Recon AI - Autonomous Settlement Reconciliation & Financial Intelligence

> **Razorpay AI Buildathon 2026 Submission**  
> **Track 04**: AI Finance Controller 
> **Repository**: `Samyak-777/recon-ai`  
> **Architecture**: Deterministic 4-Stage Reconciliation Engine + Autonomous Settlement RAG + Razorpay MCP Tools  
> **Live At**: https://recon-chi-peach.vercel.app/
---

## Executive Summary & Problem Statement

For Indian merchants, reconciling Razorpay settlements is a notorious operational bottleneck. The **net bank credit** arriving in a merchant's bank account masks a complex multi-layered hierarchy of per-transaction fee schedules:
1. **Gross-to-Net Opacity**: 1,500 customer checkouts across UPI, Credit Cards, and Netbanking are netted into a single bulk settlement payout minus Merchant Discount Rate (MDR) fees, 18% GST on MDR, and cross-period refund adjustments.
2. **Input Tax Credit (ITC) Leakage**: The 18% GST charged on MDR is 100% claimable under Section 16 of the CGST Act. Without transaction-level unpacking, merchants lose thousands in unclaimed ITC.
3. **Cross-Period Refund Drift**: When a refund is deducted from a settlement batch 3 days after the original transaction, naive string matching fails, creating phantom ledger variances.

**ReconAI** solves this by establishing a **4-Stage Deterministic Reconciliation Pipeline** coupled with an **Autonomous Settlement Q&A Copilot** and a **7-Day Cash Flow Forecaster**, processing batches of 150+ records with **98.67% measured match accuracy in <1ms**.

---

## System Architecture

```mermaid
graph TD
    subgraph Ingestion["1. Ingestion Layer"]
        A[Razorpay Settlement Batch] --> B[Recon Recon/Combined API]
        C[Merchant Order Management System] --> D[MongoDB Financial Ledgers]
    end

    subgraph Pipeline["2. 4-Stage Reconciliation Engine (Deterministic)"]
        B & D --> E["Stage 1: Exact ID & UTR Join Matcher"]
        E --> F["Stage 2: Gross-to-Net Waterfall Unpacker<br/>(MDR + 18% GST + Refund Netting)"]
        F --> G["Stage 3: Variance Classifier<br/>(ROUNDING | FEE_DEDUCTION | TAX | CROSS_PERIOD)"]
        G --> H["Stage 4: AI Heuristic Fuzzy Matcher<br/>(Confidence-Gated Candidate Scoring)"]
    end

    subgraph Intelligence["3. Financial Intelligence Layer"]
        H --> I["Settlement Q&A Agent<br/>(Deterministic Python Aggregations)"]
        H --> J["7-Day Cash Forecaster<br/>(Day-of-Week Seasonality Model)"]
        H --> K["ITC Tax Optimizer<br/>(GSTR-2B Compliance Dossier)"]
    end

    subgraph Presentation["4. Reactive Dark-Mode Dashboard"]
        I & J & K --> L["React 19 + Tailwind CSS + Lucide Interface<br/>(Port 5174)"]
    end
```

---

## 6 Core Superpowers of ReconAI

### 1. Interactive Gross-to-Net Waterfall
Every settlement is dynamically exploded into its constituent order-level waterfall:
$$\text{Net Payout} = \text{Gross Amount} - \text{MDR Fee} - \text{GST on MDR (18\%)} - \text{Refunds Deducted}$$
Merchants can inspect any transaction to verify exact MDR schedules applied by instrument (UPI: 0%, Card: 2.0%, Intl Card: 3.5%).

### 2. Deterministic Exception Classification Queue
Unlike probabilistic LLM chatbots that hallucinate numbers, ReconAI uses hard deterministic thresholds to categorize variances:
- **`ROUNDING`**: Sub-rupee variances ($\le \text{Rs. } 1.00$) auto-classified as floating-point precision tolerance.
- **`CROSS_PERIOD_REFUND`**: Automatic detection of refund clawbacks settling in different settlement batches.
- **`FEE_DEDUCTION`**: Flags negotiated rate variances or promotional card discounts.
- **`MISSING_FROM_SETTLEMENT`**: Detects gateway-captured payments with pending bank settlement transfers.

### 3. Autonomous Settlement Q&A Copilot
Ask natural language questions about settlement batches with **0% hallucination**:
- *"What was our total GST paid on MDR?"* $\rightarrow$ Computes exact sum and flags claimable ITC.
- *"Show all unmatched settlement exceptions."* $\rightarrow$ Returns grouped variance breakdown.
- *"Give me the MDR fee breakdown across payment methods."* $\rightarrow$ Generates weighted effective rates.

### 4. 7-Day Forward Cash Flow Forecaster
Predicts upcoming liquidity based on historical Razorpay settlement cycles, weekend checkout volume accumulations (Monday settlement spikes), and payment rail clearance velocity ($T+1$ for UPI, $T+2$ for Cards).

### 5. Input Tax Credit (ITC) Optimization Engine
Automatically extracts GSTIN metadata and computes total claimable input tax credit on MDR fees, generating audit-ready figures for monthly GSTR-2B filing.

### 6. 🔌 Native Razorpay MCP Tool Integration
Integrated directly with the native Razorpay Model Context Protocol (MCP) Server, exposing 45 financial tools including `fetch_settlement_recon_details`, `fetch_all_settlements`, `fetch_all_orders`, and `create_instant_settlement`.

---

## Benchmark & Measured Performance

Tested against **150 synthetic Razorpay transactions** across 6 settlement batches:

| Metric | Result | Target / Standard |
|---|---|---|
| **Total Records Processed** | **150** | $\ge 50$ (Buildathon requirement) |
| **Exact Match Rate** | **98.67%** (148/150) | $> 95\%$ |
| **False Positive Rate** | **0.00%** | $< 0.5\%$ |
| **Engine Processing Latency** | **< 1.0 ms** | $< 500\text{ ms}$ |
| **Reconciliation Throughput** | **> 150,000 txns/sec** | High-scale batch readiness |
| **Exceptions Categorized** | **20** (100% explained) | Complete exception transparency |
| **ITC Optimization Rate** | **100%** (Rs. 8,136.29) | Total tax compliance |

---

## Failure Recovery & "What Broke at 2 AM"

*Judges evaluate engineering resilience: what failed during development and how we resolved it.*

1. **The Cross-Period Refund Trap**: In our first iteration, when a customer initiated a partial refund 2 days after purchase, the settlement batch deducted the refund amount directly from the merchant payout. Our naive exact matcher flagged the entire settlement batch as "Amount Mismatch."  
   *Fix*: Implemented a secondary entity sidecar that scans prior captured transactions for refund UUIDs and reconstructs the delta before variance scoring.
2. **Sub-Rupee Rounding Drift**: Cumulative transaction-level MDR calculation produced a Rs. 0.03 variance against the lump-sum settlement payout due to standard IEEE 754 float rounding.  
   *Fix*: Established a configurable `ROUNDING_TOLERANCE = Rs. 1.00` rule in `recon_engine.py` that separates arithmetic precision differences from genuine financial anomalies.
3. **LLM Hallucination in Accounting**: Early prototypes used GPT-4 to generate reconciliation summaries directly. In 8% of cases, the model rounded Rs. 3,516,984.69 to Rs. 3.52M or invented explanations for missing UTRs.  
   *Fix*: Implemented the **Deterministic Evidence-First Invariant** — all numbers are calculated by Python aggregation engines; LLMs are strictly limited to intent classification and natural language formatting.

---

## Quickstart & Reproduction

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB running on `localhost:27017`

### 1-Command Startup
```bash
# Clone the repository
git clone https://github.com/Samyak-777/recon-ai.git
cd recon-ai

# Launch both Backend (Port 8005) and Frontend (Port 5174)
python run_recon_servers.py
```

Open your browser at **`http://localhost:5174`** to interact with the live dashboard!

### Run Standalone Benchmark
```bash
python tools/run_recon_benchmark.py
```

---

## 5-Minute Video Presentation Structure

- **0:00 - 0:45**: *The Problem*: The Indian settlement reconciliation nightmare (MDR fees, GST on MDR, cross-period refund drift).
- **0:45 - 1:45**: *The Solution Architecture*: The 4-Stage Deterministic Engine + Razorpay MCP integration.
- **1:45 - 3:00**: *Live Demo*: 150-transaction batch run, Gross-to-Net Waterfall, and 1-click Exception Queue verification.
- **3:00 - 4:00**: *AI Finance Features*: Settlement Q&A Copilot answering GST/ITC queries and 7-Day Cash Flow Forecaster.
- **4:00 - 4:45**: *Failure Recovery*: Resolving cross-period refund drift and IEEE float rounding in Indian fintech.
- **4:45 - 5:00**: *Conclusion*: Why ReconAI is ready for production merchants.
