#!/usr/bin/env python3
"""
Vireo Audio Support Desk Auto-Categorization & Intelligence Suite
Master Entrypoint

Usage:
  python3 run.py serve [--port 8080]
  python3 run.py analyze
  python3 run.py classify --input "Customer message here" [--channel chat]
  python3 run.py audit
  python3 run.py eval
  python3 run.py batch --file tickets.csv [--output predictions.csv]
"""

import sys
import argparse
import csv

from vireo.classifier import TicketClassifier, infer_ground_truth
from vireo.router import TicketRouter
from vireo.analytics import AnalyticsEngine
from vireo.policy_audit import PolicyAuditor
from vireo.evaluator import Evaluator
from vireo.server import DashboardServer


def cmd_analyze(args):
    """Prints full analytical breakdown and executive decision charts."""
    print("=" * 80)
    print(" VIREO AUDIO — CUSTOMER SUPPORT DESK ANALYTICAL AUDIT")
    print(" Prepared for Priya Raman (Head of CX) & Arjun Mehta (Finance Controller)")
    print("=" * 80)

    engine = AnalyticsEngine()
    monthly = engine.get_monthly_breakdown()
    audit = engine.get_routing_misclassification_audit()
    workload = engine.get_team_workload_and_performance()
    proj = engine.get_financial_projections()

    print("\n1. THE BILLING QUEUE ILLUSION VS REALITY")
    print("-" * 80)
    print(f"Total historical tickets: {audit['total_tickets']:,}")
    print(f"Intake Bot Assigned to Billing: {audit['billing_assigned_count']:,} ({audit['billing_assigned_pct']}%)  <-- Priya's metric")
    print(f"Billing tickets actually resolved by Billing: {audit['billing_resolved_by_billing']:,} ({audit['billing_true_workload_pct']}%)")
    print(f"Billing tickets misrouted & resolved by Logistics: {audit['billing_to_logistics_count']:,} ({audit['billing_to_logistics_share_of_billing']}% of Billing queue!)")
    print(f"Total routing mismatches across helpdesk: {audit['total_routing_mismatches']:,} ({audit['mismatch_rate_pct']}%)")

    print("\n2. MONTHLY TEAM WORKLOAD BREAKDOWN (2026)")
    print("-" * 80)
    print(f"{'Month':8} | {'Total':5} | {'Billing (Asgn)':14} | {'Billing (True)':14} | {'Logistics (Asgn)':16} | {'Logistics (True)':16}")
    print("-" * 80)
    for m in ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06']:
        tot = sum(monthly['bot_team_by_month'][m].values())
        b_asg = monthly['bot_team_by_month'][m].get('Billing', 0)
        b_res = monthly['resolved_team_by_month'][m].get('Billing', 0)
        l_asg = monthly['bot_team_by_month'][m].get('Logistics', 0)
        l_res = monthly['resolved_team_by_month'][m].get('Logistics', 0)
        print(f"{m:8} | {tot:5} | {b_asg:4} ({b_asg/tot*100:4.1f}%)   | {b_res:4} ({b_res/tot*100:4.1f}%)   | {l_asg:4} ({l_asg/tot*100:4.1f}%)    | {l_res:4} ({l_res/tot*100:4.1f}%)")

    print("\n3. TEAM WORKLOAD & OPERATIONAL BOTTLENECKS")
    print("-" * 80)
    print(f"{'Team':22} | {'Staff':5} | {'Resolved':8} | {'Tkts/Ag':8} | {'Median Res':10} | {'Breach %':8} | {'CSAT':5}")
    print("-" * 80)
    for w in workload:
        print(f"{w['team']:22} | {w['agent_count']:2} ag | {w['resolved_tickets']:8} | {w['tickets_per_agent']:8.1f} | {w['median_resolution_hours']:8.1f} h | {w['breach_rate_pct']:7.1f}% | {w['avg_csat']:4.2f}")

    print("\n4. THE TRANSFER PENALTY (LOGISTICS)")
    print("-" * 80)
    d_log = audit['logistics_direct']
    t_log = audit['logistics_transferred_from_billing']
    print(f"Direct to Logistics:       Median Res: {d_log['median_hours']}h | Breach Rate: {d_log['breach_rate_pct']}%  | CSAT: {d_log['avg_csat']}")
    print(f"Transferred from Billing:  Median Res: {t_log['median_hours']}h | Breach Rate: {t_log['breach_rate_pct']}% | CSAT: {t_log['avg_csat']} (1.0 pt drop!)")

    print("\n5. FINANCIAL BUSINESS CASE (AT VIREO'S 650 TKTS/WEEK VOLUME)")
    print("-" * 80)
    print(f"Weekly Volume:                          650 tickets (~8,450 / quarter)")
    print(f"Current Quarterly Transfer Fee Waste:   Rs {proj['quarterly_transfer_waste_inr']:,} (at Rs 305/transfer)")
    print(f"Billing-Initiated Transfer Fee Waste:   Rs {proj['quarterly_billing_transfer_waste_inr']:,}")
    print(f"Avoidable SLA Breach Penalty Credits:   Rs {proj['quarterly_avoidable_sla_credits_inr']:,}")
    print(f"Headcount Cost for 2 Hires:             Rs {proj['quarterly_headcount_salary_inr']:,} / quarter (Rs 9,00,000 / year)")
    print(f"--------------------------------------------------------------------------------")
    print(f"TOTAL VALUE GENERATED:                  Rs {proj['total_quarterly_value_inr']:,} / quarter (Rs {proj['total_annual_value_inr']:,} / year)")
    print("=" * 80)


