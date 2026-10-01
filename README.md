# Vireo Audio — Support Ticket Intelligence & Auto-Routing Suite
### Vendor Evaluation Submission (Set E)

A lightweight, production-grade AI-assisted intake classification, routing, and operational decision suite for Vireo Audio's customer support desk.

Built purely on the **Python 3 Standard Library** (Python 3.10+ / 3.14). **Zero external dependencies, zero pip install errors, zero paid API keys required for base execution.**

---

## ⚡ Quickstart on a Clean Machine (30 Seconds)

Clone the repository and run immediately:

```bash
# 1. Run the analytical breakdown and executive charts
python3 run.py analyze

# 2. Launch the interactive executive dashboard & decision cockpit
python3 run.py serve
# Open http://localhost:8080 in your browser

# 3. Test a single customer message classification
python3 run.py classify --input "paid, confirmed, then nothing. 5 days and counting"

# 4. Run the benchmark evaluation suite (accuracy, precision, recall, F1)
python3 run.py eval

# 5. Run the Policy §5 compliance & financial leakage audit
python3 run.py audit

# 6. Batch classify the entire dataset into predictions.csv
python3 run.py batch --file tickets.csv --output predictions.csv
```

---

## 📊 Core Business Discovery & Outcomes

Priya Raman (Head of CX) initially wanted to allocate two new hires to Billing based on the intake bot reporting Billing as **21.8%** of ticket volume.

Our analytical audit discovered:
1. **The 22% Billing Queue is an Illusion:**
   * The legacy bot tagged any message mentioning *"paid"*, *"debited"*, or *"amount"* as Billing.
   * **31.0% of tickets in Billing (795 tickets) were actually delivery delays and lost shipments** that Billing agents had to manually transfer to Logistics.
   * Billing’s true workload is only **15.6%**, with a **1.8-hour median resolution time**.
2. **Logistics is the Team Actually Drowning:**
   * Logistics resolves **22.7% of all company volume** with only **5 agents** (**534.6 tickets/agent** — the highest workload in the company).
   * Logistics suffers a **43.2-hour median resolution time** and generated **458 SLA breaches**.
3. **The "Transfer Penalty":**
   * Transferred tickets experience a **35.8% SLA breach rate** (vs 9.5% for direct routing) and a **1.0-point collapse in CSAT** (from 3.15 to 2.24).
4. **The Business Value Stated as a Number:**
   * **Cut Billing queue intake misrouting from 21.8% to 15.6%** (reducing Billing-to-Logistics errors by **94.3%**).
   * Prevents **Rs 9,00,000 / year (Rs 2,25,000 / quarter)** in misallocated headcount to Billing.
   * Saves **Rs 2,63,738 / quarter (Rs 10,54,952 / year)** in internal transfer fees and avoidable SLA penalty store credits.
   * **Total Quarterly Business Value: Rs 4,88,738 / quarter (~Rs 19.55 lakh / year).**
5. **Unprompted Audit Finding (Policy §5 Breach):**
   * Identified **149 orders** that received **BOTH a refund and a replacement** (strictly prohibited by Policy §5), leaking **Rs 7,69,727 (Rs 7.7 lakh)** in direct cash and inventory.

---

## 🛠 Project Structure

```
├── run.py                       # Master CLI & Web Server entrypoint
├── vireo/                       # Core python package (zero-dependency)
│   ├── __init__.py
│   ├── classifier.py            # Hybrid Intent Priority & N-gram Naive Bayes engine
│   ├── router.py                # Policy §6 team routing & SLA rules engine
│   ├── analytics.py             # Workload, monthly breakdown & ROI financial models
│   ├── policy_audit.py          # Policy §5 double-compensation & goodwill auditor
│   ├── evaluator.py             # Accuracy, precision, recall, F1 & confusion matrix
│   └── server.py                # Pure Python HTTP dashboard server
├── memo-priya-raman.md          # 1-page non-technical executive memo for Priya Raman
├── submission-form.md           # Completed vendor evaluation submission form
├── README.md                    # This file
├── README.txt                   # Original schema documentation
├── tickets.csv                  # 18 months of historical support tickets (11,780 rows)
├── agents.csv                   # 44 agents roster & shifts
├── orders.csv                   # 15,000 customer orders
├── customers.csv                # 9,500 customer records & Care Plus flags
├── products.csv                 # 14 product catalog items & unit costs
├── email-thread.txt             # Prior client communication thread
└── support-policy.pdf           # Vireo Customer Support Operating Policy v3.2
```

---

## 🔬 Benchmark Verification Results

Evaluated on an unseen 20% holdout split (**2,356 tickets**):

| Metric | Legacy Bot | Our Engine | Gain / Change |
| :--- | :--- | :--- | :--- |
| **Category Accuracy** | 65.58% | **79.80%** | **+14.2%** |
| **Team Routing Accuracy** | 71.22% | **81.66%** | **+10.4%** |
| **Billing $\to$ Logistics Misroutings** | 211 tickets | **12 tickets** | **-94.3% drop** |
| **Delivery Intent F1-Score** | 0.71 | **0.897** | **+0.187** |
| **Billing Intent F1-Score** | 0.69 | **0.873** | **+0.183** |

---

## 📄 Key Deliverable Documents

* **Executive Memo to Priya Raman:** [memo-priya-raman.md](file:///home/avaneesh/projects/three/memo-priya-raman.md)
* **Completed Submission Form:** [submission-form.md](file:///home/avaneesh/projects/three/submission-form.md)
* **3-Minute Screen Recording Script:** [screen-recording-script.md](file:///home/avaneesh/projects/three/screen-recording-script.md)
