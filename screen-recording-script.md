# Screen Recording Walkthrough Script (Max 3 Minutes)

**Target Duration:** 2 minutes 45 seconds (Strictly under 3 minutes)  
**Format:** Screen recording showing terminal, web dashboard, and code. No presentation slides.  

---

### Minute 0:00 – 0:45 | What We Built & The Core Discovery

**Screen Visual:** Terminal showing `python3 run.py analyze`, then opening browser at `http://localhost:8080`.

**Voiceover / Script:**
> *"Hi Priya and Arjun. When we received your brief asking whether to add two hires to Billing based on its 22% queue volume, we built Vireo SmartRoute—an AI-assisted intake auto-categorization and routing system.*
>
> *Our first step was analyzing the 11,780 historical tickets. We immediately discovered that the 22% Billing queue is an illusion created by your legacy intake bot.*
>
> *The bot tagged anything mentioning 'paid', 'debited', or 'money deducted' as Billing. But 31% of those tickets—nearly 800 tickets—were actually customers complaining about courier delays and lost parcels. Billing agents had to manually transfer nearly half their queue to Logistics.*
>
> *Billing’s true workload is only 15.6%, with a median resolution time of under 2 hours. Meanwhile, Logistics is handling 22.7% of volume with only 5 agents, suffering 40-hour delays and 458 SLA breaches. Putting two hires into Billing would waste Rs 9 lakh a year on idle capacity."*

---

### Minute 0:45 – 1:30 | Live Tool Demonstration & Side-by-Side Routing

**Screen Visual:** Browser on the "Live Interactive Classifier" tab of the dashboard (`http://localhost:8080`).

**Action:** Paste into the text box:
`"paid, confirmed, then nothing. 5 days and counting"`
Click **Classify & Route**.

**Voiceover / Script:**
> *"Here is the tool running live. Watch what happens with a classic customer message: 'paid, confirmed, then nothing. 5 days and counting'.*
>
> *Your legacy bot sees the word 'paid' and misroutes it to Billing. Billing sits on it, charges a Rs 305 internal transfer fee, and hands it off to Logistics. By the time Logistics touches it, first-response SLA breach risk jumps from 9.5% to 35.8%, resolution takes 43 hours, and CSAT collapses from 3.2 to 2.2.*
>
> *Our Hybrid AI router analyzes customer intent. It recognizes that non-delivery of an order supersedes payment confirmation. It routes directly to Logistics under Policy Section 6 at 97% confidence. This single routing change avoids Rs 305 in transfer waste and cuts over 24 hours of delay."*

---

### Minute 1:30 – 2:15 | Prompts Used & Version Iterations

**Screen Visual:** Visual Studio Code / terminal showing `vireo/classifier.py` and evaluation output `python3 run.py eval`.

**Voiceover / Script:**
> *"Let's talk about the AI iterations and prompts behind this:*
>
> *In Version 1, we tested a pure LLM prompt asking a chat model to classify tickets into the 11 categories. While accuracy was high (~82%), calling an LLM API on 650 tickets a week was slow, introduced external API dependency risks, and struggled with edge-case terminology like Indian postal pin codes, UTR numbers, and RTO.*
>
> *In Version 2, we attempted a purely rule-based regex approach. That was too rigid—accuracy plummeted to 43.8% because customer messages have extreme spelling variations and informal slang.*
>
> *In Version 3 (our production architecture), we built a hybrid engine: domain intent priority hierarchy combined with an N-gram Naive Bayes classifier with Laplace smoothing, running on standard Python with zero dependencies.*
>
> *On an unseen 20% test split of 2,356 tickets, category accuracy jumped from 65.6% to 79.8%, team routing accuracy reached 81.7%, and Billing-to-Logistics misrouting dropped by 94.3%—from 211 errors down to just 12."*

---

### Minute 2:15 – 2:45 | What We Threw Away & Unasked Discovery

**Screen Visual:** Browser showing the "Policy & Leakage Audit" tab on the dashboard, displaying the 149 double-compensation cases.

**Voiceover / Script:**
> *"What did we discard?*
> 1. *We threw away heavy PyTorch/transformer models that required multi-gigabyte GPU downloads, keeping the codebase completely lightweight so anyone can clone and run it instantly on a clean machine.*
> 2. *We threw away automated refund-approval bots because Policy Section 6 mandates that only Tier 2 agents can certify warranty replacements.*
>
> *Finally, something nobody asked for: our audit engine caught 149 orders where customers received BOTH a cash refund and a replacement unit—violating Policy Section 5 and leaking Rs 7.7 lakh in direct cash.*
>
> *By deploying this system, Vireo saves Rs 2.59 lakh a quarter in eliminated transfer waste, avoids Rs 9 lakh in misallocated headcount, and plugs Rs 7.7 lakh in refund leakage. Thank you."*

---

### Checklist Before Hitting Record:
1. Terminal open with `python3 run.py analyze` executed.
2. Web browser open at `http://localhost:8080`.
3. Code editor showing `vireo/classifier.py`.
4. Keep recording strictly under 3 minutes (target: 2:45).
5. Ensure audio is clear. No slides!