def cmd_classify(args):
    """Classifies a single customer message."""
    classifier = TicketClassifier()
    # Train on tickets.csv
    with open('tickets.csv', 'r', encoding='utf-8') as f:
        tickets = list(csv.DictReader(f))
    with open('agents.csv', 'r', encoding='utf-8') as f:
        agent_teams = {r['agent_id']: r['team'] for r in csv.DictReader(f)}

    train_data = []
    for t in tickets:
        c, tm = infer_ground_truth(t, agent_teams)
        train_data.append({'message': t['customer_message'], 'gt_category': c})
    classifier.train(train_data)

    router = TicketRouter()
    pred = classifier.predict(args.input)
    route_info = router.route(pred['category'], channel=args.channel)

    print("\n--- TICKET CLASSIFICATION & ROUTING RESULT ---")
    print(f"Input Message:      \"{args.input}\"")
    print(f"Channel:            {args.channel}")
    print(f"Predicted Category: {pred['category']}")
    print(f"Confidence:         {round(pred['confidence'] * 100, 1)}%")
    print(f"Assigned Team:      {route_info['assigned_team']}")
    print(f"Service Tier:       Tier {route_info['tier']}")
    print(f"SLA Target:         {route_info['sla_target_minutes']} minutes")
    print(f"SOP Justification:  {route_info['sop_clause']}")
    print("-" * 46 + "\n")


def cmd_audit(args):
    """Runs policy compliance audits."""
    auditor = PolicyAuditor()
    res = auditor.run_all_audits()
    dc = res['double_compensation']
    gw = res['goodwill_cap']

    print("=" * 80)
    print(" VIREO SUPPORT DESK POLICY COMPLIANCE AUDIT (Policy v3.2)")
    print("=" * 80)
    print("\n1. POLICY §5 DOUBLE-COMPENSATION VIOLATIONS")
    print(f"Rule: 'In no case is a customer to receive both a refund and a replacement for the same order'")
    print(f"Violations detected:                {dc['total_double_compensated_orders']} orders")
    print(f"Total Cash Refund Leakage:          Rs {dc['total_refund_leakage_inr']:,}")
    print(f"Total Replacement Cost Leakage:     Rs {dc['total_replacement_cost_leakage_inr']:,}")
    print(f"TOTAL DIRECT FINANCIAL LEAKAGE:     Rs {dc['total_financial_loss_inr']:,}")

    print("\nTop 5 Double Compensation Cases:")
    for c in dc['cases'][:5]:
        print(f"  Order {c['order_id']} | {c['customer_name']} | {c['product_name']} | Refund: Rs {c['refund_amount_inr']:,} + Repl: Rs {c['replacement_total_cost_inr']:,} = Loss: Rs {c['total_financial_loss_inr']:,}")

    print(f"\n2. GOODWILL CREDIT CAP (§5: Max Rs 500)")
    print(f"Breaches detected (> Rs 500):       {gw['goodwill_breaches_count']} tickets")
    print(f"Total Excess Payout:                Rs {gw['total_excess_inr']:,}")
    print("=" * 80)


