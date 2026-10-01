# MEMORANDUM

**TO:** Priya Raman, Head of Customer Experience  
**CC:** Arjun Mehta, Finance Controller; Neha Kulkarni, Support Operations Manager; Sameer Qureshi, IT Helpdesk Administrator  
**FROM:** Kabir Nanda, Vendor CX Advisory Lead  
**DATE:** 1 October 2026  
**SUBJECT:** Support Headcount Allocation & Ticket Routing Analysis  
**READING TIME:** ~8 minutes  

---

### Executive Summary: Where the Two Hires Must Go

Priya, based on the historical export of 11,780 tickets, **we strongly recommend that you do NOT allocate the next two hires to Billing.** 

Allocating them to Billing would spend Rs 9.0 lakh per year (Rs 2.25 lakh/quarter) on a team that does not have a volume problem. While the helpdesk intake bot reports Billing at **21.8%** of total tickets, Billing’s **actual resolved workload is only 15.6%**. 

The team that is truly drowning—exactly as Neha suspected—is **Logistics**:
* **Logistics handles 22.7% of all resolved tickets** (2,673 tickets) with only **5 agents** (534 tickets/agent—the heaviest load in the company).
* Logistics suffers a **median resolution time of 43.2 hours** and an average of **40.4 hours** (versus **1.8 hours** in Billing).
* Logistics generated **458 first-response SLA breaches** (costing Rs 1.6 lakh in automatic Rs 350 store credits).

If you add two hires to Billing, Billing agents will average barely 4 to 5 tickets a day. If you allocate those two hires to Logistics, their workload drops from 534 to 381 tickets per agent, and delivery resolution times will drop by more than half.

Even better: if you implement the automated intake routing tool we have built, **you may not need to hire anyone at all**—recovering **Rs 4.84 lakh per quarter** in eliminated operational waste, while fixing the root cause.

---

### 1. The Billing Queue Illusion: Why the Bot Lied

Why did Billing look like 22% of total volume?

The intake bot tags any customer message that contains words like *"paid"*, *"amount debited"*, *"money went out"*, or *"transaction done"* as `Billing & Payments` and dumps it into Billing's queue.

However, when Indian e-commerce customers write:
> *"Paid on 19 June, still waiting for something to show up."*  
> *"Money went out of my account 10 days ago and I have nothing in hand."*  
> *"Payment successful but order not delivered."*

Their issue is **not billing**; their issue is **non-delivery**. 

In the data, **31.0% of tickets routed to Billing (795 tickets) were delivery queries** that Billing agents had to manually transfer to Logistics. In the current helpdesk alone, Billing generated **632 internal transfers**—accounting for **48.7% of all transfers across the entire support desk**.

Billing agents were not overworked with billing cases; they were acting as an unpaid, manual triage desk for courier delays.

---

### 2. The Hidden Cost of Misrouting: The "Transfer Penalty"

Under Policy §4, every internal transfer between teams costs **Rs 305** in re-handling and administration. Under Policy §3, every ticket missing its first-response target automatically pays out a **Rs 350 store credit**.

When a delivery query is misrouted to Billing and transferred to Logistics, the customer suffers what we call the **Transfer Penalty**:

| Metric | Direct to Logistics | Transferred from Billing | Penalty Impact |
| :--- | :--- | :--- | :--- |
| **First-Response Breach Rate** | **9.5%** | **35.8%** | **Nearly 4x higher breach rate** |
| **Median Resolution Time** | **30.1 hours** | **43.3 hours** | **+13.2 hours added delay** |
| **Average CSAT Score** | **3.15 / 5.0** | **2.24 / 5.0** | **Nearly 1 full point drop in CSAT** |
| **Internal Transfer Fee** | **Rs 0** | **Rs 305** | **Rs 305 re-handling fee per ticket** |

At Vireo's operating volume of **650 tickets per week** (~8,450 tickets per quarter):
* Internal transfers waste **Rs 4.33 lakh per quarter** (of which Billing misrouting accounts for **Rs 2.11 lakh**).
* Misrouted transfer delays trigger **Rs 52,700 per quarter** in avoidable Rs 350 SLA breach credits.
* **Total operational waste from misrouting: ~Rs 2.59 lakh every quarter.**

---

### 3. Addressing Arjun Mehta's Challenge: "Fix a Process Rather Than Hire"

Arjun noted: *"Two hires is about Rs 9 lakh a year. I want to see the volume case in writing before I sign, and I'd rather fix a process than hire into it if that's an option."*

Here is the exact financial comparison for Arjun:

1. **Option A: Priya’s Initial Plan (2 hires into Billing)**
   * Cost: **+Rs 9.0 lakh/year** (+Rs 2.25 lakh/quarter).
   * Result: Wasted capital. Billing workload is already light; Logistics continues to drown, SLA breaches continue, customer churn increases.

2. **Option B: Data-Driven Reallocation (2 hires into Logistics)**
   * Cost: **+Rs 9.0 lakh/year** (+Rs 2.25 lakh/quarter).
   * Result: Solves the bottleneck. Logistics team expands from 5 to 7 agents; resolution times drop below 20 hours; SLA breaches fall by 60%.

3. **Option C: Intelligent Auto-Routing (Fix the Process — Our Tool)**
   * Capital Expenditure: **Rs 0 new hires** (or defer hires until Q1 FY27).
   * Direct Operational Savings: **Rs 2.59 lakh/quarter** (~Rs 10.4 lakh/year) by eliminating 94% of Billing-to-Logistics transfers and avoidable SLA penalties.
   * Total Financial Value (Headcount avoided + Waste eliminated): **Rs 4.84 lakh per quarter (Rs 19.4 lakh/year).**

---

### 4. An Unasked Finding: Rs 7.7 Lakh in Policy §5 Financial Leakage

While auditing the ticket and order data, our tool discovered a serious financial leakage that nobody asked for:

> **Policy §5 explicitly mandates:** *"In no case is a customer to receive both a refund and a replacement for the same order; where this happens in error it must be escalated to the Team Lead and Finance the same day."*

Across the dataset, **149 orders received BOTH a cash refund AND a replacement unit**, resulting in **Rs 7,69,727 (Rs 7.7 lakh) in direct financial leakage**:
* Cash refunded: **Rs 4,90,467**
* Replacement unit + shipping cost: **Rs 2,79,260**

**Why did this happen?** Because of siloed teams and misrouting. A customer opened a ticket with Logistics, who issued a replacement unit under SOP 3.1. Two days later, a separate ticket arrived mentioning *"money deducted"*, was routed to Billing or Returns Desk, and an agent processed a full refund without visibility into the replacement shipment.

By unifying intake routing, this Rs 7.7 lakh leakage is immediately stopped.

---

### 5. Recommended Action Plan

1. **Do not hire into Billing.** If two headcount slots are funded, allocate both to **Logistics** immediately.
2. **Deploy the AI Auto-Categorizer at Intake:** Replace the keyword bot with our hybrid intent router. It cuts Billing-to-Logistics misrouting by **94.3%** and raises team routing accuracy from **71.2% to 81.7%**, instantly saving ~Rs 2.6 lakh per quarter.
3. **Lock Down Refund/Replacement Handshakes:** Implement a mandatory cross-check in the helpdesk preventing a refund from being approved if a replacement flag is already active on the same `order_id` (saving Rs 7.7 lakh in recurring leakage).

We have packaged the working tool, live dashboard, benchmark test suite, and audit reports into the project repository for immediate evaluation.