def cmd_eval(args):
    """Runs benchmark evaluation against ground truth."""
    print("[*] Running benchmark evaluation on historical dataset...")
    ev = Evaluator()
    res = ev.run_evaluation(test_split_ratio=0.2)

    print("=" * 80)
    print(" MODEL EVALUATION & VERIFICATION REPORT")
    print(f" Test Sample Size: {res['sample_size']} tickets (unseen 20% test split)")
    print("=" * 80)
    print(f"Metric                                  Legacy Bot      Our Engine      Improvement")
    print("-" * 80)
    print(f"Category Accuracy:                      {res['legacy_bot_category_accuracy_pct']}%         {res['classifier_category_accuracy_pct']}%         +{res['classifier_category_accuracy_pct'] - res['legacy_bot_category_accuracy_pct']:.1f}%")
    print(f"Category Error Rate:                    {res['legacy_bot_category_error_rate_pct']}%         {res['classifier_category_error_rate_pct']}%         -{res['legacy_bot_category_error_rate_pct'] - res['classifier_category_error_rate_pct']:.1f}%")
    print(f"Team Routing Accuracy:                  {res['legacy_bot_team_routing_accuracy_pct']}%         {res['router_team_accuracy_pct']}%         +{res['router_team_accuracy_pct'] - res['legacy_bot_team_routing_accuracy_pct']:.1f}%")
    print(f"Billing->Logistics Misroutings:         {res['legacy_billing_to_logistics_misroutings']} tickets     {res['classifier_billing_to_logistics_misroutings']} tickets      -{res['misrouting_reduction_pct']}% drop")

    print("\nPER-CATEGORY PERFORMANCE:")
    print(f"{'Category':24} | {'Support':7} | {'Precision':9} | {'Recall':7} | {'F1-Score':8}")
    print("-" * 65)
    for m in res['category_metrics']:
        print(f"{m['category']:24} | {m['support']:7} | {m['precision']:9.3f} | {m['recall']:7.3f} | {m['f1_score']:8.3f}")

    print("\nCOMMON FAILURE MODES:")
    for f in res['top_failure_modes']:
        print(f"  {f['transition']}: {f['count']} cases")
    print("=" * 80)


def cmd_batch(args):
    """Batch categorizes a CSV file."""
    print(f"[*] Processing batch from {args.file}...")
    classifier = TicketClassifier()
    with open('tickets.csv', 'r', encoding='utf-8') as f:
        tickets = list(csv.DictReader(f))
    with open('agents.csv', 'r', encoding='utf-8') as f:
        agent_teams = {r['agent_id']: r['team'] for r in csv.DictReader(f)}
    train_data = []
    for t in tickets:
        c, tm = infer_ground_truth(t, agent_teams)
        train_data.append({'message': t['customer_message'], 'gt_category': c})
    classifier.train(train_data)

    router = TicketRouter()
    output_file = args.output or 'predictions.csv'

    with open(args.file, 'r', encoding='utf-8') as in_f, open(output_file, 'w', encoding='utf-8', newline='') as out_f:
        reader = csv.DictReader(in_f)
        fieldnames = reader.fieldnames + ['predicted_category', 'predicted_team', 'confidence']
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        count = 0
        for row in reader:
            pred = classifier.predict(row.get('customer_message', ''))
            route = router.route(pred['category'], channel=row.get('channel', 'chat'))
            row['predicted_category'] = pred['category']
            row['predicted_team'] = route['assigned_team']
            row['confidence'] = round(pred['confidence'], 3)
            writer.writerow(row)
            count += 1

    print(f"[+] Successfully processed {count:,} tickets to {output_file}")


def cmd_serve(args):
    """Starts dashboard web server."""
    server = DashboardServer(port=args.port)
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Vireo Audio Support Desk Auto-Categorization Suite")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch interactive web dashboard")
    p_serve.add_argument("--port", type=int, default=8080, help="Port to listen on (default 8080)")

    # analyze
    subparsers.add_parser("analyze", help="Print monthly breakdowns, workloads, and ROI to stdout")

    # classify
    p_classify = subparsers.add_parser("classify", help="Auto-categorize and route a single ticket")
    p_classify.add_argument("--input", "-i", type=str, required=True, help="Customer message text")
    p_classify.add_argument("--channel", "-c", type=str, default="chat", choices=["chat", "email", "voice", "social"])

    # audit
    subparsers.add_parser("audit", help="Run Policy §5 compliance & financial leakage audit")

    # eval
    subparsers.add_parser("eval", help="Run benchmark verification against ground truth")

    # batch
    p_batch = subparsers.add_parser("batch", help="Batch classify a CSV file")
    p_batch.add_argument("--file", "-f", type=str, required=True, help="Input CSV path")
    p_batch.add_argument("--output", "-o", type=str, default="predictions.csv", help="Output CSV path")

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "classify":
        cmd_classify(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "batch":
        cmd_batch(args)
    else:
        # Default behavior: run analysis and print helpful tips
        cmd_analyze(args)
        print("\nTip: Run 'python3 run.py serve' to open the interactive dashboard in your browser.")
        print("     Run 'python3 run.py eval' to view the benchmark verification report.")


if __name__ == "__main__":
    main()
